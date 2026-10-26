"""Explicitly synthetic software tests; no research accuracy evidence."""

import copy
import json
import random
from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn

from ai_model.models.cnn import build_cnn, set_training_stage
from ai_model.training.engine import load_checkpoint, train_run, training_class_weights, scaled_optimizer_step
from ai_model.training.metrics import classification_metrics
from ai_model.training.evaluation import evaluate_run
from ai_model.training.reproducibility import capture_rng, load_config, restore_rng, seed_all
from ai_model.training.storage import atomic_save, run_lock


@pytest.fixture(autouse=True, scope="module")
def limit_threads():
    previous = torch.get_num_threads()
    torch.set_num_threads(2)
    yield
    torch.set_num_threads(previous)


class SyntheticTinyCNN(nn.Module):
    def __init__(self, classes):
        super().__init__()
        self.features = nn.Sequential(nn.Conv2d(3, 4, 3, padding=1), nn.BatchNorm2d(4), nn.ReLU(), nn.AdaptiveAvgPool2d(1), nn.Flatten())
        self.classifier = nn.Sequential(nn.Dropout(0.2), nn.Linear(4, classes))

    def forward(self, images):
        return self.classifier(self.features(images))


def synthetic_factory(classes, _initialize):
    return SyntheticTinyCNN(classes), {"weights_enum": None, "purpose": "SYNTHETIC_FIXTURE_ONLY"}


@pytest.fixture
def training_config():
    root = Path(__file__).resolve().parents[1]
    config = load_config(root / "ai_model/config/e1.json")
    config.update(batch_size=2, warmup_epochs=1, finetune_epochs=2, patience=5, amp=False)
    return config


def test_metrics_match_hand_computed_one_vs_rest_counts_and_undefined_values():
    metrics = classification_metrics([0, 0, 1, 1], [[0.9, 0.1], [0.7, 0.3], [0.8, 0.2], [0.2, 0.8]], ["a", "b"])
    assert metrics["confusion_matrix"] == [[2, 0], [1, 1]]
    assert metrics["accuracy"] == 0.75
    assert metrics["per_class"]["a"]["precision"] == pytest.approx(2 / 3)
    assert metrics["per_class"]["a"]["specificity"] == 0.5
    assert metrics["macro_f1"] == pytest.approx((0.8 + 2 / 3) / 2)
    assert metrics["per_class"]["a"]["roc_auc"] == 0.75
    missing = classification_metrics([0, 0], [[0.9, 0.1], [0.7, 0.3]], ["a", "b"])
    assert missing["per_class"]["b"]["sensitivity"] is None
    assert missing["per_class"]["b"]["precision"] is None
    assert missing["per_class"]["b"]["roc_auc"] is None
    assert missing["per_class"]["b"]["roc_auc_unavailable_reason"]
    with pytest.raises(ValueError, match="normalized"):
        classification_metrics([0], [[0.8, 0.8]], ["a", "b"])


def test_class_weights_use_only_training_records():
    records = [{"class_index": "0"}] * 3 + [{"class_index": "1"}]
    assert torch.allclose(training_class_weights(records, ["a", "b"]), torch.tensor([2 / 3, 2.0]))


def test_rng_state_roundtrips_through_weights_only_checkpoint(tmp_path):
    seed_all(123)
    path = tmp_path / "rng.pt"
    atomic_save(path, capture_rng(), tensor=True)
    expected = (random.random(), np.random.rand(), torch.rand(4))
    restore_rng(load_checkpoint(path))
    actual = (random.random(), np.random.rand(), torch.rand(4))
    assert expected[:2] == actual[:2]
    assert torch.equal(expected[2], actual[2])


