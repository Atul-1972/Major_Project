"""Download the official ISIC HAM10000 distribution and preserve provenance."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import time
import urllib.error
import urllib.request
import zipfile
import zlib
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT / "data" / "ham10000"
BASE = "https://isic-archive.s3.amazonaws.com/challenges/2018/"
REGIONAL_BASE = "https://isic-archive.s3.us-east-1.amazonaws.com/challenges/2018/"
INPUT = "ISIC2018_Task3_Training_Input.zip"
TRUTH = "ISIC2018_Task3_Training_GroundTruth.zip"
GROUPS = "ISIC2018_Task3_Training_LesionGroupings.csv"
CLASSES = ("akiec", "bcc", "bkl", "df", "mel", "nv", "vasc")
LICENSE = "https://creativecommons.org/licenses/by-nc/4.0/"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def download(filename: str, destination: Path) -> dict:
    """Resume only with a stored entity tag; never reuse an unverified final file."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    receipt_path = destination.with_name(destination.name + ".receipt.json")
    if destination.exists():
        if not receipt_path.exists():
            raise ValueError(f"Existing {destination.name} has no receipt; preserve it and use a different download directory")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if sha256_file(destination) != receipt["sha256"]:
            raise ValueError(f"Checksum mismatch in existing {destination.name}")
        print(f"Verified cached {filename}", flush=True)
        return receipt
    partial = destination.with_name(destination.name + ".part")
    partial_meta = partial.with_name(partial.name + ".json")
    previous = json.loads(partial_meta.read_text(encoding="utf-8")) if partial_meta.exists() else {}
    offset = partial.stat().st_size if partial.exists() and previous.get("etag") else 0
    headers = {"User-Agent": "SkinDiseaseAI-academic-data-pipeline/1.0"}
    if offset:
        headers.update({"Range": f"bytes={offset}-", "If-Range": previous["etag"]})
    url = BASE + filename
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
        if "text/html" in response.headers.get("Content-Type", ""):
            raise ValueError("Provider returned an HTML page instead of dataset content")
        resumed = response.status == 206 and offset > 0
        if resumed and not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-"):
            raise ValueError("Invalid Content-Range; partial download was preserved")
        if not resumed:
            offset = 0
        remaining = int(response.headers["Content-Length"]) if response.headers.get("Content-Length") else None
        total = offset + remaining if remaining is not None else None
        if total and shutil.disk_usage(destination.parent).free < total - offset + 1024**3:
            raise ValueError("Insufficient disk space for download plus 1 GiB reserve")
        metadata = {"url": url, "etag": response.headers.get("ETag"), "last_modified": response.headers.get("Last-Modified"), "bytes_expected": total}
        save_json(partial_meta, metadata)
        written = offset
        next_log = written + 64 * 1024**2
        print(f"Downloading {filename}: starting at {offset:,} bytes; total {total}", flush=True)
        with partial.open("ab" if resumed else "wb") as handle:
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                handle.write(chunk)
                written += len(chunk)
                if written >= next_log:
                    print(f"{filename}: {written / 1024**2:.0f} MiB saved", flush=True)
                    next_log = written + 64 * 1024**2
            handle.flush()
            os.fsync(handle.fileno())
    if total is not None and written != total:
        raise ValueError(f"Incomplete download: {written} of {total} bytes; rerun to resume")
    receipt = {**metadata, "bytes": written, "sha256": sha256_file(partial), "acquired_at_utc": datetime.now(timezone.utc).isoformat(), "license_url": LICENSE}
    save_json(receipt_path, receipt)
    os.replace(partial, destination)
    return receipt


