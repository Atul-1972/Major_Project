"""Run a declared E1-E4 smoke test, training/resume, or fixed final evaluation."""

import argparse
import json
from pathlib import Path

import torch

from ai_model.data.acquire import DEFAULT_DATA
from .engine import train_run
from .evaluation import evaluate_run
from .reproducibility import ROOT, experiment_identity, load_config
from .smoke import smoke_test


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("smoke", "train", "evaluate"))
    parser.add_argument("--config", type=Path, default=ROOT / "ai_model/config/e1.json")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--manifests", type=Path)
    parser.add_argument("--run-dir", type=Path, default=ROOT / "artifacts/runs/E1-seed42")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--epochs-this-session", type=int)
    parser.add_argument("--confirm-final-test", action="store_true")
    parser.add_argument("--diagnostic-cpu", action="store_true", help="CPU smoke only; never qualifies as the GPU training gate")
    parser.add_argument("--no-pretrained", action="store_true", help="Uninitialized CPU diagnostic smoke only, never research training")
    args = parser.parse_args()
    try:
        torch.set_num_threads(min(4, torch.get_num_threads()))
        if args.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA GPU unavailable. Request one NVIDIA GPU allocation; CPU diagnostics do not qualify as research training.")
        if args.device == "cpu" and (args.action != "smoke" or not args.diagnostic_cpu):
            raise ValueError("Only explicit diagnostic smoke runs use CPU; research training requires the GPU gate")
        if args.no_pretrained and not (args.action == "smoke" and args.device == "cpu" and args.diagnostic_cpu):
            raise ValueError("Research training requires ImageNet initialization")
        config = load_config(args.config)
        manifests = args.manifests or args.data_dir / "processed/splits"
        device = torch.device(args.device)
        report_path = args.run_dir / ("cpu_diagnostic.json" if args.device == "cpu" else "gpu_smoke.json")
        if args.action == "smoke":
            result = smoke_test(args.data_dir, manifests, config, report_path, device, pretrained=not args.no_pretrained)
        elif args.action == "train":
            smoke = json.loads((args.run_dir / "gpu_smoke.json").read_text())
            if not smoke["passed"] or smoke["device"] != "cuda" or not smoke["initialization"]["sha256"] or smoke["identity_fingerprint"] != experiment_identity(config, manifests)["fingerprint"]:
                raise ValueError("Run a passing GPU smoke test with this exact protocol before training")
            state = train_run(args.data_dir, manifests, config, args.run_dir, device, resume=args.resume, epochs_this_session=args.epochs_this_session)
            result = {key: state[key] for key in ("status", "next_epoch", "best_epoch", "best_score")}
        else:
            result = evaluate_run(args.data_dir, manifests, config, args.run_dir, device, confirm_final_test=args.confirm_final_test)
        print(json.dumps(result, indent=2, allow_nan=False), flush=True)
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f"Training command stopped: {error}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
