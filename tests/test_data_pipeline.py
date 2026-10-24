import csv
import json
import shutil
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

from ai_model.data.acquire import sha256_file
from ai_model.data.audit import audit_dataset
from ai_model.data.dataset import SkinLesionDataset, make_loader
from ai_model.data.pipeline import verify_loaders
from ai_model.data.preprocessing import LetterboxResize, build_transform, load_config
from ai_model.data.splitting import assign_groups, create_manifests, validate_no_leakage, verify_manifest_files


def test_audit_and_all_split_loader_batches(prepared_dataset):
    data = prepared_dataset
    report = verify_loaders(data["root"], data["splits"], data["output"] / "loader_verification.json", batch_size=2)
    assert report["passed"] and report["training_performed"] is False
    assert report["device"] == "cpu"
    for batch in report["batches"].values():
        assert batch["batch_shape"] == [2, 3, 224, 224]
        assert batch["finite"] and batch["deterministic_evaluation"]


def test_audit_reports_missing_corrupt_extra_and_repeated_images(source_dataset):
    data = source_dataset
    (data["images"] / "TEST_0_0.png").unlink()
    (data["images"] / "TEST_0_1.png").write_bytes(b"not an image")
    Image.new("RGB", (128, 128)).save(data["images"] / "UNLABELLED.png")
    with data["metadata"].open("a", encoding="utf-8") as handle:
        handle.write("TEST_0_2,other_lesion,bcc,synthetic\n")
    report, _ = audit_dataset(data["metadata"], data["images"], data["output"], data["spec"])
    assert report["passed"] is False
    codes = {error["code"] for error in report["errors"]}
    assert {"missing_or_ambiguous_image", "unreadable_or_invalid_image", "unlabelled_images", "repeated_image_ids", "release_counts_differ"} <= codes


def test_duplicate_images_connect_different_lesion_groups(source_dataset):
    data = source_dataset
    shutil.copyfile(data["images"] / "TEST_0_0.png", data["images"] / "TEST_0_1.png")
    report, records = audit_dataset(data["metadata"], data["images"], data["output"], data["spec"])
    assert report["passed"]
    by_id = {row["image_id"]: row for row in records}
    assert by_id["TEST_0_0"]["group_id"] == by_id["TEST_0_1"]["group_id"]
    assert report["exact_duplicate_groups"] == 1
    partitions = assign_groups(records, ["bcc", "nv"])
    validate_no_leakage(partitions, ["bcc", "nv"])


def test_near_duplicate_images_are_connected(source_dataset):
    data = source_dataset
    with Image.open(data["images"] / "TEST_0_0.png") as image:
        pixels = np.array(image)
    pixels[0, 0, 0] ^= 1
    Image.fromarray(pixels).save(data["images"] / "TEST_0_1.png")
    report, records = audit_dataset(data["metadata"], data["images"], data["output"], data["spec"])
    assert report["passed"]
    by_id = {row["image_id"]: row for row in records}
    assert by_id["TEST_0_0"]["pixel_sha256"] != by_id["TEST_0_1"]["pixel_sha256"]
    assert by_id["TEST_0_0"]["group_id"] == by_id["TEST_0_1"]["group_id"]
    assert report["near_duplicate_pairs"]


def test_conflicting_duplicate_labels_fail_audit(source_dataset):
    data = source_dataset
    shutil.copyfile(data["images"] / "TEST_0_0.png", data["images"] / "TEST_1_0.png")
    report, _ = audit_dataset(data["metadata"], data["images"], data["output"], data["spec"])
    assert not report["passed"]
    assert any(error["code"] == "conflicting_labels_for_pixel_sha256" for error in report["errors"])


def test_partial_patient_identifiers_fail(source_dataset):
    data = source_dataset
    with data["metadata"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*data["rows"][0], "patient_id"])
        writer.writeheader()
        writer.writerows([{**row, "patient_id": "patient1" if index == 0 else ""} for index, row in enumerate(data["rows"])])
    report, _ = audit_dataset(data["metadata"], data["images"], data["output"], data["spec"])
    assert any(error["code"] == "partial_patient_identifiers" for error in report["errors"])


def test_available_patient_ids_connect_different_lesions_and_diagnoses(source_dataset):
    data = source_dataset
    with data["metadata"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*data["rows"][0], "patient_id"])
        writer.writeheader()
        writer.writerows([{**row, "patient_id": "shared-patient" if row["image_id"] in ("TEST_0_0", "TEST_1_0") else row["image_id"]} for row in data["rows"]])
    report, records = audit_dataset(data["metadata"], data["images"], data["output"], data["spec"])
    assert report["passed"] and report["unique_patients"] == 11
    by_id = {row["image_id"]: row for row in records}
    assert by_id["TEST_0_0"]["group_id"] == by_id["TEST_1_0"]["group_id"]
    validate_no_leakage(assign_groups(records, ["bcc", "nv"]), ["bcc", "nv"])


