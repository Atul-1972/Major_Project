"""Epoch-boundary E1 training: train/validation only, resumable durable state."""

import csv
import json
import math
import time
from collections import Counter
from pathlib import Path

import torch
from torch import nn

from ai_model.data.dataset import make_loader
from ai_model.data.splitting import verify_manifest_files
from ai_model.models.cnn import set_training_stage
from ai_model.models.registry import build_model
from .metrics import classification_metrics
from .reproducibility import capture_rng, environment, experiment_identity, restore_rng, seed_all
from .storage import atomic_save, run_lock


def training_class_weights(records, classes):
    counts = Counter(int(row["class_index"]) for row in records)
    if set(counts) != set(range(len(classes))):
        raise ValueError("Training split is missing a class")
    return torch.tensor([len(records) / (len(classes) * counts[index]) for index in range(len(classes))], dtype=torch.float32)


def optimizer_and_scheduler(model, config):
    optimizer = torch.optim.AdamW([
        {"params": model.features.parameters(), "lr": config["finetune_lr"]},
        {"params": model.classifier.parameters(), "lr": config["warmup_lr"]},
    ], weight_decay=config["weight_decay"])

    def factor(epoch):
        fine_epoch = max(0, epoch - config["warmup_epochs"])
        return 0.5 * (1 + math.cos(math.pi * min(fine_epoch, config["finetune_epochs"]) / config["finetune_epochs"]))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, [
        lambda epoch: 0.0 if epoch < config["warmup_epochs"] else factor(epoch),
        lambda epoch: 1.0 if epoch < config["warmup_epochs"] else config["finetune_lr"] / config["warmup_lr"] * factor(epoch),
    ])
    return optimizer, scheduler


def predict_loader(model, loader, device):
    model.eval()
    labels, scores, identifiers, groups = [], [], [], []
    loss = 0.0
    with torch.inference_mode():
        for batch in loader:
            images, target = batch["image"].to(device), batch["label"].to(device)
            logits = model(images)
            if logits.shape != (len(target), len(loader.dataset.classes)) or not torch.isfinite(logits).all():
                raise ValueError("Invalid model output")
            loss += nn.functional.cross_entropy(logits, target, reduction="sum").item()
            labels.extend(target.cpu().tolist())
            scores.extend(logits.float().softmax(dim=1).cpu().tolist())
            identifiers.extend(batch["image_id"])
            groups.extend(batch["group_id"])
    codes = [item["code"] for item in loader.dataset.classes]
    metrics = classification_metrics(labels, scores, codes)
    metrics["loss"] = loss / len(labels)
    return metrics, {"labels": labels, "scores": scores, "image_ids": identifiers, "group_ids": groups}


def load_checkpoint(path):
    # Checkpoints written here use only tensors and primitive Python containers.
    return torch.load(path, map_location="cpu", weights_only=True)


def scaled_optimizer_step(loss, model, optimizer, scaler, clip_norm):
    scaler.scale(loss).backward()
    scaler.unscale_(optimizer)
    # FP16 overflow is handled by GradScaler's skip/backoff, not a false failure.
    nn.utils.clip_grad_norm_(model.parameters(), clip_norm, error_if_nonfinite=not scaler.is_enabled())
    previous_scale = scaler.get_scale()
    scaler.step(optimizer)
    scaler.update()
    return scaler.get_scale() >= previous_scale


def best_payload(state):
    return {
        "schema_version": 1, "experiment": state['identity']['config']['experiment'], "purpose": state["purpose"],
        "identity": state["identity"], "initialization": state["initialization"],
        "model": state["best_model"], "selected_epoch": state["best_epoch"],
        "validation_macro_f1": state["best_score"],
        "selection_rule": "highest validation macro-F1; earliest checkpoint on ties",
    }


