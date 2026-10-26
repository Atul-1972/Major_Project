"""Build the private complete E1-E4 transfer ZIP with original data and initialization."""

import argparse
import ast
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ['E1', 'E2', 'E3', 'E4']
WEIGHTS = ('efficientnet_v2_s-dd5fe13b.pth', 'swin_t-704ceda3.pth')
RAW = ('ISIC2018_Task3_Training_Input.zip', 'ISIC2018_Task3_Training_GroundTruth.zip', 'ISIC2018_Task3_Training_LesionGroupings.csv')


def digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024**2), b''):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(root):
    from ai_model.data.splitting import verify_manifest_files

    root = Path(root)
    splits = root / 'data/ham10000/processed/splits'
    frozen = verify_manifest_files(splits)
    files = [root / 'ai_model/__init__.py']
    for directory in ('data', 'models', 'training'):
        files += sorted((root / 'ai_model' / directory).rglob('*.py'))
    files += sorted((root / 'ai_model/config').glob('*.json'))
    files += [root / name for name in ('train.py', 'setup_training.sh', 'run_training.sh', 'submit_slurm.sh', 'requirements/training-linux.txt', 'LICENSE', 'scripts/build_training_bundle.py')]
    files += [root / 'tests' / name for name in ('conftest.py', 'test_training.py', 'test_all_models.py', 'test_training_bundle.py', 'test_data_pipeline.py', 'test_acquire.py')]
    files += [root / 'docs' / name for name in ('TRAINING_PACKAGE.md', 'TRAINING_VALIDATION.md', 'DATASET_SOURCE.md', 'DUPLICATE_REVIEW.md', 'EXPERIMENT_PLAN.md')]
    files += [splits / name for name in frozen['files_sha256']] + [splits / 'manifest_set.json']
    data = root / 'data/ham10000'
    files += [data / 'metadata.csv', data / 'provenance.json']
    for name in RAW:
        raw = data / 'raw' / name
        receipt_path = raw.with_name(name + '.receipt.json')
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        if raw.stat().st_size != receipt['bytes'] or digest_file(raw) != receipt['sha256']:
            raise ValueError(f'Original dataset receipt mismatch: {name}')
        files += [raw, receipt_path]
    for name in WEIGHTS:
        path = root / 'artifacts/torch-cache' / name
        prefix = name.rsplit('-', 1)[1].split('.')[0]
        if not path.is_file() or not digest_file(path).startswith(prefix):
            raise ValueError(f'Missing or invalid official ImageNet initialization: {name}')
        files.append(path)
    return list(dict.fromkeys(files)), frozen


def build_bundle(root=ROOT):
    root = Path(root).resolve()
    files, frozen = collect_files(root)
    for path in files:
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f'Missing/unsafe package input: {path}')
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    hashes = {path.relative_to(root).as_posix(): digest_file(path) for path in files}
    # The top-level guide is directly visible after extracting the package.
    guide = (root / 'docs/TRAINING_PACKAGE.md').read_bytes()
    hashes['START_HERE.md'] = hashlib.sha256(guide).hexdigest()
    manifest = {'schema_version': 1, 'experiments': EXPERIMENTS, 'private_training_transfer': True,
                'includes_data': True, 'includes_initialization': True, 'includes_python_environment': False,
                'includes_research_trained_weights': False, 'split_fingerprint': frozen['input_fingerprint'],
                'files_sha256': hashes}
    output = root / 'artifacts/training-package'
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output / 'SkinDiseaseAI-all-models-training.zip'
    required = sum(path.stat().st_size for path in files)
    if shutil.disk_usage(output).free < required + 1024**3:
        raise ValueError('Insufficient free space for package plus 1 GiB reserve')
    temporary = archive_path.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary, 'w', allowZip64=True) as archive:
        for path in files:
            relative = path.relative_to(root).as_posix()
            compression = zipfile.ZIP_STORED if path.suffix in ('.zip', '.pth') else zipfile.ZIP_DEFLATED
            archive.write(path, 'SkinDiseaseAI/' + relative, compress_type=compression)
        archive.writestr('SkinDiseaseAI/START_HERE.md', guide, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr('SkinDiseaseAI/training_bundle_manifest.json', json.dumps(manifest, indent=2) + '\n', compress_type=zipfile.ZIP_DEFLATED)
    temporary.replace(archive_path)
    receipt = {'archive': archive_path.name, 'bytes': archive_path.stat().st_size,
               'sha256': digest_file(archive_path), 'files': len(hashes) + 1, 'experiments': EXPERIMENTS,
               'split_fingerprint': frozen['input_fingerprint'], 'dataset_and_imagenet_initialization_included': True,
               'gpu_execution_verified': False, 'python_environment_included': False}
    (output / 'transfer-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2), flush=True)
    return archive_path


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(ROOT))
    argparse.ArgumentParser(description=__doc__).parse_args()
    build_bundle()