def test_epoch_resume_matches_uninterrupted_weights_optimizer_and_selection(prepared_dataset, training_config):
    data = prepared_dataset
    kwargs = {"_model_factory": synthetic_factory}
    complete_dir = data["root"] / "uninterrupted"
    resumed_dir = data["root"] / "resumed"
    full = train_run(data["root"], data["splits"], training_config, complete_dir, torch.device("cpu"), **kwargs)
    partial = train_run(data["root"], data["splits"], training_config, resumed_dir, torch.device("cpu"), epochs_this_session=1, **kwargs)
    assert partial["status"] == "paused" and partial["next_epoch"] == 1
    resumed = train_run(data["root"], data["splits"], training_config, resumed_dir, torch.device("cpu"), resume=True, **kwargs)
    assert full["status"] == resumed["status"] == "completed"
    assert full["best_epoch"] == resumed["best_epoch"]
    assert full["best_score"] == resumed["best_score"]
    assert full["global_step"] == resumed["global_step"]
    for key in full["model"]:
        assert torch.equal(full["model"][key], resumed["model"][key]), key
    for index, state in full["optimizer"]["state"].items():
        for key, value in state.items():
            assert torch.equal(value, resumed["optimizer"]["state"][index][key])
    assert full["scheduler"] == resumed["scheduler"]
    assert resumed["history"][0]["stage"] == "head_warmup"
    assert resumed["history"][1]["stage"] == "full_finetuning"
    assert resumed["history"][0]["trainable_parameters"] < resumed["history"][1]["trainable_parameters"]
    best = load_checkpoint(resumed_dir / "best.pt")
    assert best["selected_epoch"] == resumed["best_epoch"]


def test_resume_rejects_config_changes_and_duplicate_training(prepared_dataset, training_config):
    data = prepared_dataset
    run = data["root"] / "protected"
    train_run(data["root"], data["splits"], training_config, run, torch.device("cpu"), epochs_this_session=1, _model_factory=synthetic_factory)
    changed = {**training_config, "seed": 77}
    with pytest.raises(ValueError, match="Resume rejected"):
        train_run(data["root"], data["splits"], changed, run, torch.device("cpu"), resume=True, _model_factory=synthetic_factory)
    with pytest.raises(ValueError, match="already exists"):
        train_run(data["root"], data["splits"], training_config, run, torch.device("cpu"), _model_factory=synthetic_factory)
    with run_lock(run):
        with pytest.raises(OSError):
            train_run(data["root"], data["splits"], training_config, run, torch.device("cpu"), resume=True, _model_factory=synthetic_factory)


def test_pause_before_first_epoch_has_recoverable_initial_state(prepared_dataset, training_config):
    data = prepared_dataset
    run = data["root"] / "initial_pause"
    run.mkdir()
    (run / "PAUSE").write_text("pause")
    state = train_run(data["root"], data["splits"], training_config, run, torch.device("cpu"), _model_factory=synthetic_factory)
    assert state["status"] == "paused" and load_checkpoint(run / "last.pt")["next_epoch"] == 0
    (run / "PAUSE").unlink()
    state = train_run(data["root"], data["splits"], training_config, run, torch.device("cpu"), resume=True, _model_factory=synthetic_factory)
    assert state["status"] == "completed"


def test_warmup_preserves_backbone_buffers_and_finetuning_unfreezes_them():
    model = SyntheticTinyCNN(2)
    before = copy.deepcopy(model.features.state_dict())
    set_training_stage(model, warmup=True)
    model(torch.rand(2, 3, 32, 32)).sum().backward()
    assert all(torch.equal(before[key], value) for key, value in model.features.state_dict().items())
    assert all(p.grad is None for p in model.features.parameters())
    set_training_stage(model, warmup=False)
    model(torch.rand(2, 3, 32, 32)).sum().backward()
    assert any(p.grad is not None for p in model.features.parameters())


def test_actual_efficientnet_architecture_has_seven_logits_without_network():
    model, initialization = build_cnn(pretrained=False)
    model.eval()
    with torch.inference_mode():
        logits = model(torch.rand(2, 3, 64, 64))
    assert logits.shape == (2, 7) and torch.isfinite(logits).all()
    assert initialization["weights_enum"] is None


def test_interrupted_epoch_repeats_from_prior_committed_state(prepared_dataset, training_config):
    data = prepared_dataset

    class InterruptedCNN(SyntheticTinyCNN):
        def __init__(self, classes):
            super().__init__(classes)
            self.calls = 0

        def forward(self, images):
            self.calls += 1
            if self.training and self.calls == 7:
                raise KeyboardInterrupt("Synthetic interruption after the first fine-tuning batch")
            return super().forward(images)

    def interrupted_factory(classes, _initialize):
        return InterruptedCNN(classes), {"purpose": "SYNTHETIC_FIXTURE_ONLY"}

    run = data["root"] / "interrupted"
    with pytest.raises(KeyboardInterrupt):
        train_run(data["root"], data["splits"], training_config, run, torch.device("cpu"), _model_factory=interrupted_factory)
    assert load_checkpoint(run / "last.pt")["next_epoch"] == 1
    actual = train_run(data["root"], data["splits"], training_config, run, torch.device("cpu"), resume=True, _model_factory=synthetic_factory)
    expected = train_run(data["root"], data["splits"], training_config, data["root"] / "reference", torch.device("cpu"), _model_factory=synthetic_factory)
    assert actual["global_step"] == expected["global_step"]
    assert all(torch.equal(value, actual["model"][key]) for key, value in expected["model"].items())


