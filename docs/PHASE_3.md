# Phase 3: EfficientNetV2-S baseline, with pause and resume

**Current training target:** the user subsequently requested all E1-E4 models and explicitly authorized Phases 4 and 5 on 2026-10-26. Use the complete supercomputer package and [TRAINING_PACKAGE.md](TRAINING_PACKAGE.md). It includes source, dataset/provider receipts, both official ImageNet initializations, setup and sequential launchers. The Colab notebook and small E1 transfer below are historical alternatives; their saved source snapshot has not been rebuilt to contain the expanded training suite. GPU/research execution remains pending.

Approved on 2026-10-25 by the user's "so start phase 3" instruction. The user also requested step-by-step Colab guidance and pause/resume support. Phase 2 data is frozen. Phase 3 stays in progress until actual GPU training, checkpoint recovery, validation selection, evaluation and error analysis are reviewed. E1 is a comparison baseline; CNN-Transformer fusion is still required in its later approved phase.

## What you need to do in Colab

1. Open [Google Colab](https://colab.research.google.com/) in a normal browser and sign in.
2. Use **File → Upload notebook** to open the local file `ai_model/notebooks/phase3_e1_training.ipynb`.
3. Select **Runtime → Change runtime type → GPU** (T4 if available), save, then connect. Run the first cell. Success means `GPU ready` followed by a GPU name. Free GPU resources are not guaranteed.
4. Open [Google Drive](https://drive.google.com/). In **My Drive**, choose **New → File upload** and upload `artifacts/colab-transfer/skindiseaseai-phase3.zip`. Keep the filename unchanged. Do not unzip it in Drive. Do not upload `.venv`, the whole repository, or your local image dataset.
5. Return to the notebook. Run cells from top to bottom with each cell's **play** button. Wait for one cell to finish before starting the next. The Drive cell asks you to authorize access through Google's dialog. The notebook verifies the transfer and the exact Phase 2 split fingerprint.
6. The image cell downloads the original dataset directly inside Colab. Your laptop does not upload the 2.6 GiB image archive. It reuses the frozen Phase 2 manifests and verifies real batches; it never regenerates splits.
7. Run the GPU smoke-test cell. Success means `passed: true`, `device: cuda` and `checkpoint_reload_matches: true`. If the official ImageNet download or a compatibility check fails, stop and share that error; do not switch to random initialization for training.
8. Run the training cell with `EPOCHS_THIS_SESSION = 1` first. Wait for `Saved epoch 1` and `status: paused`. Check **My Drive → SkinDiseaseAI-training → E1-seed42** for `last.pt`, `best.pt`, `history.json` and `status.json`.
9. Change that variable to `EPOCHS_THIS_SESSION = None`, then rerun the training cell. It detects `last.pt` and resumes automatically. Do not change the config or split files during a run.
10. When training reports `completed` or `early_stopped`, run the final evaluation cell. It saves metrics, confusion/ROC/training plots and private error records under the same Drive run folder's `evaluation/` directory. Test scores never select the checkpoint.
11. Keep the run artifacts. For review, return `gpu_smoke.json`, `history.json`, `status.json`, `evaluation/report.json` and `evaluation/report.md` to the local project under ignored `reports/local/`. Phase 3 is not complete just because the notebook was prepared or a GPU is connected.

The local agent cannot control your signed-in Colab browser or claim it executed your GPU cells. User-reported GPU availability and actual saved run evidence are recorded separately.

## Pause and resume

- A complete checkpoint is saved to Drive after each completed training/validation epoch. An initial checkpoint also protects recovery during the first epoch.
- To stop a running notebook cell, use its stop button. Changes from the unfinished epoch may be lost. Wait for Drive writes to settle before disconnecting; no tool can guarantee persistence during an interrupted remote synchronization.
- To resume after a Colab runtime resets, reopen this notebook, use the same Drive account/run folder, rerun the setup/download/smoke cells, then rerun the training cell. Original image files must be reacquired if the runtime cache disappeared.
- One epoch per session is also supported: leave `EPOCHS_THIS_SESSION = 1` and rerun the cell whenever ready.
- The saved state includes weights, AdamW moments, cosine scheduler, mixed-precision scaler, epoch/global step, history, best validation weights, early-stopping state and Python/NumPy/PyTorch/CUDA random state. Epoch shuffle and augmentation are seeded with `seed + epoch`.
- An immutable identity covers model/config, source code, class mapping, preprocessing, all manifest hashes, duplicate-review evidence and key package versions. A changed identity rejects resume. Different hardware may still change floating-point results; bitwise equivalence across machines is not promised.
- `last.pt` is authoritative. If a crash interrupts the separate `best.pt` write, resume restores best weights from `last.pt`. Never launch two sessions against the same run folder.

## Training protocol

`ai_model/config/e1.json` implements the recorded starting protocol: seed 42, batch 8, three head-only warm-up epochs at 1e-3, up to twenty full-network epochs at 1e-4, AdamW with weight decay 1e-4, a cosine fine-tuning schedule, patience five and selection by highest validation macro-F1 (earliest checkpoint on ties). Backbone parameters, BatchNorm buffers and stochastic-depth behavior stay frozen during warm-up. Training uses inverse-frequency class weights computed from `train.csv` only; there is no weighted sampler. Validation/test loss is unweighted cross-entropy.

The pretrained initialization is explicitly `EfficientNet_V2_S_Weights.IMAGENET1K_V1`; URL and full local SHA-256 are recorded. Torchvision's published ImageNet evaluation transform uses 384-pixel crops. This project deliberately retains the frozen 224-pixel letterbox protocol shared across E1–E4; do not claim it reproduces the published ImageNet recipe.

The training command reads train/validation loaders only. A separate final-test command requires a finished run and a fixed validation-selected checkpoint. A persistent test-selection receipt prevents switching checkpoint/protocol under an existing test report; interrupted evaluation may retry only the same selection. Metrics include fixed-order confusion counts, precision, sensitivity, specificity, F1/support, macro-F1, balanced accuracy, overall accuracy and one-vs-rest ROC-AUC. Undefined denominators produce null values with a documented policy. Reports include parameters, elapsed time, peak CUDA allocation and synchronized model-only latency. Private error records are technical disagreements with source labels, not clinical relabeling.

## Local commands and dependencies

From `SkinDiseaseAI`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/phase3-windows.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/build_colab_bundle.py
```

The transfer bundle is a private allowlist of model/data/training source, config, selected documentation and frozen manifest/review files. It contains no source images, archives, weights, venv, credentials or chat transcripts. Its receipt is `artifacts/colab-transfer/transfer-receipt.json`. Rebuild only after saving the intended code; do not replace an ongoing experiment's source with a modified bundle.

The optional local CPU diagnostic does not qualify as GPU training or as research performance evidence:

```powershell
.\.venv\Scripts\python.exe -m ai_model.training.cli smoke --device cpu --diagnostic-cpu --no-pretrained --run-dir artifacts/runs/E1-cpu-diagnostic
```

For a supported CUDA environment, the notebook runs these same modules:

```text
python -m ai_model.training.cli smoke --data-dir <runtime-data> --manifests <frozen-splits> --run-dir <durable-run>
python -m ai_model.training.cli train --data-dir <runtime-data> --manifests <frozen-splits> --run-dir <durable-run> --epochs-this-session 1
python -m ai_model.training.cli train --data-dir <runtime-data> --manifests <frozen-splits> --run-dir <durable-run> --resume
python -m ai_model.training.cli evaluate --data-dir <runtime-data> --manifests <frozen-splits> --run-dir <durable-run> --confirm-final-test
```

Paths in angle brackets are explained command parameters, not runnable literal paths. The notebook fills them in. A passed GPU smoke test with the same experiment identity is required before the training CLI starts. The CPU diagnostic may use random initialization only when explicitly requested; research training always requires official ImageNet initialization. No trained skin-lesion model is bundled.

## If Colab says Failed to fetch

The JavaScript stack trace alone does not identify a root cause. Test `print('Colab is working')` in a fresh connected notebook. If even that fails, diagnose the browser/runtime connection before the model code: reload, use a normal supported browser window, test without Colab-blocking extensions, and compare another network such as a phone hotspot. If third-party cookies are blocked, Google's FAQ recommends a `googleusercontent.com` exception; do not enable third-party cookies globally just for this project. The user reported that Colab was working again and `torch.cuda.is_available()` returned True; that is not yet a passed project GPU smoke test.

Sources: [Colab FAQ](https://research.google.com/colaboratory/faq.html), [Torchvision 0.24 EfficientNetV2-S](https://docs.pytorch.org/vision/0.24/models/generated/torchvision.models.efficientnet_v2_s.html), [PyTorch checkpoint guidance](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html), [PyTorch 2.9 reproducibility](https://docs.pytorch.org/docs/2.9/notes/randomness.html), [PyTorch 2.9 AMP](https://docs.pytorch.org/docs/2.9/notes/amp_examples.html).
