"""One configured image transform shared by training, evaluation, and inference."""

from __future__ import annotations

import json
import math
from pathlib import Path

import torch
from PIL import Image, ImageOps
from torchvision.transforms import v2


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "preprocessing.json"


def load_config(path: Path = DEFAULT_CONFIG):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config.get("schema_version") != 1 or config.get("color_mode") != "RGB" or config.get("normalize_exif_orientation") is not True:
        raise ValueError("Unsupported preprocessing version, color mode or orientation policy")
    if config.get("resize_policy") != "aspect_preserving_letterbox" or config.get("interpolation") != "bilinear":
        raise ValueError("Unsupported resize/interpolation policy")
    size = config.get("image_size")
    if not isinstance(size, int) or not 32 <= size <= 1024:
        raise ValueError("image_size must be an integer between 32 and 1024")
    fill = config.get("fill_rgb", [])
    if len(fill) != 3 or any(not isinstance(value, int) or not 0 <= value <= 255 for value in fill):
        raise ValueError("fill_rgb must contain three byte values")
    for field in ("mean", "std"):
        values = config.get(field, [])
        if len(values) != 3 or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values):
            raise ValueError(f"Invalid normalization {field}")
    if any(value <= 0 for value in config["std"]):
        raise ValueError("Normalization standard deviations must be positive")
    augmentation = config.get("training_augmentation", {})
    expected = {"horizontal_flip_probability", "vertical_flip_probability", "brightness", "contrast", "saturation"}
    if set(augmentation) != expected or any(not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1 for value in augmentation.values()):
        raise ValueError("Invalid training augmentation configuration")
    return config


class LetterboxResize:
    """Normalize orientation and fit the entire image without stretching/cropping."""
    def __init__(self, size: int, fill: tuple[int, int, int]):
        self.size = size
        self.fill = fill

    def __call__(self, image: Image.Image):
        image = ImageOps.exif_transpose(image).convert("RGB")
        return ImageOps.pad(image, (self.size, self.size), method=Image.Resampling.BILINEAR, color=self.fill, centering=(0.5, 0.5))


def build_transform(config_path: Path = DEFAULT_CONFIG, training=False):
    config = load_config(config_path)
    operations = [LetterboxResize(config["image_size"], tuple(config["fill_rgb"]))]
    if training:
        augmentation = config["training_augmentation"]
        operations.extend([
            v2.RandomHorizontalFlip(p=augmentation["horizontal_flip_probability"]),
            v2.RandomVerticalFlip(p=augmentation["vertical_flip_probability"]),
            v2.ColorJitter(brightness=augmentation["brightness"], contrast=augmentation["contrast"], saturation=augmentation["saturation"]),
        ])
    operations.extend([v2.ToImage(), v2.ToDtype(torch.float32, scale=True), v2.Normalize(mean=config["mean"], std=config["std"])])
    return v2.Compose(operations)
