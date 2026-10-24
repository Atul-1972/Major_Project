"""Checksum-verified PyTorch Dataset/DataLoader for the frozen split manifests."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset

from .acquire import sha256_file
from .preprocessing import build_transform
from .splitting import SPLITS, verify_manifest_files


class SkinLesionDataset(Dataset):
    def __init__(self, data_root: Path, manifest_dir: Path, split: str, *, training: bool | None = None):
        if split not in SPLITS:
            raise ValueError("split must be train, val, or test")
        if training is None:
            training = split == "train"
        if training and split != "train":
            raise ValueError("Augmentation is allowed only for the training split")
        self.root = Path(data_root).resolve()
        self.manifest_dir = Path(manifest_dir)
        self.bundle = verify_manifest_files(self.manifest_dir)
        mapping = json.loads((self.manifest_dir / "class_mapping.json").read_text(encoding="utf-8"))
        self.classes = mapping["classes"]
        self.indexes = {item["code"]: item["index"] for item in self.classes}
        if sorted(self.indexes.values()) != list(range(len(self.classes))):
            raise ValueError("Invalid class mapping")
        with (self.manifest_dir / f"{split}.csv").open(encoding="utf-8", newline="") as handle:
            self.records = list(csv.DictReader(handle))
        if not self.records or len({row["image_id"] for row in self.records}) != len(self.records):
            raise ValueError("Empty manifest or duplicate image IDs")
        for row in self.records:
            if row["split"] != split or self.indexes.get(row["dx"]) != int(row["class_index"]):
                raise ValueError("Manifest split or label does not match the class mapping")
            path = (self.root / row["relative_path"]).resolve()
            if not path.is_relative_to(self.root) or not path.is_file():
                raise ValueError("Manifest image path is missing or outside the data root")
        self.transform = build_transform(self.manifest_dir / "preprocessing.json", training=training)

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        record = self.records[index]
        path = (self.root / record["relative_path"]).resolve()
        if not path.is_relative_to(self.root) or sha256_file(path) != record["file_sha256"]:
            raise ValueError(f"Image changed since audit: {record['image_id']}")
        with Image.open(path) as source:
            tensor = self.transform(source)
        if tensor.ndim != 3 or tensor.shape[0] != 3 or not torch.isfinite(tensor).all():
            raise ValueError("Preprocessing produced an invalid tensor")
        return {"image": tensor, "label": torch.tensor(int(record["class_index"]), dtype=torch.long), "image_id": record["image_id"], "group_id": record["group_id"]}


def seed_worker(_worker_id):
    seed = torch.initial_seed() % 2**32
    random.seed(seed)
    np.random.seed(seed)


def make_loader(data_root: Path, manifest_dir: Path, split: str, batch_size=8, seed=42, num_workers=0):
    if batch_size < 1 or num_workers < 0:
        raise ValueError("batch_size must be positive and num_workers nonnegative")
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(SkinLesionDataset(data_root, manifest_dir, split), batch_size=batch_size, shuffle=split == "train", num_workers=num_workers, worker_init_fn=seed_worker, generator=generator, drop_last=False)