def test_splits_repeat_deterministically_and_never_overwrite(prepared_dataset):
    data = prepared_dataset
    first = assign_groups(data["records"], ["bcc", "nv"], seed=42)
    second = assign_groups(list(reversed(data["records"])), ["bcc", "nv"], seed=42)
    assert first == second
    assert data["summary"]["leakage_checks"]["patient_id"] is None
    assert create_manifests(data["records"], data["spec"], data["config"], data["splits"]) == data["summary"]
    with pytest.raises(ValueError, match="Immutable manifests"):
        create_manifests(data["records"], data["spec"], data["config"], data["splits"], seed=43)


def test_too_few_independent_groups_never_fall_back_to_row_splitting():
    records = [{"image_id": f"image{index}", "group_id": f"group{index % 2}", "dx": "nv"} for index in range(6)]
    with pytest.raises(ValueError, match="three independent groups"):
        assign_groups(records, ["nv"])


def test_cross_split_patient_leakage_is_detected(prepared_dataset):
    data = prepared_dataset
    partitions = assign_groups(data["records"], ["bcc", "nv"])
    partitions["train"][0]["patient_id"] = "shared-patient"
    partitions["val"][0]["patient_id"] = "shared-patient"
    with pytest.raises(ValueError, match="patient_id leakage"):
        validate_no_leakage(partitions, ["bcc", "nv"])


def test_modified_manifest_and_modified_source_are_rejected(prepared_dataset):
    data = prepared_dataset
    dataset = SkinLesionDataset(data["root"], data["splits"], "val")
    path = data["root"] / dataset.records[0]["relative_path"]
    Image.new("RGB", (160, 128), "red").save(path)
    with pytest.raises(ValueError, match="changed since audit"):
        dataset[0]
    with (data["splits"] / "val.csv").open("a") as handle:
        handle.write("modified\n")
    with pytest.raises(ValueError, match="Manifest bundle was modified"):
        verify_manifest_files(data["splits"])


def test_evaluation_has_no_augmentation_and_repeats_exactly(prepared_dataset):
    data = prepared_dataset
    for split in ("val", "test"):
        with pytest.raises(ValueError, match="training split"):
            SkinLesionDataset(data["root"], data["splits"], split, training=True)
        dataset = SkinLesionDataset(data["root"], data["splits"], split)
        assert torch.equal(dataset[0]["image"], dataset[0]["image"])
        assert dataset[0]["image"].shape == (3, 224, 224)
        assert dataset[0]["label"].dtype == torch.int64


def test_letterboxing_preserves_full_image_and_rgb_padding():
    fill = (124, 116, 104)
    image = Image.new("RGB", (200, 100), (255, 0, 0))
    result = LetterboxResize(224, fill)(image)
    assert result.size == (224, 224)
    assert result.getpixel((112, 0)) == fill
    assert result.getpixel((112, 112)) == (255, 0, 0)
    assert result.getpixel((0, 112)) == (255, 0, 0)
    tensor = build_transform()(image)
    expected = (torch.tensor([1.0, 0.0, 0.0]) - torch.tensor([0.485, 0.456, 0.406])) / torch.tensor([0.229, 0.224, 0.225])
    assert torch.allclose(tensor[:, 112, 112], expected)


def test_invalid_preprocessing_config_is_rejected(tmp_path):
    original = Path(__file__).resolve().parents[1] / "ai_model/config/preprocessing.json"
    config = json.loads(original.read_text())
    config["std"][0] = 0
    target = tmp_path / "invalid.json"
    target.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="positive"):
        load_config(target)


def test_orientation_is_normalized_before_letterboxing():
    image = Image.new("RGB", (200, 100), (255, 0, 0))
    image.getexif()[274] = 6
    result = LetterboxResize(224, (124, 116, 104))(image)
    assert result.getpixel((0, 112)) == (124, 116, 104)
    assert result.getpixel((112, 0)) == (255, 0, 0)


def test_seeded_loader_order_repeats_without_dropping_images(prepared_dataset):
    data = prepared_dataset
    first = make_loader(data["root"], data["splits"], "train", batch_size=3, seed=123)
    second = make_loader(data["root"], data["splits"], "train", batch_size=3, seed=123)
    ids = [identifier for batch in first for identifier in batch["image_id"]]
    assert ids == [identifier for batch in second for identifier in batch["image_id"]]
    assert len(ids) == len(first.dataset) == len(set(ids))


def test_dataset_rejects_manifest_path_escape_even_with_valid_hashes(prepared_dataset):
    data = prepared_dataset
    csv_path = data["splits"] / "val.csv"
    with csv_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        rows = list(reader)
    rows[0]["relative_path"] = "../outside.png"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = data["splits"] / "manifest_set.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files_sha256"]["val.csv"] = sha256_file(csv_path)
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="outside the data root"):
        SkinLesionDataset(data["root"], data["splits"], "val")
