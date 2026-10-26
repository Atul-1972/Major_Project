"""Prepare a private, small Phase 3 transfer bundle; never package image/weight data."""

import ast
import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def notebook(fingerprint):
    cells = []

    def markdown(source):
        cells.append({"id": f"phase3-cell-{len(cells) + 1}", "cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)})

    def code(source):
        ast.parse(source)
        cells.append({"id": f"phase3-cell-{len(cells) + 1}", "cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": source.splitlines(keepends=True)})

    markdown("""# SkinDiseaseAI — Phase 3: resumable E1 CNN baseline

GPU training has not been run by the local agent. Run these cells from top to bottom. Keep the notebook and training folder private. This is a dermoscopic research baseline, not a clinical screening result or the final fusion model.

Before starting: upload `skindiseaseai-phase3.zip` to the top level of **My Drive**. Select **Runtime → Change runtime type → GPU**, then connect. If even `print('hello')` gives a browser `Failed to fetch` error, fix the Colab connection first; see `docs/PHASE_3.md` in the local project.
""")
    markdown("""## 1. Check the GPU
Success: `GPU ready` and a GPU name. Stop here if a GPU is unavailable; free allocation is not guaranteed.
""")
    code("""import os, sys, subprocess, json, hashlib, zipfile
from pathlib import Path
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
import torch
assert torch.cuda.is_available(), 'No CUDA GPU. Select a GPU runtime and reconnect; do not start long CPU training.'
print('GPU ready:', torch.cuda.get_device_name(0))
print('PyTorch:', torch.__version__)
""")
    markdown("""## 2. Connect your Google Drive and unpack the small transfer file
Approve Drive access in Google's own dialog. Checkpoints will be saved to **My Drive / SkinDiseaseAI-training / E1-seed42**. Images are downloaded to temporary Colab storage, not uploaded from your laptop.
""")
    code("""from google.colab import drive
drive.mount('/content/drive')
BUNDLE = Path('/content/drive/MyDrive/skindiseaseai-phase3.zip')
assert BUNDLE.is_file(), 'Upload skindiseaseai-phase3.zip to My Drive, then rerun this cell.'
DESTINATION = Path('/content/skindiseaseai-phase3')
DESTINATION.mkdir(exist_ok=True)
with zipfile.ZipFile(BUNDLE) as archive:
    members = archive.infolist()
    assert len(members) < 500 and sum(x.file_size for x in members) < 100 * 1024**2, 'Unexpected transfer archive size'
    for member in members:
        target = (DESTINATION / member.filename).resolve()
        assert target.is_relative_to(DESTINATION.resolve()) and not member.filename.startswith('/') and chr(92) not in member.filename, 'Unsafe archive member'
        assert (member.external_attr >> 16) & 0o170000 != 0o120000, 'Archive symlink rejected'
    archive.extractall(DESTINATION)
PROJECT = DESTINATION / 'SkinDiseaseAI'
bundle_manifest = json.loads((PROJECT / 'colab_bundle_manifest.json').read_text())
for name, digest in bundle_manifest['files_sha256'].items():
    target = (PROJECT / name).resolve()
    assert target.is_relative_to(PROJECT.resolve()), 'Unsafe manifest path'
    assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, f'Transfer checksum mismatch: {name}'
os.chdir(PROJECT)
sys.path.insert(0, str(PROJECT))
DATA = Path('/content/skindiseaseai-data/ham10000')
MANIFESTS = PROJECT / 'data/ham10000/processed/splits'
RUN = Path('/content/drive/MyDrive/SkinDiseaseAI-training/E1-seed42')
print('Transfer verified. Checkpoint folder:', RUN)
""")
    markdown("""## 3. Verify the Python environment
Keep Colab's matched GPU PyTorch/Torchvision. Install only the small evaluation/plotting dependencies below; do not install the Windows requirements. If imports fail or packages were already loaded at other versions, restart the runtime and rerun from cell 1.
""")
    code("""subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', 'requirements/phase3-colab.txt'], check=True)
import torchvision, numpy, PIL, sklearn, matplotlib
print({'torch': torch.__version__, 'torchvision': torchvision.__version__, 'numpy': numpy.__version__, 'Pillow': PIL.__version__, 'sklearn': sklearn.__version__, 'matplotlib': matplotlib.__version__})
assert sklearn.__version__ == '1.7.2' and matplotlib.__version__ == '3.10.7', 'Restart runtime to load the requested versions'
from ai_model.data.splitting import verify_manifest_files
bundle = verify_manifest_files(MANIFESTS)
EXPECTED_SPLIT_FINGERPRINT = '""" + fingerprint + """'
assert bundle['input_fingerprint'] == EXPECTED_SPLIT_FINGERPRINT, 'Wrong Phase 2 split bundle'
RUN.mkdir(parents=True, exist_ok=True)
freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True, check=True)
(RUN / 'colab-package-freeze.txt').write_text(freeze.stdout)
""")
    markdown("""## 4. Download the original images inside Colab
This downloads about 2.6 GiB directly from the official source using Colab's connection. Allow the cell to finish. Rerun after a runtime reset; saved Drive checkpoints and the fixed split bundle stay separate. Acquisition errors stop the notebook. Keep source attribution/noncommercial conditions in `docs/DATASET_SOURCE.md`.
""")
    code("""subprocess.run([sys.executable, '-u', '-m', 'ai_model.data.acquire', '--data-dir', str(DATA), '--extract', '--workers', '4'], check=True)
from ai_model.data.pipeline import verify_loaders
batch_report = verify_loaders(DATA, MANIFESTS, RUN / 'colab-loader-verification.json')
assert batch_report['passed']
print('Frozen train/validation/test loaders passed. Splits were not regenerated.')
""")
    markdown("""## 5. Run the GPU compatibility test
This downloads the official ImageNet initialization, performs two disposable training batches, and checks checkpoint reload. It does not produce a trained research classifier. Success: `passed: true`, `device: cuda`, and `checkpoint_reload_matches: true`.
""")
    code("""BASE = [sys.executable, '-u', '-m', 'ai_model.training.cli']
OPTIONS = ['--data-dir', str(DATA), '--manifests', str(MANIFESTS), '--run-dir', str(RUN)]
subprocess.run(BASE + ['smoke'] + OPTIONS, check=True)
""")
    markdown("""## 6. Train one epoch first, then resume
The first run intentionally saves after one epoch. Success: `Saved epoch 1` and `status: paused`, with `last.pt` and `best.pt` in the Drive checkpoint folder.

After that, change **EPOCHS_THIS_SESSION = 1** to **EPOCHS_THIS_SESSION = None** and rerun this cell to continue the remaining epochs. The cell automatically adds `--resume` when a checkpoint exists. Never change config, source files, or manifests in a resumed run. A new comparison experiment needs a new run folder.

To stop sooner, click the cell's stop button. The current unfinished epoch can repeat; the last completed checkpoint is retained. After reconnecting, rerun cells 1–5, then this cell with the same RUN folder. Do not launch two notebooks against the same run folder.
""")
    code("""EPOCHS_THIS_SESSION = 1  # After the first saved epoch: change to None and rerun this cell.
command = BASE + ['train'] + OPTIONS
if (RUN / 'last.pt').is_file():
    command.append('--resume')
if EPOCHS_THIS_SESSION is not None:
    command.extend(['--epochs-this-session', str(EPOCHS_THIS_SESSION)])
subprocess.run(command, check=True)
print(json.loads((RUN / 'status.json').read_text()))
""")
    markdown("""## 7. Evaluate only the finished, validation-selected model
Run after training reports `completed` or `early_stopped`. This opens the held-out test set for the fixed model, saves metrics/plots/private error records, and never changes the selected checkpoint from test scores. If training is paused, evaluation stays locked.
""")
    code("""status = json.loads((RUN / 'status.json').read_text())
if status['status'] in ('completed', 'early_stopped'):
    subprocess.run(BASE + ['evaluate'] + OPTIONS + ['--confirm-final-test'], check=True)
    print((RUN / 'evaluation/report.md').read_text())
else:
    print('Training is not finished. Resume cell 6; final test remains locked.')
""")
    markdown("""## Stop at the phase boundary
Keep Drive checkpoints and all run records private. The agent must inspect actual GPU smoke/training/evaluation evidence before closing Phase 3. Download `gpu_smoke.json`, `history.json`, `status.json`, `evaluation/report.json`, and `evaluation/report.md` for review. Phase 4 needs separate approval. No backend or model-fusion work starts here.

Sources: [Colab FAQ](https://research.google.com/colaboratory/faq.html), [Torchvision EfficientNetV2-S](https://docs.pytorch.org/vision/0.24/models/generated/torchvision.models.efficientnet_v2_s.html), [PyTorch reproducibility](https://docs.pytorch.org/docs/2.9/notes/randomness.html), [AMP](https://docs.pytorch.org/docs/2.9/notes/amp_examples.html).
""")
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}, "colab": {"name": "SkinDiseaseAI Phase 3 E1"}}, "nbformat": 4, "nbformat_minor": 5}


