"""Package integrity, held-out selection rules and safe orchestration checks."""

import hashlib
import json
from pathlib import Path

import pytest
import torch

from ai_model.training import suite


def synthetic_bundle(root):
    content = b'explicitly synthetic package fixture'
    (root / 'payload.txt').write_bytes(content)
    manifest = {'experiments': list(suite.EXPERIMENTS), 'includes_data': True, 'includes_initialization': True,
                'files_sha256': {'payload.txt': hashlib.sha256(content).hexdigest()}}
    (root / 'training_bundle_manifest.json').write_text(json.dumps(manifest))
    return manifest


def test_package_tampering_missing_and_escaping_paths_are_rejected(tmp_path):
    manifest = synthetic_bundle(tmp_path)
    assert suite.verify_package(tmp_path) == manifest
    (tmp_path / 'payload.txt').write_text('changed')
    with pytest.raises(ValueError, match='missing or changed'):
        suite.verify_package(tmp_path)
    (tmp_path / 'payload.txt').unlink()
    with pytest.raises(ValueError, match='missing or changed'):
        suite.verify_package(tmp_path)
    manifest['files_sha256'] = {'../outside.txt': 'invalid'}
    (tmp_path / 'training_bundle_manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='missing or changed'):
        suite.verify_package(tmp_path)


def test_suite_selects_hybrid_using_validation_and_keeps_better_baseline_visible():
    rows = [{'experiment': name, 'status': 'completed', 'best_epoch': 2, 'validation_macro_f1': score}
            for name, score in zip(suite.EXPERIMENTS, [0.9, 0.7, 0.8, 0.8])]
    selected = suite.select_candidates(rows)
    assert selected['comparison_best'] == 'E1'
    assert selected['selected_hybrid'] == 'E3'
    assert not selected['hybrid_beats_both_baselines']
    assert selected['test_scores_used_for_selection'] is False
    rows[3]['validation_macro_f1'] = 0.95
    assert suite.select_candidates(rows)['selected_hybrid'] == 'E4'
    rows[3]['status'] = 'paused'
    with pytest.raises(ValueError, match='finished'):
        suite.select_candidates(rows)


def test_suite_refuses_cpu_research_before_acquisition(tmp_path, monkeypatch):
    monkeypatch.setattr(torch.cuda, 'is_available', lambda: False)
    monkeypatch.setattr(suite.subprocess, 'run', lambda *_a, **_kw: pytest.fail('No commands should start without a GPU'))
    with pytest.raises(ValueError, match='GPU allocation'):
        suite.run_suite(tmp_path)


def test_suite_resume_stops_at_pause_without_test_access(tmp_path, monkeypatch):
    from ai_model.training import engine, reproducibility

    monkeypatch.setattr(torch.cuda, 'is_available', lambda: True)
    monkeypatch.setattr(reproducibility, 'environment', lambda _device: {'purpose': 'MOCK_ENVIRONMENT_UNIT_TEST'})
    monkeypatch.setattr(reproducibility, 'load_config', lambda _path: {'experiment': 'E1'})
    monkeypatch.setattr(engine, 'load_checkpoint', lambda _path: {'status': 'paused'})
    calls = []

    def run(command, **_kwargs):
        calls.append(command)
        class Result:
            stdout = 'SYNTHETIC_UNIT_TEST_FREEZE'
        return Result()

    monkeypatch.setattr(suite.subprocess, 'run', run)
    run_dir = tmp_path / 'artifacts/training/E1-seed42'
    run_dir.mkdir(parents=True)
    (run_dir / 'last.pt').write_text('not real weights; command orchestration fixture')
    result = suite.run_suite(tmp_path)
    assert result == {'status': 'paused', 'experiment': 'E1'}
    assert any('train' in command and '--resume' in command for command in calls)
    assert not any('evaluate' in command for command in calls)
    assert not (tmp_path / 'artifacts/training/validation_selection.json').exists()


def test_pretrained_file_corruption_is_rejected_without_network(tmp_path, monkeypatch):
    from ai_model.models.weights import load_official_weights

    class FixtureWeights:
        url = 'https://example.invalid/fixture-deadbeef.pth'

    (tmp_path / 'fixture-deadbeef.pth').write_bytes(b'corrupt fixture')
    monkeypatch.setattr(torch.hub, 'download_url_to_file', lambda *_a, **_kw: pytest.fail('Cached corruption must not download'))
    with pytest.raises(ValueError, match='checksum mismatch'):
        load_official_weights(None, FixtureWeights(), tmp_path)


def test_full_suite_fixes_all_validation_choices_before_any_test(tmp_path, monkeypatch):
    from ai_model.training import engine, reproducibility

    monkeypatch.setattr(torch.cuda, 'is_available', lambda: True)
    monkeypatch.setattr(reproducibility, 'environment', lambda _device: {'purpose': 'MOCK_UNIT_TEST'})
    monkeypatch.setattr(reproducibility, 'load_config', lambda _path: {})
    output = tmp_path / 'artifacts/training'
    trained = []
    tested = []

    def state(path):
        experiment = Path(path).parent.name.split('-')[0]
        return {'status': 'completed', 'best_epoch': 1, 'best_score': {'E1': 0.7, 'E2': 0.6, 'E3': 0.8, 'E4': 0.75}[experiment],
                'identity': {'fingerprint': 'SYNTHETIC_' + experiment}}

    monkeypatch.setattr(engine, 'load_checkpoint', state)
    monkeypatch.setattr(suite, 'export_selected', lambda *_args: None)

    def run(command, **_kwargs):
        if 'train' in command:
            trained.append(Path(command[command.index('--run-dir') + 1]).name.split('-')[0])
        if 'evaluate' in command:
            assert trained == list(suite.EXPERIMENTS)
            selection = json.loads((output / 'validation_selection.json').read_text())
            assert selection['selected_hybrid'] == 'E3'
            run = Path(command[command.index('--run-dir') + 1])
            (run / 'evaluation').mkdir(parents=True)
            (run / 'evaluation/report.json').write_text(json.dumps({'test_metrics': {'purpose': 'SYNTHETIC_UNIT_TEST'}, 'training_seconds': 0}))
            tested.append(run.name.split('-')[0])
        class Result:
            stdout = 'SYNTHETIC_FREEZE'
        return Result()

    monkeypatch.setattr(suite.subprocess, 'run', run)
    result = suite.run_suite(tmp_path)
    assert tested == list(suite.EXPERIMENTS)
    assert result['selected_hybrid'] == 'E3'
    assert (output / 'suite_status.json').is_file()


def test_actual_attention_export_reloads_in_fresh_process_and_detects_tampering(prepared_dataset, tmp_path, monkeypatch):
    """Random untrained weights in a simulated finished run; no accuracy claim."""
    import subprocess
    import sys
    from ai_model.data import dataset
    from ai_model.models.registry import build_model
    from ai_model.training.reproducibility import load_config
    from ai_model.training.storage import atomic_save

    previous = torch.get_num_threads()
    torch.set_num_threads(2)
    try:
        source = Path(__file__).resolve().parents[1]
        config = load_config(source / 'ai_model/config/e4.json')
        config_path = tmp_path / 'export-source/ai_model/config/e4.json'
        config_path.parent.mkdir(parents=True)
        config_path.write_text(json.dumps(config))
        mapping = json.loads((prepared_dataset['splits'] / 'class_mapping.json').read_text())
        model, initialization = build_model(config, len(mapping['classes']), pretrained=False)
        output = tmp_path / 'fixture-export'
        run = output / 'E4-seed42'
        identity = {'fingerprint': 'SYNTHETIC_UNTRAINED_EXPORT_FIXTURE', 'config': config}
        state = {'status': 'completed', 'purpose': 'research_training', 'identity': identity, 'initialization': initialization,
                 'best_model': model.state_dict()}
        atomic_save(run / 'last.pt', state, tensor=True)
        atomic_save(run / 'evaluation/report.json', {'purpose': 'SYNTHETIC_UNTRAINED_EXPORT_FIXTURE', 'selection': {'identity': identity['fingerprint']}})
        del model, state
        monkeypatch.setattr(dataset, 'make_loader', lambda *_a, **_kw: [{'image': torch.rand(1, 3, 64, 64)}])
        suite.export_selected(config_path.parents[2], prepared_dataset['splits'], output, {'selected_hybrid': 'E4', 'purpose': 'SYNTHETIC_EXPORT_TEST'})
        subprocess.run([sys.executable, str(source / 'train.py'), '--verify-export', '--output', str(output)], cwd=source, check=True)
        verified = json.loads((output / 'selected-hybrid/export_verification.json').read_text())
        assert verified['clean_process_reload_matches']
        (output / 'selected-hybrid/config.json').write_text('{}')
        with pytest.raises(ValueError, match='checksum mismatch'):
            suite.verify_export(output)
    finally:
        torch.set_num_threads(previous)
