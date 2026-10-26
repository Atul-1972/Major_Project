# SkinDiseaseAI: college-operated Phase 3 training

For the user's own college login, follow the step-by-step [supercomputer beginner guide](SUPERCOMPUTER_BEGINNER_GUIDE.md). It covers connecting, uploading, setup, a first checkpointed GPU job, monitoring, resume and retrieving all-model results. The college has promised a login; actual connection and scheduler details are still pending.

**Superseded by the complete all-model package.** The user clarified that they will run training and explicitly authorized E1-E4, including Phases 4 and 5. Use [TRAINING_PACKAGE.md](TRAINING_PACKAGE.md) and `artifacts/training-package/SkinDiseaseAI-all-models-training.zip`. That package includes dataset archives, both official ImageNet initializations and the sequential launcher. The E1-only transfer and instructions below are retained as historical handoff context.

Prepared 2026-10-26. The student reports that the college team will train the model; student login access has not been offered. This guide accompanies the existing private `artifacts/colab-transfer/skindiseaseai-phase3.zip`. No college GPU execution is verified yet.

## Scope and transfer

Run E1 EfficientNetV2-S first, using the supplied configuration and frozen HAM10000 splits. The Transformer and fusion experiments follow separately; their training implementations are not included. This is a research baseline, not a clinically validated classifier.

The ZIP contains source, configuration, frozen manifests and duplicate-review evidence. It does not contain images, pretrained weights, the local virtual environment or chat history. Its size is 1,170,252 bytes and SHA-256 is:

```text
08b58d9e83061d3c66fbb052b39670042def142addf881cd5ccee17410048f26
```

Extract into a private persistent project directory. Run commands from its `SkinDiseaseAI/` subdirectory. Use the Python modules below; the included notebook is specifically for Colab and its Drive paths do not apply to the college system.

## Details to confirm before execution

Please return the GPU model/VRAM, software environment, scheduling/time limits and expected start date. The trainer uses one CUDA GPU; allocating multiple GPUs does not distribute this implementation. Select a compatible matched CUDA PyTorch/Torchvision pair for the facility. Python 3.11, torch 2.9.1 and torchvision 0.24.1 were tested locally on Windows CPU, not on the college GPU. Other local package versions were NumPy 2.3.5, Pillow 12.0.0, scikit-learn 1.7.2 and Matplotlib 3.10.7. Record actual versions and run the compatibility check before training.

Dataset acquisition needs the official ISIC source and pretrained initialization needs the official Torchvision weight download. If compute nodes lack network access, use an approved transfer/staging node and preserve the supplied files and provenance. Dataset attribution and noncommercial conditions are in the included `docs/DATASET_SOURCE.md`.

Use the facility's allocated compute jobs for GPU commands, with its own account, partition and time-limit settings. This guide does not supply guessed scheduler directives. Keep source, manifests, package versions and run directory unchanged between smoke, training, resume and evaluation. Persistent storage must retain checkpoints after a job ends; local scratch alone is insufficient.

## Run sequence for the college operator

These are Linux shell commands after the environment is activated and the extracted project directory is on persistent storage. Stop on any error; do not continue to training after a failed verification. Preserve logs for every step.

```bash
DATA="$PWD/data/ham10000"
MANIFESTS="$DATA/processed/splits"
RUN="$PWD/artifacts/runs/E1-seed42"

python -m ai_model.data.acquire --data-dir "$DATA" --extract --workers 4
```

Verify the frozen manifests and real data loaders; do not run dataset preparation or regenerate splits:

```bash
python - <<'PY'
from pathlib import Path
from ai_model.data.splitting import verify_manifest_files
from ai_model.data.pipeline import verify_loaders
root = Path.cwd()
data = root / 'data/ham10000'
manifests = data / 'processed/splits'
manifest = verify_manifest_files(manifests)
assert manifest['input_fingerprint'] == '59c4dc4192093bb29e33e7d1d79c8937819d7d4e0fd05a0e552009d76e3a43fd'
run = root / 'artifacts/runs/E1-seed42'
run.mkdir(parents=True, exist_ok=True)
assert verify_loaders(data, manifests, run / 'college-loader-verification.json')['passed']
PY
```

On one allocated CUDA GPU, run the official-pretrained smoke check and one epoch:

```bash
python -m ai_model.training.cli smoke --data-dir "$DATA" --manifests "$MANIFESTS" --run-dir "$RUN"
python -m ai_model.training.cli train --data-dir "$DATA" --manifests "$MANIFESTS" --run-dir "$RUN" --epochs-this-session 1
```

Verify `gpu_smoke.json` reports `passed: true`, `device: cuda` and `checkpoint_reload_matches: true`. Verify `last.pt`, `best.pt`, `history.json` and `status.json` exist on persistent storage, with one completed epoch and paused status. Return these first-step results and elapsed time to the student before full training. Do not use random initialization or alter batch size/config to bypass a failure; return the error for review.

After the first saved epoch is reviewed, resume with the same source, environment and run directory:

```bash
python -m ai_model.training.cli train --data-dir "$DATA" --manifests "$MANIFESTS" --run-dir "$RUN" --resume
```

An interrupted epoch may repeat. Never launch concurrent jobs against this run directory. After status is `completed` or `early_stopped`, evaluate the fixed validation-selected model once:

```bash
python -m ai_model.training.cli evaluate --data-dir "$DATA" --manifests "$MANIFESTS" --run-dir "$RUN" --confirm-final-test
```

## Return to the student

Return the complete private `artifacts/runs/E1-seed42/` directory, including `last.pt`, `best.pt`, `run.json`, `gpu_smoke.json`, loader verification, history/status, and the entire `evaluation/` directory with metrics, plots, predictions and error analysis. Include job logs, GPU details, actual package freeze and training duration. Keep checkpoints and image-level records private. Source modifications, if required, must be returned explicitly and must not silently overwrite the original experiment.

The student does not need to share a college password or private key. No external message or upload has been sent by the local agent.