def build_bundle(root=ROOT):
    from ai_model.data.splitting import verify_manifest_files
    root = Path(root)
    splits = root / "data/ham10000/processed/splits"
    manifest = verify_manifest_files(splits)
    notebook_path = root / "ai_model/notebooks/phase3_e1_training.ipynb"
    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    notebook_path.write_text(json.dumps(notebook(manifest["input_fingerprint"]), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    files = [root / "ai_model/__init__.py"]
    for directory in ("data", "models", "training"):
        files += sorted((root / "ai_model" / directory).rglob("*.py"))
    files += sorted((root / "ai_model/config").glob("*.json"))
    files += [notebook_path, root / "requirements/phase3-colab.txt"]
    files += [root / "docs" / name for name in ("PHASE_3.md", "DUPLICATE_REVIEW.md", "DATASET_SOURCE.md", "EXPERIMENT_PLAN.md")]
    files += [splits / name for name in manifest["files_sha256"]] + [splits / "manifest_set.json"]
    hashes = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    output = root / "artifacts/colab-transfer"
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output / "skindiseaseai-phase3.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, "SkinDiseaseAI/" + path.relative_to(root).as_posix())
        archive.writestr("SkinDiseaseAI/colab_bundle_manifest.json", json.dumps({"phase": 3, "private_transfer": True, "split_fingerprint": manifest["input_fingerprint"], "files_sha256": hashes}, indent=2))
    receipt = {"archive": archive_path.name, "bytes": archive_path.stat().st_size, "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(), "files": len(files), "contains_images_or_weights": False, "split_fingerprint": manifest["input_fingerprint"]}
    (output / "transfer-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return archive_path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    build_bundle()
