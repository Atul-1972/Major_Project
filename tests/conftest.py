"""Small, explicitly synthetic fixtures for testing; never research/training data."""

import csv
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def source_dataset(tmp_path):
    root = tmp_path / "SYNTHETIC_TEST_FIXTURE"
    images = root / "images"
    images.mkdir(parents=True)
    rows = []
    for label_index, label in enumerate(("bcc", "nv")):
        for number in range(6):
            identifier = f"TEST_{label_index}_{number}"
            pixels = np.random.default_rng(label_index * 100 + number).integers(0, 256, size=(128, 160, 3), dtype=np.uint8)
            Image.fromarray(pixels).save(images / f"{identifier}.png")
            rows.append({"image_id": identifier, "lesion_id": f"lesion_{label_index}_{number}", "dx": label, "dx_type": "synthetic fixture only"})
    metadata = root / "metadata.csv"
    with metadata.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    spec = root / "spec.json"
    spec.write_text(json.dumps({"dataset": "SYNTHETIC_TEST_FIXTURE_NOT_RESEARCH_DATA", "expected_images": 12, "classes": [{"index": index, "code": code, "name": code, "expected_images": 6} for index, code in enumerate(("bcc", "nv"))]}), encoding="utf-8")
    config = Path(__file__).resolve().parents[1] / "ai_model/config/preprocessing.json"
    return {"root": root, "images": images, "metadata": metadata, "spec": spec, "config": config, "rows": rows, "output": root / "processed"}


@pytest.fixture
def prepared_dataset(source_dataset):
    from ai_model.data.audit import audit_dataset
    from ai_model.data.splitting import create_manifests

    data = source_dataset
    report, records = audit_dataset(data["metadata"], data["images"], data["output"], data["spec"])
    assert report["passed"], report["errors"]
    data["records"] = records
    data["splits"] = data["output"] / "splits"
    data["summary"] = create_manifests(records, data["spec"], data["config"], data["splits"])
    return data
