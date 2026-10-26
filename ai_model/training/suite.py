"""Sequential E1-E4 orchestration; validation selection precedes all test access."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS = ('E1', 'E2', 'E3', 'E4')
FINISHED = ('completed', 'early_stopped')


def verify_package(root):
    from ai_model.data.acquire import sha256_file

    root = Path(root).resolve()
    path = root / 'training_bundle_manifest.json'
    if not path.is_file():
        raise ValueError('No training bundle manifest. Use the extracted complete training ZIP.')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if manifest.get('experiments') != list(EXPERIMENTS) or not manifest.get('includes_data') or not manifest.get('includes_initialization'):
        raise ValueError('The complete E1-E4 bundle with data and initialization is required')
    for name, digest in manifest['files_sha256'].items():
        target = (root / name).resolve()
        if not target.is_relative_to(root) or not target.is_file() or sha256_file(target) != digest:
            raise ValueError(f'Package file missing or changed: {name}')
    print(f"Package verified: {len(manifest['files_sha256'])} files", flush=True)
    return manifest


def select_candidates(rows):
    """Fix comparison and hybrid choices without reading any held-out score."""
    if [row['experiment'] for row in rows] != list(EXPERIMENTS):
        raise ValueError('All four declared experiments must finish before selection')
    import math

    if any(row['status'] not in FINISHED or row['best_epoch'] is None or not math.isfinite(row['validation_macro_f1']) for row in rows):
        raise ValueError('Selection requires finished runs and finite validation scores')
    best = max(rows, key=lambda row: row['validation_macro_f1'])
    hybrid = max((row for row in rows if row['experiment'] in ('E3', 'E4')), key=lambda row: row['validation_macro_f1'])
    return {'selection_rule': 'highest validation macro-F1; lower experiment number on ties',
            'comparison_best': best['experiment'], 'selected_hybrid': hybrid['experiment'],
            'hybrid_beats_both_baselines': hybrid['validation_macro_f1'] > max(row['validation_macro_f1'] for row in rows[:2]),
            'runs': rows, 'test_scores_used_for_selection': False}


def export_selected(root, manifests, output, selection):
    import torch
    from ai_model.data.acquire import sha256_file
    from ai_model.data.dataset import make_loader
    from ai_model.models.registry import build_model
    from .engine import load_checkpoint
    from .reproducibility import load_config
    from .storage import atomic_save

    experiment = selection['selected_hybrid']
    if experiment not in ('E3', 'E4'):
        raise ValueError('Export selection must be one of the required hybrid candidates')
    run = output / f'{experiment}-seed42'
    state = load_checkpoint(run / 'last.pt')
    report = json.loads((run / 'evaluation/report.json').read_text())
    if report['selection']['identity'] != state['identity']['fingerprint']:
        raise ValueError('Export evaluation identity mismatch')
    config = load_config(root / f'ai_model/config/{experiment.lower()}.json')
    if state['status'] not in FINISHED or state['purpose'] != 'research_training' or state['identity']['config'] != config:
        raise ValueError('Export requires a finished research run with matching config')
    torch.set_num_threads(min(4, torch.get_num_threads()))
    mapping = json.loads((manifests / 'class_mapping.json').read_text())
    model, _ = build_model(config, len(mapping['classes']), pretrained=False)
    model.load_state_dict(state['best_model'])
    model.eval()
    probe = next(iter(make_loader(root / 'data/ham10000', manifests, 'val', batch_size=1)))['image']
    with torch.inference_mode():
        expected = model(probe)
    destination = output / 'selected-hybrid'
    atomic_save(destination / 'weights.pt', state['best_model'], tensor=True)
    model.load_state_dict(torch.load(destination / 'weights.pt', map_location='cpu', weights_only=True))
    with torch.inference_mode():
        torch.testing.assert_close(model(probe), expected, rtol=0, atol=0)
    atomic_save(destination / 'config.json', config)
    atomic_save(destination / 'class_mapping.json', mapping)
    atomic_save(destination / 'preprocessing.json', json.loads((manifests / 'preprocessing.json').read_text()))
    atomic_save(destination / 'evaluation.json', report)
    atomic_save(destination / 'verification_probe.pt', {'image': probe, 'logits': expected}, tensor=True)
    files = ('weights.pt', 'config.json', 'class_mapping.json', 'preprocessing.json', 'evaluation.json', 'verification_probe.pt')
    atomic_save(destination / 'model_card.json', {'experiment': experiment, 'architecture': config['architecture'],
                'identity': state['identity'], 'initialization': state['initialization'],
                'selection': selection, 'export_reload_matches': True,
                'files_sha256': {name: sha256_file(destination / name) for name in files},
                'purpose': 'research_inference_not_clinically_validated', 'scores': 'uncalibrated softmax scores',
                'explanations': 'not included in this training package; requires separate validation',
                'clean_process_verification': 'verify-export action required; see export_verification.json'})
    print(f'Hybrid inference files saved to {destination}', flush=True)


def verify_export(output):
    import torch
    from ai_model.data.acquire import sha256_file
    from ai_model.models.registry import build_model
    from .reproducibility import load_config
    from .storage import atomic_save

    destination = Path(output) / 'selected-hybrid'
    torch.set_num_threads(min(4, torch.get_num_threads()))
    card = json.loads((destination / 'model_card.json').read_text())
    for name, digest in card['files_sha256'].items():
        path = (destination / name).resolve()
        if not path.is_relative_to(destination.resolve()) or sha256_file(path) != digest:
            raise ValueError(f'Exported file checksum mismatch: {name}')
    config = load_config(destination / 'config.json')
    mapping = json.loads((destination / 'class_mapping.json').read_text())
    model, _ = build_model(config, len(mapping['classes']), pretrained=False)
    model.load_state_dict(torch.load(destination / 'weights.pt', map_location='cpu', weights_only=True))
    model.eval()
    probe = torch.load(destination / 'verification_probe.pt', map_location='cpu', weights_only=True)
    with torch.inference_mode():
        torch.testing.assert_close(model(probe['image']), probe['logits'], rtol=1e-5, atol=1e-6)
    atomic_save(destination / 'export_verification.json', {'passed': True, 'device': 'cpu', 'clean_process_reload_matches': True})


def run_suite(root=ROOT, *, output=None, epochs_this_session=None, smoke_only=False):
    # Imports occur after package verification, for useful errors before torch installation.
    import torch
    from .engine import load_checkpoint
    from .reproducibility import environment, load_config
    from .storage import atomic_save, run_lock

    root = Path(root).resolve()
    output = Path(output).resolve() if output else root / 'artifacts/training'
    if not torch.cuda.is_available():
        raise ValueError('No usable CUDA GPU. Run inside a college NVIDIA GPU allocation, not on a CPU/login node.')
    output.mkdir(parents=True, exist_ok=True)
    with run_lock(output):
        atomic_save(output / 'gpu_environment.json', environment(torch.device('cuda')))
        freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], check=True, capture_output=True, text=True)
        (output / 'package-freeze.txt').write_text(freeze.stdout, encoding='utf-8')
        data = root / 'data/ham10000'
        manifests = data / 'processed/splits'
        # Complete bundle carries original archives and receipts, so this runs without network.
        subprocess.run([sys.executable, '-u', '-m', 'ai_model.data.acquire', '--data-dir', str(data), '--extract', '--workers', '1'], cwd=root, check=True)
        subprocess.run([sys.executable, '-u', '-m', 'ai_model.data.pipeline', 'verify', '--data-dir', str(data)], cwd=root, check=True)
        rows = []
        for experiment in EXPERIMENTS:
            config_path = root / f'ai_model/config/{experiment.lower()}.json'
            config = load_config(config_path)
            run = output / f'{experiment}-seed42'
            options = ['--data-dir', str(data), '--manifests', str(manifests), '--run-dir', str(run), '--config', str(config_path)]
            base = [sys.executable, '-u', '-m', 'ai_model.training.cli']
            # Rerun the real smoke on every new allocation before any resume.
            subprocess.run(base + ['smoke'] + options, cwd=root, check=True)
            if smoke_only:
                continue
            command = base + ['train'] + options
            if (run / 'last.pt').is_file():
                command.append('--resume')
            if epochs_this_session is not None:
                command += ['--epochs-this-session', str(epochs_this_session)]
            subprocess.run(command, cwd=root, check=True)
            state = load_checkpoint(run / 'last.pt')
            if state['status'] not in FINISHED:
                print(f'{experiment} paused. Rerun the same command to resume. Evaluation remains locked.', flush=True)
                return {'status': 'paused', 'experiment': experiment}
            rows.append({'experiment': experiment, 'status': state['status'], 'best_epoch': state['best_epoch'],
                         'validation_macro_f1': state['best_score'], 'identity': state['identity']['fingerprint']})
            del state
        if smoke_only:
            return {'status': 'smoke_passed', 'research_training_run': False}
        selection = select_candidates(rows)
        selection_path = output / 'validation_selection.json'
        if selection_path.exists() and json.loads(selection_path.read_text()) != selection:
            raise ValueError('Existing validation selection differs; do not change selections after opening test results')
        atomic_save(selection_path, selection)
        # All four validation-selected checkpoints are fixed before any final-test report.
        reports = []
        for row in rows:
            experiment = row['experiment']
            run = output / f'{experiment}-seed42'
            subprocess.run([sys.executable, '-u', '-m', 'ai_model.training.cli', 'evaluate', '--data-dir', str(data),
                            '--manifests', str(manifests), '--run-dir', str(run), '--config', str(root / f'ai_model/config/{experiment.lower()}.json'),
                            '--confirm-final-test'], cwd=root, check=True)
            report = json.loads((run / 'evaluation/report.json').read_text())
            reports.append({'experiment': experiment, 'validation_macro_f1': row['validation_macro_f1'],
                            'test_metrics': report['test_metrics'], 'training_seconds': report['training_seconds']})
        atomic_save(output / 'comparison.json', {'selection': selection, 'results': reports})
        export_selected(root, manifests, output, selection)
        subprocess.run([sys.executable, '-u', str(root / 'train.py'), '--verify-export', '--output', str(output)], cwd=root, check=True)
        atomic_save(output / 'suite_status.json', {'status': 'completed', 'selection': selection, 'gpu_training_evidence': 'per-run gpu_smoke.json and run.json'})
        return {'status': 'completed', 'selected_hybrid': selection['selected_hybrid'], 'output': str(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-package', action='store_true', help='Verify shipped files without GPU or training')
    parser.add_argument('--smoke-only', action='store_true', help='Check all four GPU models without research training')
    parser.add_argument('--epochs-this-session', type=int)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/training')
    parser.add_argument('--verify-export', action='store_true', help='Clean-process exported model check')
    args = parser.parse_args()
    if args.epochs_this_session is not None and args.epochs_this_session < 1:
        parser.error('--epochs-this-session must be positive')
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    os.environ.setdefault('MPLBACKEND', 'Agg')
    try:
        if args.verify_export:
            verify_export(args.output)
            return 0
        verify_package(ROOT)
        if args.check_package:
            return 0
        result = run_suite(output=args.output, epochs_this_session=args.epochs_this_session, smoke_only=args.smoke_only)
        print(json.dumps(result, indent=2), flush=True)
        return 0
    except (OSError, ValueError, RuntimeError, ImportError, KeyError, subprocess.CalledProcessError) as error:
        print(f'Training stopped: {error}\nKeep the output directory. Fix the reported issue, then rerun to resume.', file=sys.stderr, flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
