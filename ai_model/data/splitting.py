"""Deterministic class-aware splitting of indivisible related-image groups."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from .acquire import save_json, sha256_file
from .audit import RECORD_FIELDS, write_records


SPLITS = ("train", "val", "test")


def validate_no_leakage(partitions: dict[str, list[dict]], classes: list[str]):
    for name in SPLITS:
        rows = partitions[name]
        if not rows or set(classes) != {row["dx"] for row in rows}:
            raise ValueError(f"{name} is empty or lacks class coverage")
    for field in ("image_id", "group_id", "lesion_id", "patient_id", "pixel_sha256"):
        owners = {}
        for split, rows in partitions.items():
            for row in rows:
                value = row.get(field)
                if not value:
                    continue
                if value in owners and owners[value] != split:
                    raise ValueError(f"Cross-split {field} leakage")
                owners[value] = split
    ids = [row["image_id"] for rows in partitions.values() for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Repeated image ID inside manifests")


def assign_groups(records, classes, ratios=(0.7, 0.15, 0.15), seed=42):
    if len(ratios) != 3 or any(ratio <= 0 for ratio in ratios) or abs(sum(ratios) - 1) > 1e-8:
        raise ValueError("Three positive split ratios summing to one are required")
    if not records or len({row["image_id"] for row in records}) != len(records):
        raise ValueError("Records are empty or contain duplicate image IDs")
    groups = defaultdict(list)
    for row in records:
        if row["dx"] not in classes or not row.get("group_id"):
            raise ValueError("Unknown class or missing connected group ID")
        groups[row["group_id"]].append(row)
    totals = Counter(row["dx"] for row in records)
    vectors = {name: Counter(row["dx"] for row in rows) for name, rows in groups.items()}
    availability = Counter(label for vector in vectors.values() for label in vector)
    if any(availability[label] < 3 for label in classes):
        raise ValueError("Each class needs at least three independent groups for train/val/test coverage")
    best = None
    for attempt in range(16):
        rng = random.Random(seed + attempt)
        order = sorted(groups)
        rng.shuffle(order)
        order.sort(key=lambda name: max(vectors[name][label] / totals[label] for label in vectors[name]), reverse=True)
        counts = [Counter() for _ in SPLITS]
        sizes = [0, 0, 0]
        remaining = availability.copy()
        assignment = {}
        for name in order:
            vector = vectors[name]
            for label in vector:
                remaining[label] -= 1
            options = []
            for index, ratio in enumerate(ratios):
                # Reserve enough unassigned groups to fill every still-empty class/split.
                if any(remaining[label] < sum(counts[other][label] == 0 for other in range(3) if other != index) for label in vector):
                    continue
                cost = 0.0
                for label in classes:
                    target = max(totals[label] * ratio, 1)
                    before = counts[index][label] - target
                    cost += ((before + vector[label]) ** 2 - before**2) / target
                target_size = len(records) * ratio
                cost += 0.1 * (((sizes[index] + len(groups[name]) - target_size) ** 2 - (sizes[index] - target_size) ** 2) / target_size)
                options.append((cost, rng.random(), index))
            if not options:
                break
            index = min(options)[2]
            assignment[name] = index
            counts[index].update(vector)
            sizes[index] += len(groups[name])
        if len(assignment) != len(groups):
            continue
        partitions = {split: [] for split in SPLITS}
        for row in records:
            split = SPLITS[assignment[row["group_id"]]]
            partitions[split].append({**row, "split": split})
        try:
            validate_no_leakage(partitions, classes)
        except ValueError:
            continue
        score = sum((counts[index][label] - totals[label] * ratios[index]) ** 2 / max(totals[label] * ratios[index], 1) for index in range(3) for label in classes)
        if best is None or score < best[0]:
            best = score, partitions
    if best is None:
        raise ValueError("No valid group partition found. Review grouping/class coverage; image-level splitting is forbidden.")
    return {split: sorted(rows, key=lambda row: row["image_id"]) for split, rows in best[1].items()}


def verify_manifest_files(directory: Path):
    manifest = json.loads((directory / "manifest_set.json").read_text(encoding="utf-8"))
    for name, checksum in manifest["files_sha256"].items():
        if Path(name).name != name or sha256_file(directory / name) != checksum:
            raise ValueError(f"Manifest bundle was modified: {name}")
    return manifest


def create_manifests(records, spec_path: Path, preprocessing_path: Path, output: Path, seed=42, ratios=(0.7, 0.15, 0.15), duplicate_review: Path | None = None):
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    classes = [item["code"] for item in spec["classes"]]
    if [item["index"] for item in spec["classes"]] != list(range(len(classes))):
        raise ValueError("Class indexes must be contiguous and ordered")
    review_sha256 = sha256_file(duplicate_review) if duplicate_review is not None else None
    canonical = {"records": sorted(records, key=lambda row: row["image_id"]), "seed": seed, "ratios": ratios, "spec_sha256": sha256_file(spec_path), "preprocessing_sha256": sha256_file(preprocessing_path), "duplicate_review_sha256": review_sha256}
    fingerprint = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if output.exists() and any(output.iterdir()):
        if not (output / "manifest_set.json").exists():
            raise ValueError("Output is nonempty without a completed manifest bundle; choose a new output directory")
        previous = verify_manifest_files(output)
        if previous["input_fingerprint"] != fingerprint:
            raise ValueError("Immutable manifests already exist for different inputs/configuration; choose a new output directory")
        return json.loads((output / "split_summary.json").read_text(encoding="utf-8"))
    partitions = assign_groups(records, classes, ratios=ratios, seed=seed)
    output.mkdir(parents=True, exist_ok=True)
    indexes = {code: index for index, code in enumerate(classes)}
    summary = {"seed": seed, "requested_ratios": dict(zip(SPLITS, ratios)), "images": len(records), "connected_groups": len({row["group_id"] for row in records}), "split_counts": {}, "class_counts": {}, "group_counts": {}, "leakage_checks": {"image_id": 0, "group_id": 0, "lesion_id": 0, "pixel_sha256": 0, "patient_id": 0 if all(row.get("patient_id") for row in records) else None}, "input_fingerprint": fingerprint}
    for split, rows in partitions.items():
        for row in rows:
            row["class_index"] = indexes[row["dx"]]
        write_records(output / f"{split}.csv", rows, RECORD_FIELDS + ["class_index", "split"])
        summary["split_counts"][split] = len(rows)
        summary["class_counts"][split] = dict(Counter(row["dx"] for row in rows))
        summary["group_counts"][split] = len({row["group_id"] for row in rows})
    save_json(output / "class_mapping.json", {"dataset": spec["dataset"], "classes": [{key: item[key] for key in ("index", "code", "name")} for item in spec["classes"]]})
    (output / "preprocessing.json").write_bytes(preprocessing_path.read_bytes())
    save_json(output / "split_summary.json", summary)
    names = [f"{split}.csv" for split in SPLITS] + ["class_mapping.json", "preprocessing.json", "split_summary.json"]
    if duplicate_review is not None:
        (output / "duplicate_review.json").write_bytes(duplicate_review.read_bytes())
        names.append("duplicate_review.json")
    save_json(output / "manifest_set.json", {"schema_version": 1, "input_fingerprint": fingerprint, "files_sha256": {name: sha256_file(output / name) for name in names}})
    return summary
