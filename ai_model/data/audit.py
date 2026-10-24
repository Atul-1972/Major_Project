"""Audit source labels and actual images before allowing any split or training."""

from __future__ import annotations

import csv
import hashlib
import json
import struct
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from .acquire import save_json, sha256_file


DEFAULT_SPEC = Path(__file__).resolve().parents[1] / "config" / "dataset_spec.json"
RECORD_FIELDS = ["image_id", "lesion_id", "patient_id", "group_id", "dx", "dx_type", "relative_path", "file_sha256", "pixel_sha256", "dhash", "width", "height", "original_mode"]


class UnionFind:
    def __init__(self, identifiers):
        self.parents = {identifier: identifier for identifier in identifiers}

    def find(self, identifier):
        while self.parents[identifier] != identifier:
            self.parents[identifier] = self.parents[self.parents[identifier]]
            identifier = self.parents[identifier]
        return identifier

    def join(self, left, right):
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parents[max(a, b)] = min(a, b)


class HashTree:
    """BK-tree of 64-bit perceptual hashes for bounded Hamming-distance queries."""
    def __init__(self):
        self.root = None

    def add(self, value, identifier):
        if self.root is None:
            self.root = [value, [identifier], {}]
            return
        node = self.root
        while True:
            distance = (value ^ node[0]).bit_count()
            if distance == 0:
                node[1].append(identifier)
                return
            if distance not in node[2]:
                node[2][distance] = [value, [identifier], {}]
                return
            node = node[2][distance]

    def query(self, value, radius):
        pending = [self.root] if self.root is not None else []
        while pending:
            node = pending.pop()
            distance = (value ^ node[0]).bit_count()
            if distance <= radius:
                for identifier in node[1]:
                    yield identifier, distance
            pending.extend(child for edge, child in node[2].items() if distance - radius <= edge <= distance + radius)


def image_features(path: Path, max_pixels=20_000_000, min_dimension=128):
    if path.stat().st_size > 20 * 1024**2:
        raise ValueError("Encoded image exceeds 20 MiB audit limit")
    with Image.open(path) as probe:
        if probe.format not in ("JPEG", "PNG") or getattr(probe, "n_frames", 1) != 1:
            raise ValueError("Unsupported format or multiframe image")
        if min(probe.size) < min_dimension or probe.width * probe.height > max_pixels:
            raise ValueError("Image dimensions are outside audit limits")
        original_mode = probe.mode
        probe.verify()
    with Image.open(path) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
        pixels = np.asarray(image)
        pixel_digest = hashlib.sha256(struct.pack("!II", image.width, image.height) + pixels.tobytes()).hexdigest()
        gray = np.asarray(image.convert("L").resize((9, 8), Image.Resampling.LANCZOS))
        bits = (gray[:, 1:] > gray[:, :-1]).flatten()
        dhash = sum(int(bit) << index for index, bit in enumerate(bits))
        thumbnail = np.asarray(image.resize((8, 8), Image.Resampling.BILINEAR), dtype=np.float32)
        return {"file_sha256": sha256_file(path), "pixel_sha256": pixel_digest, "dhash": f"{dhash:016x}", "width": image.width, "height": image.height, "original_mode": original_mode}, thumbnail


def write_records(path: Path, records: list[dict], fields=RECORD_FIELDS):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    temporary.replace(path)