def download_parallel(filename: str, destination: Path, workers=4, chunk_size=32 * 1024**2) -> dict:
    """Use validated byte ranges while retaining one contiguous resumable prefix."""
    if destination.exists():
        return download(filename, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    url = BASE + filename
    with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60) as response:
        total = int(response.headers["Content-Length"])
        etag = response.headers.get("ETag")
        modified = response.headers.get("Last-Modified")
    if not etag:
        raise ValueError("Parallel resume requires the provider's entity tag")
    partial = destination.with_name(destination.name + ".part")
    partial_meta = partial.with_name(partial.name + ".json")
    previous = json.loads(partial_meta.read_text(encoding="utf-8")) if partial_meta.exists() else {}
    offset = partial.stat().st_size if partial.exists() else 0
    if offset and (previous.get("etag") != etag or previous.get("bytes_expected") != total):
        raise ValueError("Saved partial does not match the current source; it has been preserved")
    if offset > total or shutil.disk_usage(destination.parent).free < total - offset + 1024**3:
        raise ValueError("Invalid partial length or insufficient disk space")
    metadata = {"url": url, "etag": etag, "last_modified": modified, "bytes_expected": total}
    save_json(partial_meta, metadata)
    chunks = destination.parent / ("." + filename + ".chunks")
    chunks.mkdir(exist_ok=True)

    def fetch(start, end):
        target = chunks / f"{start}-{end}.bin"
        receipt = target.with_suffix(".json")
        if target.exists() and receipt.exists():
            saved = json.loads(receipt.read_text(encoding="utf-8"))
            if saved.get("etag") == etag and target.stat().st_size == end - start + 1 and sha256_file(target) == saved.get("sha256"):
                return start, target
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}", "If-Match": etag})
                with urllib.request.urlopen(request, timeout=60) as response:
                    if response.status != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{total}" or response.headers.get("ETag") != etag:
                        raise ValueError("Provider did not honor the exact byte range/entity tag")
                    temporary = target.with_suffix(".part")
                    with temporary.open("wb") as handle:
                        shutil.copyfileobj(response, handle, length=1024**2)
                    if temporary.stat().st_size != end - start + 1:
                        raise ValueError("Incomplete byte-range response")
                    os.replace(temporary, target)
                    save_json(receipt, {"etag": etag, "sha256": sha256_file(target)})
                    return start, target
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt == 2:
                    raise
                time.sleep(2)

    ranges = [(start, min(start + chunk_size, total) - 1) for start in range(offset, total, chunk_size)]
    ready = {}
    print(f"Downloading {filename}: {workers} ranged connections, resuming {offset / 1024**2:.0f}/{total / 1024**2:.0f} MiB", flush=True)
    with partial.open("ab") as output, ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(fetch, start, end) for start, end in ranges]
        for future in as_completed(futures):
            start, target = future.result()
            ready[start] = target
            while offset in ready:
                target = ready.pop(offset)
                length = target.stat().st_size
                with target.open("rb") as handle:
                    shutil.copyfileobj(handle, output, length=1024**2)
                output.flush()
                os.fsync(output.fileno())
                offset += length
                target.unlink()
                target.with_suffix(".json").unlink()
                print(f"Contiguous download saved: {offset / 1024**2:.0f}/{total / 1024**2:.0f} MiB", flush=True)
    if partial.stat().st_size != total:
        raise ValueError("Ranged download is incomplete; partial data is retained")
    receipt = {**metadata, "bytes": total, "sha256": sha256_file(partial), "acquired_at_utc": datetime.now(timezone.utc).isoformat(), "license_url": LICENSE}
    save_json(destination.with_name(destination.name + ".receipt.json"), receipt)
    os.replace(partial, destination)
    return receipt


def validate_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = archive.infolist()
    if len(members) > 20050 or sum(member.file_size for member in members) > 12 * 1024**3:
        raise ValueError("Archive exceeds permitted member count or extracted size")
    for member in members:
        path = PurePosixPath(member.filename)
        if path.is_absolute() or ".." in path.parts or "\\" in member.filename or ":" in member.filename:
            raise ValueError("Unsafe archive member path")
        if (member.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError("Archive symlinks are not allowed")
    return members


def extract_images(archive_path: Path, directory: Path) -> int:
    directory.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        members = [member for member in validate_members(archive) if not member.is_dir() and re.fullmatch(r"ISIC_\d{7}\.jpg", PurePosixPath(member.filename).name)]
        names = [PurePosixPath(member.filename).name for member in members]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate image filenames in archive")
        if not members or any(member.file_size > 20 * 1024**2 for member in members):
            raise ValueError("Missing images or excessive individual image size")
        needed = sum(member.file_size for member in members if not (directory / PurePosixPath(member.filename).name).exists())
        if shutil.disk_usage(directory).free < needed + 1024**3:
            raise ValueError("Insufficient disk space to extract images")
        for number, member in enumerate(members, 1):
            target = directory / PurePosixPath(member.filename).name
            if target.exists():
                with target.open("rb") as handle:
                    crc = 0
                    for chunk in iter(lambda: handle.read(1024**2), b""):
                        crc = zlib.crc32(chunk, crc)
                if target.stat().st_size != member.file_size or crc != member.CRC:
                    raise ValueError(f"Existing image differs from archive: {target.name}")
                continue
            temporary = target.with_suffix(".jpg.part")
            with archive.open(member) as source, temporary.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024**2)
            os.replace(temporary, target)
            if number % 1000 == 0:
                print(f"Extracted {number}/{len(members)} images", flush=True)
    return len(members)


