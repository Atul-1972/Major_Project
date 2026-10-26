"""Epoch-boundary RNG recovery and immutable experiment provenance."""

import hashlib
import importlib.metadata
import json
import os
import platform
import random
import subprocess
from pathlib import Path

import numpy as np
import torch

from ai_model.data.acquire import sha256_file
from ai_model.data.splitting import verify_manifest_files


ROOT = Path(__file__).resolve().parents[2]


def seed_all(seed, deterministic=True):
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(deterministic)
    torch.backends.cudnn.benchmark = False


def capture_rng():
    numpy = np.random.get_state()
    return {
        "python": random.getstate(), "numpy": [numpy[0], numpy[1].tolist(), numpy[2], numpy[3], numpy[4]],
        "torch": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
    }


def restore_rng(state):
    random.setstate(state["python"])
    numpy = state["numpy"]
    np.random.set_state((numpy[0], np.asarray(numpy[1], dtype=np.uint32), numpy[2], numpy[3], numpy[4]))
    torch.set_rng_state(state["torch"].cpu())
    if state["cuda"] and torch.cuda.is_available():
        if len(state["cuda"]) != torch.cuda.device_count():
            raise ValueError("CUDA device count differs from saved checkpoint")
        torch.cuda.set_rng_state_all([item.cpu() for item in state["cuda"]])


def packages():
    return {name: importlib.metadata.version(name) for name in ("torch", "torchvision", "numpy", "Pillow", "scikit-learn", "matplotlib")}


def source_hashes():
    return {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in sorted((ROOT / "ai_model").rglob("*.py"))}


def experiment_identity(config, manifest_dir):
    manifest = verify_manifest_files(manifest_dir)
    canonical = {"config": config, "manifest": manifest, "source_files": source_hashes(), "packages": packages()}
    fingerprint = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
    return {"fingerprint": fingerprint, **canonical}


def environment(device):
    def git(*args):
        try:
            result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
        except OSError:
            return 'unavailable'
        return result.stdout.strip() if result.returncode == 0 else "unavailable"
    dirty = git("status", "--porcelain")
    result = {"python": platform.python_version(), "platform": platform.platform(), "device": str(device), "packages": packages(), "git_revision": git("rev-parse", "HEAD"), "git_dirty": None if dirty == "unavailable" else bool(dirty), "cuda_available": torch.cuda.is_available()}
    if device.type == "cuda":
        result.update(gpu=torch.cuda.get_device_name(device), cuda_version=torch.version.cuda, cudnn_version=torch.backends.cudnn.version())
    return result


def load_config(path):
    from ai_model.models.registry import ARCHITECTURES

    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config.get("schema_version") != 1 or config.get("experiment") not in ARCHITECTURES or ARCHITECTURES.get(config.get("experiment")) != config.get("architecture") or config.get("weights") != "IMAGENET1K_V1":
        raise ValueError("Only declared ImageNet-initialized E1-E4 protocols are supported")
    for key in ("batch_size", "finetune_epochs", "patience"):
        if type(config[key]) is not int or config[key] < 1:
            raise ValueError(f"Invalid {key}")
    for key in ("seed", "num_workers", "warmup_epochs"):
        if type(config[key]) is not int or config[key] < 0:
            raise ValueError(f"Invalid {key}")
    for key in ("warmup_lr", "finetune_lr", "weight_decay", "gradient_clip_norm"):
        if not isinstance(config[key], (int, float)) or not np.isfinite(config[key]) or config[key] <= 0:
            raise ValueError(f"Invalid {key}")
    if config["class_weighting"] != "inverse_training_frequency" or type(config["amp"]) is not bool or type(config["deterministic"]) is not bool:
        raise ValueError("Invalid loss/AMP/determinism policy")
    return config