def train_run(data_root, manifest_dir, config, run_dir, device, *, resume=False, epochs_this_session=None, _model_factory=None):
    """The private model injection is for explicitly synthetic unit tests only."""
    run_dir, manifest_dir = Path(run_dir), Path(manifest_dir)
    if epochs_this_session is not None and epochs_this_session < 1:
        raise ValueError("Session epoch limit must be positive")
    identity = experiment_identity(config, manifest_dir)
    purpose = "technical_fixture_not_research" if _model_factory else "research_training"
    with run_lock(run_dir):
        checkpoint_path = run_dir / "last.pt"
        if resume:
            if not checkpoint_path.is_file():
                raise ValueError("No completed-epoch checkpoint exists; use a new run directory")
            state = load_checkpoint(checkpoint_path)
            if state["identity"] != identity or state["purpose"] != purpose:
                raise ValueError("Resume rejected: configuration, splits, mapping, preprocessing, code or packages changed")
        else:
            if checkpoint_path.exists() or (run_dir / "run.json").exists():
                raise ValueError("Run already exists; use --resume or a new run directory")
            state = None
        seed_all(config["seed"], config["deterministic"])
        mapping = json.loads((manifest_dir / "class_mapping.json").read_text(encoding="utf-8"))["classes"]
        if _model_factory:
            model, initialization = _model_factory(len(mapping), state is None)
        else:
            model, initialization = build_model(config, len(mapping), pretrained=state is None)
        model.to(device)
        optimizer, scheduler = optimizer_and_scheduler(model, config)
        amp = config["amp"] and device.type == "cuda"
        scaler = torch.amp.GradScaler("cuda", enabled=amp)
        if state is not None:
            model.load_state_dict(state["model"])
            optimizer.load_state_dict(state["optimizer"])
            scheduler.load_state_dict(state["scheduler"])
            scaler.load_state_dict(state["scaler"])
            restore_rng(state["rng"])
            initialization = state["initialization"]
            # last.pt is authoritative if interruption happened before best.pt.
            if state["best_epoch"] is not None:
                atomic_save(run_dir / "best.pt", best_payload(state), tensor=True)
            if state["status"] in ("completed", "early_stopped"):
                return state
        else:
            state = {
                "schema_version": 1, "purpose": purpose, "identity": identity,
                "initialization": initialization, "next_epoch": 0, "global_step": 0,
                "best_score": -1.0, "best_epoch": None, "best_model": None,
                "bad_epochs": 0, "history": [], "status": "running", "elapsed_seconds": 0.0,
                "total_parameters": sum(parameter.numel() for parameter in model.parameters()),
            }
            atomic_save(run_dir / "run.json", {"identity": identity, "initialization": initialization, "environment": environment(device), "purpose": purpose})
            atomic_save(run_dir / "class_mapping.json", {"classes": mapping})
            atomic_save(run_dir / "preprocessing.json", json.loads((manifest_dir / "preprocessing.json").read_text()))
            state.update(model=model.state_dict(), optimizer=optimizer.state_dict(), scheduler=scheduler.state_dict(), scaler=scaler.state_dict(), rng=capture_rng(), peak_cuda_memory_bytes=None)
            # Also recover an interruption during the first epoch.
            atomic_save(checkpoint_path, state, tensor=True)
        total_epochs = config["warmup_epochs"] + config["finetune_epochs"]
        with (manifest_dir / "train.csv").open(encoding="utf-8", newline="") as handle:
            records = list(csv.DictReader(handle))
        weights = training_class_weights(records, mapping).to(device)
        atomic_save(run_dir / "class_weights.json", {"policy": config["class_weighting"], "source_split": "train", "weights": weights.cpu().tolist()})
        validation = make_loader(data_root, manifest_dir, "val", config["batch_size"], config["seed"], config["num_workers"])
        session_epochs = 0
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        try:
            for epoch in range(state["next_epoch"], total_epochs):
                if (run_dir / "PAUSE").exists():
                    state["status"] = "paused"
                    break
                started = time.perf_counter()
                warmup = epoch < config["warmup_epochs"]
                # Every epoch has a stable shuffle/augmentation stream, including a repeated interrupted epoch.
                seed_all(config["seed"] + epoch, config["deterministic"])
                train = make_loader(data_root, manifest_dir, "train", config["batch_size"], config["seed"] + epoch, config["num_workers"])
                set_training_stage(model, warmup=warmup)
                numerator, denominator = 0.0, 0.0
                optimizer_steps = 0
                learning_rates = [group["lr"] for group in optimizer.param_groups]
                for step, batch in enumerate(train):
                    images, target = batch["image"].to(device), batch["label"].to(device)
                    optimizer.zero_grad(set_to_none=True)
                    with torch.autocast(device_type=device.type, enabled=amp):
                        logits = model(images)
                        loss_sum = nn.functional.cross_entropy(logits, target, weight=weights, reduction="sum")
                        weight_sum = weights[target].sum()
                        loss = loss_sum / weight_sum
                    if not torch.isfinite(loss):
                        raise ValueError("Nonfinite training loss; last completed checkpoint retained")
                    stepped = scaled_optimizer_step(loss, model, optimizer, scaler, config["gradient_clip_norm"])
                    optimizer_steps += int(stepped)
                    state["global_step"] += int(stepped)
                    numerator += loss_sum.detach().item()
                    denominator += weight_sum.item()
                    if step % 100 == 0:
                        print(f"Epoch {epoch + 1}/{total_epochs}, batch {step + 1}/{len(train)}, loss {loss.item():.4f}", flush=True)
                if not optimizer_steps:
                    raise ValueError("No successful optimizer steps in this epoch; inspect AMP scaling/gradients")
                metrics, _ = predict_loader(model, validation, device)
                score = metrics["macro_f1"]
                improved = score > state["best_score"]
                if improved:
                    state["best_score"], state["best_epoch"] = score, epoch
                    state["best_model"] = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
                    state["bad_epochs"] = 0
                elif not warmup:
                    state["bad_epochs"] += 1
                elapsed = time.perf_counter() - started
                state["history"].append({"epoch": epoch, "stage": "head_warmup" if warmup else "full_finetuning", "train_loss": numerator / denominator, "validation_loss": metrics["loss"], "validation_macro_f1": score, "validation_accuracy": metrics["accuracy"], "learning_rates": learning_rates, "seconds": elapsed, "optimizer_steps": optimizer_steps, "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad)})
                scheduler.step()
                state["next_epoch"] = epoch + 1
                state["elapsed_seconds"] += elapsed
                session_epochs += 1
                state["status"] = "early_stopped" if not warmup and state["bad_epochs"] >= config["patience"] else ("completed" if epoch + 1 == total_epochs else "running")
                if state["status"] == "running" and ((run_dir / "PAUSE").exists() or (epochs_this_session and session_epochs >= epochs_this_session)):
                    state["status"] = "paused"
                state.update(model=model.state_dict(), optimizer=optimizer.state_dict(), scheduler=scheduler.state_dict(), scaler=scaler.state_dict(), rng=capture_rng(), peak_cuda_memory_bytes=torch.cuda.max_memory_allocated(device) if device.type == "cuda" else None)
                atomic_save(checkpoint_path, state, tensor=True)
                atomic_save(run_dir / "best.pt", best_payload(state), tensor=True)
                atomic_save(run_dir / "history.json", state["history"])
                atomic_save(run_dir / "status.json", {key: state[key] for key in ("status", "next_epoch", "best_epoch", "best_score", "global_step", "elapsed_seconds")})
                print(f"Saved epoch {epoch + 1}; validation macro-F1 {score:.4f}; status {state['status']}", flush=True)
                if state["status"] != "running":
                    break
        except (KeyboardInterrupt, Exception) as error:
            atomic_save(run_dir / "status.json", {"status": "interrupted", "checkpoint_exists": checkpoint_path.exists(), "message": str(error), "recovery": "Resume last.pt; the unfinished epoch repeats. No partial epoch was committed."})
            raise
        # A pause request can also be detected before an epoch starts.
        if state["status"] == "paused":
            atomic_save(run_dir / "status.json", {"status": "paused", "next_epoch": state["next_epoch"], "checkpoint_exists": checkpoint_path.exists()})
        verify_manifest_files(manifest_dir)
        return state
