"""Check Phase 1 readiness without installing packages or importing ML libraries."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGES = (
    "torch", "torchvision", "fastapi", "uvicorn", "numpy", "pandas",
    "scikit-learn", "Pillow", "matplotlib", "pytest",
)
REQUIRED_PATHS = (
    "AGENTS.md", "README.md", ".gitignore", ".env.example", "LICENSE",
    ".project/state.json", "docs/APPROVALS.md", "docs/REQUIREMENTS.md",
    "docs/ARCHITECTURE.md", "docs/DATASET_PLAN.md", "docs/EXPERIMENT_PLAN.md",
    "ai_model/config", "ai_model/data", "ai_model/models", "ai_model/training",
    "ai_model/evaluation", "ai_model/explainability", "ai_model/notebooks",
    "ai_model/checkpoints", "ai_model/exports", "ai_model/results",
    "backend/app", "backend/tests", "frontend/templates", "frontend/static",
    "mobile_app/README.md", "reports", "data", "requirements/phase1.txt",
)


def command(arguments: list[str]) -> dict:
    try:
        result = subprocess.run(
            arguments, cwd=ROOT, capture_output=True, text=True,
            timeout=15, check=False,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"returncode": None, "stdout": "", "stderr": str(error)}


def collect(require_ml: bool) -> dict:
    packages = {}
    for name in PACKAGES:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None

    checks = []
    checks.append({"name": "python", "passed": sys.version_info >= (3, 11), "detail": platform.python_version()})
    missing = [name for name in REQUIRED_PATHS if not (ROOT / name).exists()]
    checks.append({"name": "structure", "passed": not missing, "detail": missing})

    git = command(["git", "--version"])
    git_root = command(["git", "rev-parse", "--show-toplevel"])
    exact_repository = (
        git_root["returncode"] == 0
        and Path(git_root["stdout"]).resolve() == ROOT
    )
    checks.append({"name": "git_repository", "passed": exact_repository, "detail": git_root})

    disk = shutil.disk_usage(ROOT)
    checks.append({
        "name": "working_disk_space", "passed": disk.free >= 1024**3,
        "detail": f"{disk.free / 1024**3:.2f} GiB free; 1 GiB minimum for Phase 1 only",
    })
    try:
        state = json.loads((ROOT / ".project/state.json").read_text(encoding="utf-8"))
        history = [
            json.loads(line)
            for line in (ROOT / ".project/history.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        current = bool(history) and all(history[-1].get(key) == value for key, value in state.items())
        checks.append({"name": "checkpoint_consistency", "passed": current, "detail": state.get("phase")})
    except (OSError, ValueError, TypeError, AttributeError) as error:
        checks.append({"name": "checkpoint_consistency", "passed": False, "detail": str(error)})

    if require_ml:
        missing_ml = [name for name in ("torch", "torchvision", "numpy", "pandas", "scikit-learn", "Pillow", "matplotlib") if packages[name] is None]
        checks.append({"name": "ml_packages_present", "passed": not missing_ml, "detail": missing_ml})

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": "SkinDiseaseAI",
        "python": {
            "version": platform.python_version(), "executable": sys.executable,
            "virtual_environment": sys.prefix != sys.base_prefix,
        },
        "system": {"platform": platform.platform(), "logical_cpu_count": os.cpu_count()},
        "free_disk_gib": round(disk.free / 1024**3, 2),
        "git_version": git,
        "nvidia_smi_path": shutil.which("nvidia-smi"),
        "packages": packages,
        "checks": checks,
        "passed": all(check["passed"] for check in checks),
        "scope": "Phase 1 structure/environment checks. Package presence is not import compatibility, GPU availability, or model validation.",
        "training_status": "Not started; no dataset audit or trained checkpoint verified.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON report path; relative paths are resolved from the repository")
    parser.add_argument("--require-ml", action="store_true", help="Also fail if required ML packages are absent; does not test imports")
    args = parser.parse_args()
    report = collect(args.require_ml)
    content = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        destination = args.output if args.output.is_absolute() else ROOT / args.output
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
    print(content, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
