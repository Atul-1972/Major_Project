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
    summary = write_completion(root)
    assert summary["audited_images"] == 12  # Explicit synthetic fixture, never the project cohort.
    assert summary["training_performed"] is False
    assert summary["status"] == "locally_verified_awaiting_phase3_approval"
    report = (root / "docs/phase-reports/phase-2.md").read_text(encoding="utf-8")
    assert "Do not start it automatically" in report


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