def test_early_stopping_uses_validation_and_training_never_opens_test(prepared_dataset, training_config, monkeypatch):
    from ai_model.training import engine
    data = prepared_dataset
    accessed = []
    real_loader = engine.make_loader

    def loader(*args):
        accessed.append(args[2])
        assert args[2] != "test"
        return real_loader(*args)

    monkeypatch.setattr(engine, "make_loader", loader)
    monkeypatch.setattr(engine, "predict_loader", lambda *_: ({"macro_f1": 0.25, "accuracy": 0.5, "loss": 0.7}, {}))
    config = {**training_config, "patience": 1}
    result = train_run(data["root"], data["splits"], config, data["root"] / "early_stop", torch.device("cpu"), _model_factory=synthetic_factory)
    assert result["status"] == "early_stopped" and result["next_epoch"] == 2
    assert result["best_epoch"] == 0
    assert set(accessed) == {"train", "val"}


def test_final_test_gate_reports_and_same_selection_retry(prepared_dataset, training_config, monkeypatch):
    from ai_model.training import evaluation
    data = prepared_dataset
    run = data["root"] / "evaluated_fixture"
    args = (data["root"], data["splits"], training_config, run, torch.device("cpu"))
    train_run(*args, epochs_this_session=1, _model_factory=synthetic_factory)
    with pytest.raises(ValueError, match="confirm-final-test"):
        evaluate_run(*args, _model_factory=synthetic_factory)
    with pytest.raises(ValueError, match="Training must finish"):
        evaluate_run(*args, confirm_final_test=True, _model_factory=synthetic_factory)
    assert not (run / "evaluation/test_selection.json").exists()
    train_run(*args, resume=True, _model_factory=synthetic_factory)
    report = evaluate_run(*args, confirm_final_test=True, _model_factory=synthetic_factory)
    assert report["experiment"] == "SYNTHETIC_TEST_ONLY"
    assert report["test_metrics"]["images"] == data["summary"]["split_counts"]["test"]
    assert (run / "evaluation/confusion_matrix.png").is_file()
    assert (run / "evaluation/roc_curves.png").is_file()
    assert (run / "evaluation/training_curves.png").is_file()
    monkeypatch.setattr(evaluation, "predict_loader", lambda *_: pytest.fail("Completed evaluation must reuse its report"))
    assert evaluate_run(*args, confirm_final_test=True, _model_factory=synthetic_factory) == report


def test_failed_atomic_write_keeps_the_previous_checkpoint(tmp_path, monkeypatch):
    from ai_model.training import storage
    path = tmp_path / "checkpoint.pt"
    atomic_save(path, {"epoch": 1}, tensor=True)
    monkeypatch.setattr(storage, "replace_with_retry", lambda *_: (_ for _ in ()).throw(PermissionError("Synthetic blocked replacement")))
    with pytest.raises(PermissionError):
        atomic_save(path, {"epoch": 2}, tensor=True)
    assert load_checkpoint(path) == {"epoch": 1}


def test_scaler_backoff_does_not_count_a_skipped_optimizer_update():
    class SyntheticScaler:
        def __init__(self):
            self.value = 8

        def is_enabled(self):
            return True

        def scale(self, loss):
            return loss

        def unscale_(self, _optimizer):
            pass

        def get_scale(self):
            return self.value

        def step(self, optimizer):
            if self.value == 4:
                optimizer.step()

        def update(self):
            self.value = 4

    model = nn.Linear(2, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    scaler = SyntheticScaler()
    before = model.weight.detach().clone()
    assert not scaled_optimizer_step(model(torch.ones(1, 2)).sum(), model, optimizer, scaler, 1.0)
    assert torch.equal(model.weight, before)
    optimizer.zero_grad(set_to_none=True)
    assert scaled_optimizer_step(model(torch.ones(1, 2)).sum(), model, optimizer, scaler, 1.0)
    assert not torch.equal(model.weight, before)