def canonical_metadata(raw_directory: Path, output: Path) -> int:
    """Join official one-hot diagnosis labels to official lesion group IDs."""
    with zipfile.ZipFile(raw_directory / TRUTH) as archive:
        members = [item for item in validate_members(archive) if PurePosixPath(item.filename).name == TRUTH.replace(".zip", ".csv")]
        if len(members) != 1:
            raise ValueError("Expected exactly one ground-truth CSV")
        labels = list(csv.DictReader(io.StringIO(archive.read(members[0]).decode("utf-8-sig"))))
    with (raw_directory / GROUPS).open(encoding="utf-8-sig", newline="") as handle:
        groups = list(csv.DictReader(handle))
    grouping = {}
    for row in groups:
        image_id = row.get("image", "").strip()
        lesion = row.get("lesion_id", "").strip()
        if not image_id or not lesion or image_id in grouping:
            raise ValueError("Missing or repeated image/lesion identifier in group metadata")
        grouping[image_id] = row
    rows = []
    seen = set()
    for row in labels:
        image_id = row.get("image", "").strip()
        scores = [float(row[code.upper()]) for code in CLASSES]
        if any(score not in (0, 1) for score in scores) or sum(scores) != 1:
            raise ValueError(f"Invalid one-hot diagnosis for {image_id}")
        if image_id not in grouping or image_id in seen:
            raise ValueError("Labels/group IDs do not join one-to-one")
        seen.add(image_id)
        group = grouping[image_id]
        rows.append({"image_id": image_id, "lesion_id": group["lesion_id"].strip(), "dx": CLASSES[scores.index(1)], "dx_type": group.get("diagnosis_confirm_type", "").strip()})
    if seen != set(grouping):
        raise ValueError("Label and group image sets differ")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image_id", "lesion_id", "dx", "dx_type"])
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: row["image_id"]))
    os.replace(temporary, output)
    return len(rows)


def main() -> int:
    global BASE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--metadata-only", action="store_true", help="Fetch and join labels/groups without downloading images")
    parser.add_argument("--extract", action="store_true", help="Extract after downloading; existing verified images are retained")
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 9), help="Image download connections, default 4; small metadata downloads stay serial")
    parser.add_argument("--regional-endpoint", action="store_true", help="Use the same public S3 bucket's us-east-1 endpoint; entity identity is still checked")
    parser.add_argument("--probe", action="store_true", help="Measure a 1 MiB source range and report source identity without downloading the cohort")
    args = parser.parse_args()
    if args.regional_endpoint:
        BASE = REGIONAL_BASE
    directory = args.data_dir.resolve()
    receipts = []
    try:
        if args.probe:
            start = perf_counter()
            request = urllib.request.Request(BASE + INPUT, headers={"Range": "bytes=0-1048575"})
            with urllib.request.urlopen(request, timeout=15) as response:
                if response.status != 206 or response.headers.get("Content-Range") != "bytes 0-1048575/2771732744":
                    raise ValueError("Probe did not receive the expected official archive range")
                chunks = []
                while chunk := response.read(16 * 1024):
                    chunks.append(chunk)
                    if perf_counter() - start > 30:
                        raise TimeoutError("Source probe exceeded 30 seconds; existing dataset files are untouched")
                data = b"".join(chunks)
                etag = response.headers.get("ETag")
            seconds = perf_counter() - start
            if len(data) != 1024**2:
                raise ValueError("Incomplete source probe")
            print(json.dumps({"url": BASE + INPUT, "etag": etag, "bytes": len(data), "seconds": round(seconds, 3), "MiB_per_second": round(1 / max(seconds, 0.001), 3)}), flush=True)
            return 0
        for filename in (TRUTH, GROUPS) + (() if args.metadata_only else (INPUT,)):
            for attempt in range(3):
                try:
                    target = directory / "raw" / filename
                    receipts.append(download_parallel(filename, target, workers=args.workers) if filename == INPUT and args.workers > 1 else download(filename, target))
                    break
                except urllib.error.HTTPError as error:
                    if error.code < 500 or attempt == 2:
                        raise
                    time.sleep(2)
                except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                    if attempt == 2:
                        raise
                    print(f"Connection interrupted; retrying from saved partial: {error}", flush=True)
                    time.sleep(2)
        count = canonical_metadata(directory / "raw", directory / "metadata.csv")
        save_json(directory / "provenance.json", {"distribution": "Official ISIC 2018 Task 3 Training (HAM10000)", "source_page": "https://challenge.isic-archive.com/data/#2018", "license_url": LICENSE, "intended_use": "Academic noncommercial research", "metadata_derivation": "One-to-one join of original one-hot labels and lesion group CSV; no demographics inferred", "metadata_rows": count, "metadata_sha256": sha256_file(directory / "metadata.csv"), "files": receipts})
        print(f"Saved canonical metadata: {count} rows", flush=True)
        if args.extract and not args.metadata_only:
            print(f"Verified/extracted {extract_images(directory / 'raw' / INPUT, directory / 'images')} images", flush=True)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f"Acquisition failed: {error}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
