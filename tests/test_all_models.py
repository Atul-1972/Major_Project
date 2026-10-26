"""Architecture and recovery checks; synthetic fixtures are not research results."""

import copy
from pathlib import Path

import pytest
import torch
from torch import nn

from ai_model.models.cnn import set_training_stage
from ai_model.models.registry import ARCHITECTURES, build_model
from ai_model.training.engine import train_run
from ai_model.training.reproducibility import load_config


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True, scope='module')
def few_threads():
    previous = torch.get_num_threads()
    torch.set_num_threads(2)
    yield
    torch.set_num_threads(previous)


@pytest.mark.parametrize('experiment', ('E2', 'E3', 'E4'))
def test_actual_models_warmup_backbone_freeze_and_finetune_gradients(experiment):
    config = load_config(ROOT / f'ai_model/config/{experiment.lower()}.json')
    model, initialization = build_model(config, 3, pretrained=False)
    assert initialization['sha256'] is None
    images = torch.rand(2, 3, 64, 64)
    set_training_stage(model, warmup=True)
    assert not model.features.training
    buffers = {name: value.clone() for name, value in model.features.named_buffers()}
    logits = model(images)
    assert logits.shape == (2, 3) and torch.isfinite(logits).all()
    logits.square().sum().backward()
    assert all(p.grad is None for p in model.features.parameters())
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in model.classifier.parameters())
    assert all(torch.equal(buffers[name], value) for name, value in model.features.named_buffers())
    model.zero_grad(set_to_none=True)
    set_training_stage(model, warmup=False)
    model(images).square().sum().backward()
    if experiment in ('E3', 'E4'):
        assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in model.features.cnn.parameters())
        assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in model.features.transformer.parameters())
    else:
        assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in model.features.parameters())
    assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
    model.eval()
    with torch.inference_mode():
        expected = model(images)
    state = copy.deepcopy(model.state_dict())
    model.load_state_dict(state)
    with torch.inference_mode():
        assert torch.equal(model(images), expected)


class TinyFixture(nn.Module):
    def __init__(self, classes):
        super().__init__()
        self.features = nn.Sequential(nn.Conv2d(3, 2, 1), nn.BatchNorm2d(2), nn.AdaptiveAvgPool2d(1), nn.Flatten())
        self.classifier = nn.Sequential(nn.Dropout(0.2), nn.Linear(2, classes))

    def forward(self, images):
        return self.classifier(self.features(images))


def fixture_model(classes, _pretrained):
    return TinyFixture(classes), {'purpose': 'SYNTHETIC_FIXTURE_ONLY'}


@pytest.mark.parametrize('experiment', ('E2', 'E3', 'E4'))
def test_extended_configs_recover_exact_epoch_state(prepared_dataset, experiment):
    config = load_config(ROOT / f'ai_model/config/{experiment.lower()}.json')
    config.update(batch_size=2, warmup_epochs=1, finetune_epochs=1, amp=False)
    data = prepared_dataset
    args = (data['root'], data['splits'], config)
    original = train_run(*args, data['root'] / 'full', torch.device('cpu'), _model_factory=fixture_model)
    partial = train_run(*args, data['root'] / 'resumed', torch.device('cpu'), epochs_this_session=1, _model_factory=fixture_model)
    assert partial['status'] == 'paused'
    restored = train_run(*args, data['root'] / 'resumed', torch.device('cpu'), resume=True, _model_factory=fixture_model)
    assert restored['status'] == 'completed'
    assert restored['best_score'] == original['best_score']
    assert restored['best_epoch'] == original['best_epoch']
    assert all(torch.equal(value, restored['model'][name]) for name, value in original['model'].items())


def test_registry_rejects_mismatched_architecture():
    config = load_config(ROOT / 'ai_model/config/e4.json')
    config['architecture'] = ARCHITECTURES['E1']
    with pytest.raises(ValueError, match='do not match'):
        build_model(config, pretrained=False)
