"""Finish the approved data phase in a resumable local process; never train models."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".project" / "phase2_run.local.json"
LOG = ROOT / "reports" / "local" / "phase2-run.log"
ARCHIVE_BYTES = 2_771_732_744


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


@contextmanager
def runner_lock():
    lock = ROOT / ".project" / "phase2_runner.local.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def checkpoint(summary, next_action, status="in_progress"):
    subprocess.run([sys.executable, str(ROOT / "scripts/checkpoint.py"), "--phase", "phase_2", "--status", status, "--summary", summary, "--next", next_action], cwd=ROOT, check=True)


def run_stage(stage, arguments, state):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as log:
        log.write(f"\n=== {datetime.now(timezone.utc).isoformat()} {stage} ===\n")
        log.flush()
        process = subprocess.Popen(arguments, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        try:
            while True:
                code = process.poll()
                raw = ROOT / "data/ham10000/raw"
                final = raw / "ISIC2018_Task3_Training_Input.zip"
                partial = final.with_name(final.name + ".part")
                current = final if final.exists() else partial
                size = current.stat().st_size if current.exists() else 0
                state.update({"stage": stage, "updated_at_utc": datetime.now(timezone.utc).isoformat(), "child_pid": process.pid, "archive_bytes_saved": size, "archive_bytes_total": ARCHIVE_BYTES, "archive_percent": round(size / ARCHIVE_BYTES * 100, 2), "status": "running" if code is None else ("stage_passed" if code == 0 else "needs_attention")})
                save_json(STATE, state)
                if code is not None:
                    if code != 0:
                        raise RuntimeError(f"Stage '{stage}' exited {code}; inspect {LOG}")
                    return
                time.sleep(5)
        except BaseException:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=15)
            raise


def collect_results(root=ROOT):
    """Fail closed: only actual passed cohort, integrity, and loader reports qualify."""
    processed = root / "data/ham10000/processed"
    audit = json.loads((processed / "audit.json").read_text(encoding="utf-8"))
    summary = json.loads((processed / "splits/split_summary.json").read_text(encoding="utf-8"))
    batch = json.loads((processed / "loader_verification.json").read_text(encoding="utf-8"))
    spec = json.loads((root / "ai_model/config/dataset_spec.json").read_text(encoding="utf-8"))
    expected = spec["expected_images"]
    classes = {item["code"] for item in spec["classes"]}
    if not audit["passed"] or audit["errors"] or audit["audited_images"] != expected or summary["images"] != expected:
        raise ValueError("Full actual image audit has not passed; Phase 2 cannot be closed")
    if audit["class_counts"] != {item["code"]: item["expected_images"] for item in spec["classes"]}:
        raise ValueError("Actual cohort class counts differ from the source specification")
    manifest_dir = processed / "splits"
    manifest = json.loads((manifest_dir / "manifest_set.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files_sha256"].items():
        if Path(name).name != name or hashlib.sha256((manifest_dir / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Manifest integrity failure at phase completion")
    if not batch["passed"] or batch["training_performed"]:
        raise ValueError("No valid data-only loader verification")
    for split in ("train", "val", "test"):
        result = batch["batches"][split]
        if not result["finite"] or not result["deterministic_evaluation"] or result["dataset_images"] != summary["split_counts"][split] or set(summary["class_counts"][split]) != classes:
            raise ValueError(f"Missing real {split} verification/class coverage")
    if any(value not in (0, None) for value in summary["leakage_checks"].values()):
        raise ValueError("Reported cross-split leakage")
    return audit, summary, batch, manifest


def write_completion(root=ROOT):
    audit, summary, batch, manifest = collect_results(root)
    aggregate = {
        "phase": 2, "status": "locally_verified_awaiting_phase3_approval",
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "audited_images": audit["audited_images"], "class_counts": audit["class_counts"],
        "unique_source_lesions": audit["unique_lesions"], "connected_groups": audit["connected_groups"],
        "exact_duplicate_groups": audit["exact_duplicate_groups"], "near_duplicate_pairs": len(audit["near_duplicate_pairs"]),
        "image_modes": audit["image_modes"], "dimensions": audit["dimensions"],
        "split_counts": summary["split_counts"], "split_class_counts": summary["class_counts"],
        "split_group_counts": summary["group_counts"], "leakage_checks": summary["leakage_checks"],
        "manifest_fingerprint": manifest["input_fingerprint"], "manifest_files_sha256": manifest["files_sha256"],
        "loader_batches": batch["batches"], "packages": batch["packages"],
        "limitations": audit["warnings"], "training_performed": False,
    }
    save_json(root / "reports/phase2-data-summary.json", aggregate)
    phase_date = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d")
    lines = ["# Phase 2 report", "", f"Date: {phase_date} (Asia/Calcutta).", "", "Status: complete and locally verified. Awaiting explicit Phase 3 approval; no training has started.", "", "## Delivered", "", "Official ISIC acquisition/provenance, canonical metadata, actual image audit, duplicate-aware grouped splits, immutable mapping/preprocessing/manifests, PyTorch loaders, tests, Windows instructions and a statically checked Colab notebook. See `../PHASE_2.md` and `../../reports/phase2-data-summary.json` for reproducible commands and aggregate evidence.", "", "## Actual cohort audit", "", f"Audited images: {audit['audited_images']}. Original lesion IDs: {audit['unique_lesions']}. Connected groups after duplicate handling: {audit['connected_groups']}. Exact pixel-duplicate groups: {audit['exact_duplicate_groups']}. Conservative near-duplicate pairs: {len(audit['near_duplicate_pairs'])}.", "", "| Class | Source images | Train | Validation | Test |", "| --- | ---: | ---: | ---: | ---: |"]
    for code in audit["class_counts"]:
        lines.append(f"| {code} | {audit['class_counts'][code]} | {summary['class_counts']['train'].get(code, 0)} | {summary['class_counts']['val'].get(code, 0)} | {summary['class_counts']['test'].get(code, 0)} |")
    lines.extend(["", f"Split totals: {json.dumps(summary['split_counts'])}. All classes are present in each split. Zero prohibited image, connected-group, lesion, or exact-pixel overlap; patient-level overlap is unknown when source IDs are unavailable.", "", f"Manifest fingerprint: `{manifest['input_fingerprint']}`.", "", "## Verification", "", "The completion runner requires successful acquisition/extraction, `pip check`, the full pytest suite, and actual-data `pipeline prepare` before generating this report. Detailed command output is in ignored `reports/local/phase2-run.log`. Each split produced a real finite float32 image batch and int64 labels, with deterministic evaluation transforms. The full saved audit and manifest files are under ignored `data/ham10000/processed/`.", "", "## Limitations", ""])
    lines.extend(f"- {warning}" for warning in audit["warnings"])
    lines.extend(["- Harvard API access returned HTTP 403; the official ISIC alternate source and CC BY-NC 4.0 attribution are documented in `../DATASET_SOURCE.md`.", "- Demographics absent from this distribution are not inferred. No clinical, smartphone-photo, calibration, or model-accuracy results exist.", "- Colab cells were statically checked, not executed remotely by the agent. Local tests use clearly labeled synthetic fixtures only; actual-data verification is recorded separately above.", "- No training, API, dashboard, mobile implementation, or deployment was run.", "", "## Next phase", "", "Request explicit approval for Phase 3: EfficientNetV2-S baseline setup, Colab GPU smoke test, resumable training, validation selection, evaluation and error analysis. Do not start it automatically.", ""])
    report = root / "docs/phase-reports/phase-2.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")
    replacements = {
        "README.md": [("Phase 1 is complete. Phase 2 is authorized and in progress: dataset acquisition, audit, grouped splits, preprocessing, and loader verification. Model training, backend implementation, and the dashboard have not started.", "Phase 2 is complete and locally verified. Review the Phase 2 report; explicit Phase 3 approval is required before training. Backend, dashboard and mobile work have not started.")],
        "docs/APPROVALS.md": [("Approved 2026-10-25; in progress | User instruction: \"start phase 2\"", "Approved 2026-10-25; complete and locally verified | User instruction: \"start phase 2\"")],
        "docs/CHECKLIST.md": [("- [ ] Finish the actual image download/extraction and audit every source image.", "- [x] Finish the actual image download/extraction and audit every source image."), ("- [ ] Verify class coverage, actual zero-overlap splits, and real train/val/test batches.", "- [x] Verify class coverage, actual zero-overlap splits, and real train/val/test batches."), ("- [ ] Record actual aggregate results and finalize Phase 2 report/checkpoint.", "- [x] Record actual aggregate results and finalize Phase 2 report/checkpoint."), ("- [ ] Phase 2: acquire/audit HAM10000, grouped splits, preprocessing and a verified loader batch.", "- [x] Phase 2: acquire/audit HAM10000, grouped splits, preprocessing and a verified loader batch.")],
    }
    for name, changes in replacements.items():
        path = root / name
        if path.exists():
            text = path.read_text(encoding="utf-8")
            for before, after in changes:
                text = text.replace(before, after)
            path.write_text(text, encoding="utf-8")
    readme = root / "README.md"
    if readme.exists():
        before = "Phase 2 is paused at the user's request. Its implementation and 34 passing tests are saved; the official image download is partially saved and resumable. Full image audit, frozen splits, and actual-cohort loader verification are pending. Run `python scripts/run_phase2.py` from the project venv to resume the approved data phase. No model training has started."
        readme.write_text(readme.read_text(encoding="utf-8").replace(before, "Phase 2 is complete and locally verified. Review the Phase 2 report; explicit Phase 3 approval is required before training. Backend, dashboard and mobile work have not started."), encoding="utf-8")
    approvals = root / "docs/APPROVALS.md"
    if approvals.exists():
        approvals.write_text(approvals.read_text(encoding="utf-8").replace("Approved 2026-10-25; paused at user's request |", "Approved 2026-10-25; complete and locally verified |"), encoding="utf-8")
    return aggregate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=1, choices=range(1, 9))
    args = parser.parse_args()
    state = {"phase": 2, "pid": os.getpid(), "started_at_utc": datetime.now(timezone.utc).isoformat(), "log": "reports/local/phase2-run.log", "training_authorized": False}
    owns_lock = False
    try:
        with runner_lock():
            owns_lock = True
            checkpoint("Started resumable Phase 2 completion runner. It will acquire original data, run dependency/tests checks, and verify actual grouped splits and loader batches; it never starts training.", "Monitor .project/phase2_run.local.json and reports/local/phase2-run.log. On success review the generated Phase 2 report; on failure diagnose and resume this runner.")
            run_stage("downloading_and_extracting", [sys.executable, "-u", "-m", "ai_model.data.acquire", "--extract", "--workers", str(args.workers)], state)
            run_stage("checking_dependencies", [sys.executable, "-m", "pip", "check"], state)
            run_stage("testing", [sys.executable, "-m", "pytest", "-q"], state)
            run_stage("auditing_splitting_and_verifying", [sys.executable, "-u", "-m", "ai_model.data.pipeline", "prepare"], state)
            result = write_completion()
            checkpoint(f"Phase 2 completed by the authorized runner: audited {result['audited_images']} actual images, froze leakage-checked manifests, verified all three real loader batches, and wrote the aggregate summary/report. No training performed.", "Review docs/phase-reports/phase-2.md and reports/phase2-data-summary.json. Obtain explicit Phase 3 approval before training the CNN baseline.", status="awaiting_approval")
            state.update({"status": "complete", "child_pid": None, "stage": "awaiting_phase3_approval", "updated_at_utc": datetime.now(timezone.utc).isoformat(), "report": "docs/phase-reports/phase-2.md"})
            save_json(STATE, state)
            print("Phase 2 complete; review the saved report. Training is not started.", flush=True)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        if owns_lock:
            state.update({"status": "needs_attention", "child_pid": None, "error": str(error), "updated_at_utc": datetime.now(timezone.utc).isoformat()})
            save_json(STATE, state)
            try:
                checkpoint(f"Phase 2 runner stopped at {state.get('stage')}: {error}. Saved files and download prefix are retained; Phase 2 is not complete.", "Inspect .project/phase2_run.local.json and reports/local/phase2-run.log; resolve the failure and rerun scripts/run_phase2.py. Do not start training.")
            except subprocess.SubprocessError:
                pass
        else:
            print("Could not acquire the runner lock; an existing runner's status was not changed.", file=sys.stderr)
        print(f"Phase 2 stopped; saved work retained: {error}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
