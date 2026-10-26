"""One final test evaluation of a validation-selected, finished E1 run."""

import csv
import json
import time
from pathlib import Path

import numpy as np
import torch

from ai_model.data.acquire import sha256_file
from ai_model.data.dataset import make_loader
from ai_model.models.registry import build_model
from .engine import best_payload, load_checkpoint, predict_loader
from .metrics import save_figures
from .reproducibility import environment, experiment_identity
from .storage import atomic_save, run_lock


def evaluate_run(data_root, manifest_dir, config, run_dir, device, *, confirm_final_test=False, _model_factory=None):
    if not confirm_final_test:
        raise ValueError("Final test evaluation needs --confirm-final-test after validation selection")
    run_dir = Path(run_dir)
    with run_lock(run_dir):
        state = load_checkpoint(run_dir / "last.pt")
        identity = experiment_identity(config, Path(manifest_dir))
        expected_purpose = "technical_fixture_not_research" if _model_factory else "research_training"
        if state["identity"] != identity or state["purpose"] != expected_purpose:
            raise ValueError("Evaluation protocol/code/packages changed, or run is a technical fixture")
        if state["status"] not in ("completed", "early_stopped") or state["best_epoch"] is None:
            raise ValueError("Training must finish before unlocking the test partition")
        best = best_payload(state)
        # Repair a best-file write interrupted after the authoritative last.pt save.
        best_path = run_dir / "best.pt"
        repair = not best_path.is_file()
        if not repair:
            saved = load_checkpoint(best_path)
            repair = saved["identity"] != identity or saved["selected_epoch"] != best["selected_epoch"] or any(not torch.equal(saved["model"][key], value) for key, value in best["model"].items())
        if repair:
            atomic_save(best_path, best, tensor=True)
        selection = {"identity": identity["fingerprint"], "selected_epoch": state["best_epoch"], "validation_macro_f1": state["best_score"]}
        output = run_dir / "evaluation"
        receipt_path = output / "test_selection.json"
        if receipt_path.exists():
            if json.loads(receipt_path.read_text()) != selection:
                raise ValueError("Test was already opened for a different selection; do not retune on test results")
            if (output / "report.json").is_file():
                report = json.loads((output / "report.json").read_text())
                if report["best_checkpoint_sha256"] != sha256_file(best_path):
                    raise ValueError("Evaluated checkpoint bytes changed; inspect saved evidence before repeating test evaluation")
                return report
        atomic_save(receipt_path, selection)
        mapping = json.loads((Path(manifest_dir) / "class_mapping.json").read_text())["classes"]
        model, _ = (_model_factory(len(mapping), False) if _model_factory else build_model(config, len(mapping), pretrained=False))
        model.load_state_dict(best["model"])
        model.to(device).eval()
        loader = make_loader(data_root, manifest_dir, "test", config["batch_size"], config["seed"], config["num_workers"])
        started = time.perf_counter()
        metrics, predictions = predict_loader(model, loader, device)
        evaluation_seconds = time.perf_counter() - started
        # Model-only latency, batch size 1; disk IO and preprocessing excluded.
        image = loader.dataset[0]["image"].unsqueeze(0).to(device)
        with torch.inference_mode():
            for _ in range(5):
                model(image)
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            started = time.perf_counter()
            for _ in range(20):
                model(image)
            if device.type == "cuda":
                torch.cuda.synchronize(device)
        latency = (time.perf_counter() - started) / 20
        report = {
            "experiment": "SYNTHETIC_TEST_ONLY" if _model_factory else config['experiment'], "purpose": expected_purpose, "status": "evaluated_research_model_not_clinically_validated", "selection": selection,
            "best_checkpoint_sha256": sha256_file(run_dir / "best.pt"), "initialization": state["initialization"],
            "test_metrics": metrics, "training_epochs": state["next_epoch"], "training_seconds": state["elapsed_seconds"],
            "total_parameters": state["total_parameters"], "peak_training_cuda_bytes": state["peak_cuda_memory_bytes"],
            "test_evaluation_seconds": evaluation_seconds, "environment": environment(device),
            "latency": {"seconds_per_image": latency, "batch_size": 1, "warmup_iterations": 5, "timed_iterations": 20, "scope": "FP32 model forward only; IO/preprocessing excluded; CUDA synchronized"},
            "limitations": ["Single seed; no uncertainty intervals", "Patient disjointness unknown", "Dermoscopic source domain; smartphone and clinical validity unverified", "Technical duplicate reviews do not validate diagnoses", "Scores are uncalibrated; fusion improvement over baselines must be measured"],
        }
        codes = [item["code"] for item in mapping]
        rows = []
        for index, scores in enumerate(predictions["scores"]):
            predicted = int(np.argmax(scores))
            rows.append({"image_id": predictions["image_ids"][index], "group_id": predictions["group_ids"][index], "source_label": codes[predictions["labels"][index]], "predicted_label": codes[predicted], "max_uncalibrated_score": max(scores), **{f"score_{code}": scores[i] for i, code in enumerate(codes)}})
        with (output / "predictions.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        errors = sorted((row for row in rows if row["source_label"] != row["predicted_label"]), key=lambda row: row["max_uncalibrated_score"], reverse=True)
        atomic_save(output / "error_analysis.json", {"incorrect_images": len(errors), "high_score_errors": errors[:25], "interpretation": "Technical classification errors against source labels; no clinical relabeling. Error examples remain private."})
        save_figures(metrics, state["history"], output)
        lines = [f"# {config['experiment']} research evaluation", "", f"Selected epoch (1-based): {state['best_epoch'] + 1} by validation macro-F1 {state['best_score']:.6f}.", "", f"Test accuracy: {metrics['accuracy']:.6f}; macro-F1: {metrics['macro_f1']:.6f}; balanced accuracy: {metrics['balanced_accuracy']:.6f}.", "", f"Incorrect test images: {len(errors)} / {len(rows)}. See the fixed-order confusion matrix, per-class metrics, ROC curves, and private error-analysis records.", "", "The test results were not used to choose this checkpoint. Compare fusion candidates with both baselines using the fixed protocol.", "", *[f"- {item}" for item in report["limitations"]], ""]
        (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
        # Commit completion last; an interrupted evaluation retries only the same selection.
        atomic_save(output / "report.json", report)
        return report
