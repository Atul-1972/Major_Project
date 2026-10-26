"""Disposable real-image forward/backward and checkpoint-load compatibility check."""

import time
from pathlib import Path

import torch

from ai_model.data.acquire import sha256_file
from ai_model.data.dataset import make_loader
from ai_model.models.cnn import set_training_stage
from ai_model.models.registry import build_model
from .engine import load_checkpoint, optimizer_and_scheduler, scaled_optimizer_step
from .reproducibility import capture_rng, environment, experiment_identity, restore_rng, seed_all
from .storage import atomic_save


def smoke_test(data_root, manifest_dir, config, output, device, *, pretrained=True):
    seed_all(config["seed"], config["deterministic"])
    started = time.perf_counter()
    train = make_loader(data_root, manifest_dir, "train", min(2, config["batch_size"]), config["seed"])
    validation = make_loader(data_root, manifest_dir, "val", min(2, config["batch_size"]), config["seed"])
    batch = next(iter(train))
    target = batch["label"].to(device)
    images = batch["image"].to(device)
    model, initialization = build_model(config, len(train.dataset.classes), pretrained=pretrained)
    model.to(device)
    optimizer, scheduler = optimizer_and_scheduler(model, config)
    amp = config["amp"] and device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    for warmup in (True, False):
        set_training_stage(model, warmup=warmup)
        # Exercise a nonzero backbone learning rate in the full-network check.
        if not warmup:
            optimizer.param_groups[0]["lr"] = config["finetune_lr"]
        for _ in range(8):
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, enabled=amp):
                logits = model(images)
                loss = torch.nn.functional.cross_entropy(logits, target)
            if logits.shape != (len(target), len(train.dataset.classes)) or not torch.isfinite(loss):
                raise ValueError("Smoke test produced invalid output/loss")
            stepped = scaled_optimizer_step(loss, model, optimizer, scaler, config["gradient_clip_norm"])
            if stepped:
                if not warmup and not any(p.grad is not None and p.grad.abs().sum() > 0 for p in model.features.parameters()):
                    raise ValueError("No backbone gradient in fine-tuning smoke test")
                break
        else:
            raise ValueError("AMP scale did not settle within eight smoke attempts")
    model.eval()
    probe = next(iter(validation))["image"].to(device)
    with torch.inference_mode():
        expected = model(probe)
    checkpoint_path = Path(output).with_name("smoke_roundtrip.pt")
    atomic_save(checkpoint_path, {"purpose": "technical_smoke_only_not_trained_classifier", "model": model.state_dict(), "optimizer": optimizer.state_dict(), "scheduler": scheduler.state_dict(), "scaler": scaler.state_dict(), "rng": capture_rng()}, tensor=True)
    restored = load_checkpoint(checkpoint_path)
    other, _ = build_model(config, len(train.dataset.classes), pretrained=False)
    other.load_state_dict(restored["model"])
    other.to(device).eval()
    restore_rng(restored["rng"])
    with torch.inference_mode():
        torch.testing.assert_close(other(probe), expected, rtol=1e-5, atol=1e-6)
    report = {"passed": True, "purpose": "technical_smoke_only_not_trained_classifier", "device": str(device), "environment": environment(device), "identity_fingerprint": experiment_identity(config, Path(manifest_dir))["fingerprint"], "initialization": initialization, "input_shape": list(images.shape), "output_shape": list(logits.shape), "training_batches": 2, "checkpoint_reload_matches": True, "checkpoint_sha256": sha256_file(checkpoint_path), "seconds": time.perf_counter() - started, "research_metrics_produced": False}
    atomic_save(output, report)
    return report