def audit_dataset(metadata: Path, images: Path, output: Path, spec_path: Path = DEFAULT_SPEC,
                  near_hash_distance: int = 2, near_pixel_distance: float = 0.03):
    if not metadata.is_file() or not images.is_dir():
        raise ValueError("Metadata/images are missing. Run acquisition or supply the actual source files first.")
    if not 0 <= near_hash_distance <= 4 or not 0 <= near_pixel_distance <= 0.1:
        raise ValueError("Near-duplicate thresholds exceed the documented conservative range")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    classes = [item["code"] for item in spec["classes"]]
    errors, warnings = [], []
    with metadata.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if not {"image_id", "lesion_id", "dx"}.issubset(fields):
            raise ValueError("Metadata must contain image_id, lesion_id and dx")
        rows = [{key: (value or "").strip() for key, value in row.items() if key is not None} for row in reader]
    if not rows:
        raise ValueError("Metadata contains no rows")
    files = defaultdict(list)
    for path in sorted(images.rglob("*")):
        if path.is_file() and path.suffix.lower() in (".jpg", ".jpeg", ".png"):
            files[path.stem].append(path)
    identifiers = [row["image_id"] for row in rows]
    repeated = sorted(key for key, count in Counter(identifiers).items() if count > 1)
    if repeated:
        errors.append({"code": "repeated_image_ids", "image_ids": repeated})
    extra = sorted(set(files) - set(identifiers))
    if extra:
        errors.append({"code": "unlabelled_images", "image_ids": extra})
    patients = [row.get("patient_id", "") for row in rows]
    patient_available = all(patients)
    if any(patients) and not patient_available:
        errors.append({"code": "partial_patient_identifiers", "message": "Resolve missing patient IDs before claiming a patient-group split"})
    if not any(patients):
        warnings.append("No patient identifiers: lesion-disjoint splits cannot establish patient-disjointness.")

    records, thumbnails = [], {}
    seen = set()
    for number, row in enumerate(rows, 1):
        identifier = row["image_id"]
        if not identifier or not row["lesion_id"] or row["dx"] not in classes:
            errors.append({"code": "invalid_metadata", "row": number, "image_id": identifier})
            continue
        if identifier in seen:
            continue
        seen.add(identifier)
        candidates = files.get(identifier, [])
        if len(candidates) != 1:
            errors.append({"code": "missing_or_ambiguous_image", "image_id": identifier, "file_count": len(candidates)})
            continue
        path = candidates[0]
        if not path.resolve().is_relative_to(images.resolve()):
            errors.append({"code": "image_outside_dataset", "image_id": identifier})
            continue
        try:
            features, thumbnail = image_features(path)
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            errors.append({"code": "unreadable_or_invalid_image", "image_id": identifier, "message": str(error)})
            continue
        records.append({**features, "image_id": identifier, "lesion_id": row["lesion_id"], "patient_id": row.get("patient_id", ""), "dx": row["dx"], "dx_type": row.get("dx_type", ""), "relative_path": path.resolve().relative_to(images.parent.resolve()).as_posix()})
        thumbnails[identifier] = thumbnail
        if number % 1000 == 0:
            print(f"Audited {number}/{len(rows)} metadata rows", flush=True)
    records.sort(key=lambda record: record["image_id"])
    union = UnionFind(record["image_id"] for record in records)
    for field in ("lesion_id", "patient_id", "pixel_sha256"):
        first = {}
        labels = defaultdict(set)
        for record in records:
            value = record[field]
            if not value:
                continue
            labels[value].add(record["dx"])
            if value in first:
                union.join(first[value], record["image_id"])
            else:
                first[value] = record["image_id"]
        if field in ("lesion_id", "pixel_sha256"):
            conflicts = [value for value, values in labels.items() if len(values) > 1]
            if conflicts:
                errors.append({"code": f"conflicting_labels_for_{field}", "identifiers": conflicts})
    tree = HashTree()
    by_id = {record["image_id"]: record for record in records}
    near_pairs = []
    for record in records:
        identifier = record["image_id"]
        value = int(record["dhash"], 16)
        for other_id, distance in tree.query(value, near_hash_distance):
            other = by_id[other_id]
            if other["pixel_sha256"] == record["pixel_sha256"]:
                continue
            difference = float(np.abs(thumbnails[identifier] - thumbnails[other_id]).mean() / 255)
            if difference <= near_pixel_distance:
                near_pairs.append({"left": other_id, "right": identifier, "hamming_distance": distance, "mean_thumbnail_difference": round(difference, 6)})
                if other["dx"] != record["dx"]:
                    errors.append({"code": "near_duplicate_label_conflict", "image_ids": [other_id, identifier]})
                union.join(other_id, identifier)
        tree.add(value, identifier)
    groups = defaultdict(list)
    for record in records:
        groups[union.find(record["image_id"])].append(record["image_id"])
    group_names = {root: "group_" + hashlib.sha256("|".join(sorted(members)).encode()).hexdigest()[:16] for root, members in groups.items()}
    for record in records:
        record["group_id"] = group_names[union.find(record["image_id"])]
    counts = Counter(row["dx"] for row in rows)
    if len(rows) != spec["expected_images"] or dict(counts) != {item["code"]: item["expected_images"] for item in spec["classes"]}:
        errors.append({"code": "release_counts_differ", "expected_images": spec["expected_images"], "observed_images": len(rows), "observed_classes": dict(counts)})
    missing_classes = sorted(set(classes) - {record["dx"] for record in records})
    if missing_classes:
        errors.append({"code": "missing_valid_classes", "classes": missing_classes})
    pixel_counts = Counter(record["pixel_sha256"] for record in records)
    report = {
        "schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": spec["dataset"], "passed": not errors, "metadata_sha256": sha256_file(metadata),
        "metadata_rows": len(rows), "audited_images": len(records), "class_counts": dict(counts),
        "unique_lesions": len({record["lesion_id"] for record in records}),
        "unique_patients": len(set(patients)) if patient_available else None,
        "grouping_basis": "patient+lesion+duplicate components" if patient_available else "lesion+duplicate components; patient disjointness unknown",
        "connected_groups": len(groups), "exact_duplicate_groups": sum(count > 1 for count in pixel_counts.values()),
        "near_duplicate_policy": {"hash_hamming_max": near_hash_distance, "thumbnail_mean_difference_max": near_pixel_distance, "action": "keep connected pairs in the same split; fail conflicting diagnoses"},
        "near_duplicate_pairs": near_pairs,
        "image_modes": dict(Counter(record["original_mode"] for record in records)),
        "dimensions": dict(Counter(f"{record['width']}x{record['height']}" for record in records)),
        "missing_demographics": {field: sum(not row.get(field) or row.get(field) == "unknown" for row in rows) if field in fields else "not supplied by this distribution" for field in ("age", "sex", "localization")},
        "warnings": warnings + ["Perceptual matching is a heuristic; absence of flagged pairs does not prove absence of all related images."],
        "errors": errors,
    }
    output.mkdir(parents=True, exist_ok=True)
    save_json(output / "audit.json", report)
    write_records(output / "audited_images.csv", records)
    return report, records
