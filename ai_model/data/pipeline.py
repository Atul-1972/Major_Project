"""Phase 2 entry point: audit, freeze group splits, and verify real tensor batches."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from .acquire import DEFAULT_DATA, save_json
from .audit import DEFAULT_SPEC, audit_dataset
from .splitting import SPLITS, create_manifests


PREPROCESSING = Path(__file__).resolve().parents[1] / "config" / "preprocessing.json"


def verify_loaders(data_root: Path, manifest_dir: Path, output: Path, batch_size=8, seed=42):
    import torch

    from .dataset import SkinLesionDataset, make_loader

    torch.set_num_threads(min(4, torch.get_num_threads()))
    torch.manual_seed(seed)
    results = {}
    for split in SPLITS:
        loader = make_loader(data_root, manifest_dir, split, batch_size=batch_size, seed=seed)
        batch = next(iter(loader))
        images, labels = batch["image"], batch["label"]
        size = json.loads((manifest_dir / "preprocessing.json").read_text(encoding="utf-8"))["image_size"]
        if tuple(images.shape[1:]) != (3, size, size) or images.dtype != torch.float32 or labels.dtype != torch.int64 or not torch.isfinite(images).all():
            raise ValueError(f"Invalid {split} tensor batch")
        if labels.min().item() < 0 or labels.max().item() >= len(loader.dataset.classes):
            raise ValueError("Batch label index outside class mapping")
        evaluation = SkinLesionDataset(data_root, manifest_dir, split, training=False)
        deterministic = torch.equal(evaluation[0]["image"], evaluation[0]["image"])
        if not deterministic:
            raise ValueError("Evaluation preprocessing is not deterministic")
        results[split] = {"dataset_images": len(loader.dataset), "batch_shape": list(images.shape), "image_dtype": str(images.dtype), "label_dtype": str(labels.dtype), "finite": True, "deterministic_evaluation": deterministic, "augmentation_enabled": split == "train"}
    report = {"passed": True, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "device": "cpu", "python": platform.python_version(), "packages": {name: importlib.metadata.version(name) for name in ("torch", "torchvision", "numpy", "Pillow")}, "seed": seed, "batches": results, "training_performed": False}
    save_json(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("audit", "prepare", "verify"))
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--metadata", type=Path, help="Optional original HAM10000 CSV instead of the joined ISIC metadata")
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--preprocessing", type=Path, default=PREPROCESSING)
    parser.add_argument("--output", type=Path, help="Audit/output directory; default <data-dir>/processed")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()
    data = args.data_dir.resolve()
    output = args.output.resolve() if args.output else data / "processed"
    try:
        if args.action in ("audit", "prepare"):
            report, records = audit_dataset(args.metadata or data / "metadata.csv", data / "images", output, args.spec)
            print(json.dumps({key: report[key] for key in ("passed", "metadata_rows", "audited_images", "class_counts", "unique_lesions", "connected_groups", "exact_duplicate_groups")}, indent=2), flush=True)
            if not report["passed"]:
                print(f"Audit failed: {len(report['errors'])} issue(s). Inspect {output / 'audit.json'}; splitting/training not allowed.", flush=True)
                return 1
            if args.action == "prepare":
                summary = create_manifests(records, args.spec, args.preprocessing, output / "splits", seed=args.seed)
                print(json.dumps(summary, indent=2), flush=True)
        if args.action in ("prepare", "verify"):
            verification = verify_loaders(data, output / "splits", output / "loader_verification.json", batch_size=args.batch_size, seed=args.seed)
            print(json.dumps(verification, indent=2), flush=True)
    except (OSError, ValueError, KeyError, ImportError) as error:
        print(f"Phase 2 verification failed: {error}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
