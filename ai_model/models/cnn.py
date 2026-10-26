"""E1 EfficientNetV2-S with explicit, checksum-recorded ImageNet initialization."""

from pathlib import Path
import time
import urllib.error

import torch
from torch import nn
from torchvision.models import EfficientNet_V2_S_Weights, efficientnet_v2_s

from ai_model.data.acquire import sha256_file


WEIGHTS = EfficientNet_V2_S_Weights.IMAGENET1K_V1
DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "artifacts/torch-cache"


def build_cnn(num_classes=7, *, pretrained=True, cache_dir=DEFAULT_CACHE):
    if num_classes < 2:
        raise ValueError("At least two classes are required")
    model = efficientnet_v2_s(weights=None)
    initialization = {"architecture": "efficientnet_v2_s", "weights_enum": None, "sha256": None, "url": None}
    if pretrained:
        cache = Path(cache_dir)
        cache.mkdir(parents=True, exist_ok=True)
        filename = WEIGHTS.url.rsplit("/", 1)[1]
        path = cache / filename
        prefix = filename.rsplit("-", 1)[1].split(".")[0]
        if not path.exists():
            temporary = path.with_suffix(".download")
            for attempt in range(3):
                try:
                    torch.hub.download_url_to_file(WEIGHTS.url, temporary, hash_prefix=prefix, progress=True)
                    break
                except (OSError, urllib.error.URLError):
                    if attempt == 2:
                        raise
                    time.sleep(1)
            temporary.replace(path)
        digest = sha256_file(path)
        if not digest.startswith(prefix):
            raise ValueError("ImageNet initialization checksum mismatch; cached file was preserved")
        model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
        initialization.update(weights_enum="EfficientNet_V2_S_Weights.IMAGENET1K_V1", sha256=digest, url=WEIGHTS.url)
    model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, num_classes)
    return model, initialization


def set_training_stage(model, *, warmup):
    model.train()
    for parameter in model.features.parameters():
        parameter.requires_grad_(not warmup)
    if warmup:
        # Also freeze backbone BatchNorm buffers and stochastic-depth behavior.
        model.features.eval()
    for parameter in model.classifier.parameters():
        parameter.requires_grad_(True)
