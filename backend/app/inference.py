"""Load a supplied evaluated hybrid export once; never initialize fallback predictions."""

import hashlib
import json
from pathlib import Path
import threading

from .schemas import ClassLabel, ClassScore, ModelInfo


ROOT = Path(__file__).resolve().parents[2]
DOMAIN = 'HAM10000 dermoscopic lesion images; ordinary phone photographs are not validated.'
LIMITATIONS = [
    'Research screening prototype; not a medical diagnosis or clinically validated system.',
    DOMAIN,
    'Softmax confidence is uncalibrated and is not clinical risk.',
    'Consult a qualified dermatologist for assessment.',
]
REQUIRED_HASHES = {
    'weights.pt', 'config.json', 'class_mapping.json', 'preprocessing.json',
    'evaluation.json', 'verification_probe.pt',
}


def read_json(path):
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('Oversized model metadata')
    return json.loads(path.read_text(encoding='utf-8'))


def validate_bundle(bundle: Path):
    """Check provenance before constructing a model or loading tensor files."""
    from ai_model.data.acquire import sha256_file
    from ai_model.training.reproducibility import load_config, source_hashes

    bundle = bundle.resolve(strict=True)
    card = read_json(bundle / 'model_card.json')
    if set(card['files_sha256']) != REQUIRED_HASHES:
        raise ValueError('Incomplete export integrity manifest')
    for name, expected in card['files_sha256'].items():
        path = (bundle / name).resolve(strict=True)
        if path.parent != bundle or sha256_file(path) != expected:
            raise ValueError('Export checksum mismatch')
    config = load_config(bundle / 'config.json')
    if (config['experiment'] not in ('E3', 'E4') or card['experiment'] != config['experiment']
            or card['architecture'] != config['architecture']
            or card['purpose'] != 'research_inference_not_clinically_validated'
            or card['export_reload_matches'] is not True):
        raise ValueError('An evaluated hybrid inference export is required')
    identity = card['identity']
    canonical = {key: value for key, value in identity.items() if key != 'fingerprint'}
    fingerprint = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
    if (fingerprint != identity['fingerprint'] or identity['config'] != config
            or identity['source_files'] != source_hashes()):
        raise ValueError('Training identity or inference source compatibility mismatch')
    selection = card['selection']
    rows = selection['runs']
    from ai_model.training.suite import select_candidates
    if selection != select_candidates(rows) or selection['selected_hybrid'] != config['experiment']:
        raise ValueError('Invalid validation-only hybrid selection')
    selected = next(row for row in rows if row['experiment'] == config['experiment'])
    report = read_json(bundle / 'evaluation.json')
    if (report['purpose'] != 'research_training' or report['experiment'] != config['experiment']
            or report['status'] != 'evaluated_research_model_not_clinically_validated'
            or report['selection']['identity'] != fingerprint or selected['identity'] != fingerprint
            or report['selection']['selected_epoch'] != selected['best_epoch']
            or report['selection']['validation_macro_f1'] != selected['validation_macro_f1']):
        raise ValueError('Evaluation and selection identities differ')
    verification = read_json(bundle / 'export_verification.json')
    if verification.get('passed') is not True or verification.get('clean_process_reload_matches') is not True:
        raise ValueError('Clean-process export verification is required')
    mapping = read_json(bundle / 'class_mapping.json')
    spec = read_json(ROOT / 'ai_model/config/dataset_spec.json')
    expected_classes = [{key: row[key] for key in ('index', 'code', 'name')} for row in spec['classes']]
    if mapping.get('dataset') != 'HAM10000' or mapping.get('classes') != expected_classes:
        raise ValueError('Unsupported class mapping or class order')
    return card, config, [ClassLabel(**row) for row in mapping['classes']]


class ModelService:
    def __init__(self):
        self.info = ModelInfo(model_ready=False, unavailable_reason='model_not_configured')
        self.model = None
        self.transform = None
        self.lock = threading.Lock()

    def load(self, bundle):
        if bundle is None:
            return
        try:
            import torch
            from ai_model.data.preprocessing import build_transform
            from ai_model.models.registry import build_model

            bundle = Path(bundle).resolve()
            card, config, labels = validate_bundle(bundle)
            transform = build_transform(bundle / 'preprocessing.json', training=False)
            model, _ = build_model(config, len(labels), pretrained=False)
            model.load_state_dict(torch.load(bundle / 'weights.pt', map_location='cpu', weights_only=True), strict=True)
            model.eval()
            probe = torch.load(bundle / 'verification_probe.pt', map_location='cpu', weights_only=True)
            size = transform.transforms[0].size
            if probe['image'].shape != (1, 3, size, size) or not torch.isfinite(probe['image']).all():
                raise ValueError('Invalid verification input')
            with torch.inference_mode():
                logits = model(probe['image'])
                if logits.shape != (1, len(labels)) or not torch.isfinite(logits).all():
                    raise ValueError('Invalid smoke output')
                torch.testing.assert_close(logits, probe['logits'], rtol=1e-5, atol=1e-6)
            self.model, self.transform = model, transform
            version = hashlib.sha256((bundle / 'model_card.json').read_bytes()).hexdigest()
            self.info = ModelInfo(
                model_ready=True, model_version=version, architecture=card['architecture'],
                input_domain=DOMAIN, classes=labels, score_type='uncalibrated_softmax',
            )
        except Exception:
            # No filesystem paths, metadata or deserialization messages enter public responses.
            self.close()
            self.info = ModelInfo(model_ready=False, unavailable_reason='model_bundle_rejected')

    def predict(self, image):
        import torch

        if not self.info.model_ready or self.model is None:
            raise RuntimeError('Inference unavailable')
        with self.lock, torch.inference_mode():
            logits = self.model(self.transform(image).unsqueeze(0))
            if logits.shape != (1, len(self.info.classes)) or not torch.isfinite(logits).all():
                raise ValueError('Invalid inference output')
            values = logits.softmax(dim=1)[0].tolist()
        scores = [ClassScore(**label.model_dump(), score=value) for label, value in zip(self.info.classes, values)]
        index = max(range(len(values)), key=values.__getitem__)
        return self.info.classes[index], scores

    def close(self):
        self.model = self.transform = None
        self.info = ModelInfo(model_ready=False, unavailable_reason='model_not_configured')
