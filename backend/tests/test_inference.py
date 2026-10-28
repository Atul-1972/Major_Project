"""Export adapter checks with explicitly synthetic tensors, not research evidence."""

import hashlib
import json

from PIL import Image
import pytest
import torch
from torch import nn

from backend.app import inference
from ai_model.training.suite import select_candidates


class SyntheticAdapterModel(nn.Module):
    """Small deterministic fixture to verify tensor loading/preprocessing/scoring."""
    def __init__(self):
        super().__init__()
        self.bias = nn.Parameter(torch.arange(7, dtype=torch.float32))

    def forward(self, images):
        return images.mean(dim=(1, 2, 3)).unsqueeze(1) + self.bias.unsqueeze(0)


@pytest.fixture
def synthetic_bundle(tmp_path, monkeypatch):
    # Its metadata imitates an export solely to exercise adapter checks in isolation.
    # The production constructors are replaced explicitly and no fixture is shipped.
    from ai_model.data.acquire import sha256_file
    from ai_model.training.reproducibility import source_hashes
    from ai_model.models import registry
    from ai_model.data.preprocessing import build_transform

    root = inference.ROOT
    config = json.loads((root / 'ai_model/config/e4.json').read_text())
    mapping = json.loads((root / 'ai_model/config/dataset_spec.json').read_text())
    classes = [{key: row[key] for key in ('index', 'code', 'name')} for row in mapping['classes']]
    identity = {'config': config, 'source_files': source_hashes(), 'manifest': {'fixture': 'SYNTHETIC_ADAPTER_TEST_ONLY'}, 'packages': {}}
    identity['fingerprint'] = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    rows = [{'experiment': key, 'status': 'completed', 'best_epoch': 1,
             'validation_macro_f1': value, 'identity': identity['fingerprint'] if key == 'E4' else key}
            for key, value in zip(('E1', 'E2', 'E3', 'E4'), (0.1, 0.2, 0.3, 0.4))]
    selection = select_candidates(rows)
    report = {'purpose': 'research_training', 'experiment': 'E4',
              'status': 'evaluated_research_model_not_clinically_validated',
              'selection': {'identity': identity['fingerprint'], 'selected_epoch': 1, 'validation_macro_f1': 0.4}}
    json_files = {'config.json': config, 'class_mapping.json': {'dataset': 'HAM10000', 'classes': classes},
                  'preprocessing.json': json.loads((root / 'ai_model/config/preprocessing.json').read_text()),
                  'evaluation.json': report,
                  'export_verification.json': {'passed': True, 'clean_process_reload_matches': True}}
    for name, value in json_files.items():
        (tmp_path / name).write_text(json.dumps(value), encoding='utf-8')
    model = SyntheticAdapterModel().eval()
    transform = build_transform(tmp_path / 'preprocessing.json')
    probe = transform(Image.new('RGB', (128, 160), 'red')).unsqueeze(0)
    torch.save(model.state_dict(), tmp_path / 'weights.pt')
    with torch.inference_mode():
        logits = model(probe)
    torch.save({'image': probe, 'logits': logits}, tmp_path / 'verification_probe.pt')
    card = {'experiment': 'E4', 'architecture': config['architecture'],
            'purpose': 'research_inference_not_clinically_validated', 'export_reload_matches': True,
            'identity': identity, 'selection': selection,
            'files_sha256': {name: sha256_file(tmp_path / name) for name in inference.REQUIRED_HASHES}}
    (tmp_path / 'model_card.json').write_text(json.dumps(card), encoding='utf-8')
    monkeypatch.setattr(registry, 'build_model', lambda *args, **kwargs: (SyntheticAdapterModel(), {}))
    return tmp_path


def test_adapter_load_smoke_and_scoring_using_synthetic_fixture(synthetic_bundle):
    service = inference.ModelService()
    service.load(synthetic_bundle)
    assert service.info.model_ready is True
    assert service.info.explanation_available is False
    label, scores = service.predict(Image.new('RGB', (150, 180), 'red'))
    assert label.code == 'vasc'
    assert sum(row.score for row in scores) == pytest.approx(1)
    assert [row.code for row in scores] == [row.code for row in service.info.classes]
    service.close()
    assert service.model is None and service.info.model_ready is False


@pytest.mark.parametrize('change', ('weights', 'missing_hash', 'path_escape', 'baseline', 'test_selection',
                                   'fixture_purpose', 'identity', 'class_order', 'probe', 'verification'))
def test_adapter_rejects_incompatible_or_tampered_exports(synthetic_bundle, change):
    from ai_model.data.acquire import sha256_file
    bundle = synthetic_bundle
    card_path = bundle / 'model_card.json'
    card = json.loads(card_path.read_text())
    if change == 'weights':
        (bundle / 'weights.pt').write_bytes(b'tampered')
    elif change == 'missing_hash':
        del card['files_sha256']['weights.pt']
    elif change == 'path_escape':
        card['files_sha256']['../outside'] = '0' * 64
    elif change == 'baseline':
        card['experiment'] = 'E1'
    elif change == 'test_selection':
        card['selection']['test_scores_used_for_selection'] = True
    elif change == 'fixture_purpose':
        report = json.loads((bundle / 'evaluation.json').read_text())
        report['purpose'] = 'technical_fixture_not_research'
        (bundle / 'evaluation.json').write_text(json.dumps(report))
        card['files_sha256']['evaluation.json'] = sha256_file(bundle / 'evaluation.json')
    elif change == 'identity':
        card['identity']['fingerprint'] = 'incorrect'
    elif change == 'class_order':
        mapping = json.loads((bundle / 'class_mapping.json').read_text())
        mapping['classes'].reverse()
        (bundle / 'class_mapping.json').write_text(json.dumps(mapping))
        card['files_sha256']['class_mapping.json'] = sha256_file(bundle / 'class_mapping.json')
    elif change == 'probe':
        torch.save({'image': torch.zeros(1, 3, 224, 224), 'logits': torch.zeros(1, 7)}, bundle / 'verification_probe.pt')
        card['files_sha256']['verification_probe.pt'] = sha256_file(bundle / 'verification_probe.pt')
    else:
        (bundle / 'export_verification.json').write_text('{"passed": false}')
    card_path.write_text(json.dumps(card))
    service = inference.ModelService()
    service.load(bundle)
    assert service.info.model_ready is False
    assert service.info.classes == [] and service.model is None
