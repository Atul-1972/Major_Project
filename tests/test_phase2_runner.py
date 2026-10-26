import json

import pytest

from ai_model.data.pipeline import verify_loaders
from scripts.run_phase2 import collect_results, write_completion


def completion_fixture(data):
    root = data["root"] / "runner-project"
    spec = root / "ai_model/config/dataset_spec.json"
    spec.parent.mkdir(parents=True)
    spec.write_bytes(data["spec"].read_bytes())
    import shutil

    verify_loaders(data["root"], data["splits"], data["output"] / "loader_verification.json", batch_size=2)
    shutil.copytree(data["output"], root / "data/ham10000/processed")
    return root


def test_runner_only_generates_completion_from_passed_audit_and_real_batches(prepared_dataset):
    root = completion_fixture(prepared_dataset)
    (root / "README.md").write_text(
        "Phase 2 was resumed at the user's request on 2026-10-25. Its implementation and 34 previously passing tests are saved; the official image download is partially saved and resumable. Full image audit, frozen splits, and actual-cohort loader verification are pending. Inspect `.project/phase2_run.local.json` and `reports/local/phase2-run.log` for live runner status before restarting `python scripts/run_phase2.py` from the project venv. No model training has started.",
        encoding="utf-8",
    )
    (root / "docs").mkdir()
    (root / "docs/APPROVALS.md").write_text(
        '| Phase 2 | Approved 2026-10-25; resumed 2026-10-25 | "start phase 2", "Pause now", "resume Phase 2" |',
        encoding="utf-8",
    )
    summary = write_completion(root)
    assert summary["audited_images"] == 12  # Explicit synthetic fixture, never the project cohort.
    assert summary["training_performed"] is False
    assert summary["status"] == "locally_verified_awaiting_phase3_approval"
    report = (root / "docs/phase-reports/phase-2.md").read_text(encoding="utf-8")
    assert "Do not start it automatically" in report
    assert "Phase 2 is complete and locally verified" in (root / "README.md").read_text(encoding="utf-8")
    approvals = (root / "docs/APPROVALS.md").read_text(encoding="utf-8")
    assert "complete and locally verified" in approvals
    assert '"resume Phase 2"' in approvals


def test_runner_rejects_incomplete_or_failed_image_audit(prepared_dataset):
    root = completion_fixture(prepared_dataset)
    path = root / "data/ham10000/processed/audit.json"
    audit = json.loads(path.read_text())
    audit["passed"] = False
    audit["errors"] = [{"code": "missing_image"}]
    path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match="cannot be closed"):
        collect_results(root)
    assert not (root / "reports/phase2-data-summary.json").exists()


def test_runner_rejects_an_audited_review_missing_from_the_frozen_bundle(prepared_dataset):
    root = completion_fixture(prepared_dataset)
    path = root / "data/ham10000/processed/audit.json"
    audit = json.loads(path.read_text())
    audit["duplicate_review"] = {"sha256": "0" * 64, "accepted_pairs": 1}
    path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match="review differs from the frozen"):
        collect_results(root)
    assert not (root / "reports/phase2-data-summary.json").exists()


def test_duplicate_runner_does_not_overwrite_active_status(tmp_path, monkeypatch):
    import sys
    from scripts import run_phase2

    state = tmp_path / ".project/phase2_run.local.json"
    state.parent.mkdir()
    state.write_text('{"status":"running","pid":123}')
    monkeypatch.setattr(run_phase2, "ROOT", tmp_path)
    monkeypatch.setattr(run_phase2, "STATE", state)
    monkeypatch.setattr(sys, "argv", ["run_phase2"])
    with run_phase2.runner_lock():
        assert run_phase2.main() == 1
    assert json.loads(state.read_text()) == {"status": "running", "pid": 123}


@pytest.mark.parametrize("failures", [2, 10])
def test_status_replace_retries_file_locks_and_preserves_previous_state(tmp_path, monkeypatch, failures):
    from pathlib import Path
    from scripts import run_phase2

    state = tmp_path / "status.json"
    previous = {"status": "running", "archive_bytes_saved": 100}
    updated = {"status": "running", "archive_bytes_saved": 200}
    state.write_text(json.dumps(previous), encoding="utf-8")
    original_replace = Path.replace
    attempts = []
    delays = []

    def locked_replace(source, target):
        attempts.append(target)
        assert json.loads(state.read_text(encoding="utf-8")) == previous
        if len(attempts) <= failures:
            raise PermissionError("Status file temporarily held by a Windows reader")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", locked_replace)
    monkeypatch.setattr(run_phase2.time, "sleep", delays.append)
    if failures == 10:
        with pytest.raises(PermissionError):
            run_phase2.save_json(state, updated)
        assert json.loads(state.read_text(encoding="utf-8")) == previous
        assert json.loads(state.with_suffix(".json.tmp").read_text(encoding="utf-8")) == updated
    else:
        run_phase2.save_json(state, updated)
        assert json.loads(state.read_text(encoding="utf-8")) == updated
    assert len(attempts) == min(failures + 1, 10)
    assert len(delays) == len(attempts) - 1
