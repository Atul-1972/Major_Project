# Train all four SkinDiseaseAI models

This is the complete E1-E4 training package requested on 2026-10-26. It includes the training source/configuration, original HAM10000 distribution and download receipts, frozen split/review files, official ImageNet initialization for both backbones, recovery/evaluation/export code, local software tests, and Linux launchers. It contains no research-trained skin-lesion weights yet.

## Start here

1. Transfer `SkinDiseaseAI-all-models-training.zip` to private persistent storage on the college system. Extract it and enter its `SkinDiseaseAI/` directory. Keep at least 20 GiB free after extraction for images/checkpoints/results; the final requirement depends on the filesystem and run artifacts. More space is preferable.
2. Use a Linux x86-64 environment with Python 3.11 recommended. Ask the administrator how to obtain one NVIDIA CUDA GPU allocation. GPU compatibility and memory use must pass the actual smoke checks; 16 GiB VRAM or more is a starting request, not a measured guarantee. The code uses one GPU and does not distribute training across multiple GPUs.
3. Set up the isolated Python environment once, on a node allowed to install packages:

```bash
bash setup_training.sh
```

This installs pinned torch 2.9.1 / torchvision 0.24.1 from the official CUDA 12.6 wheel index and the non-torch requirements. The NVIDIA driver must support the chosen CUDA build. Administrators can select the official CUDA 12.8 or 13.0 index using `TORCH_INDEX_URL`; see [official version instructions](https://pytorch.org/get-started/previous-versions/#v291). Python packages are not bundled because the college's GPU/OS/driver environment is unknown. Setup needs approved package-network access or an administrator-provided compatible environment/wheelhouse. Data and ImageNet weight downloads are already included, so they do not need internet during training.

If the college provides an existing compatible environment, activate it, install any missing packages from `requirements/training-linux.txt` in an approved environment, and use `PYTHON_BIN=/absolute/path/to/python bash run_training.sh` instead of creating another environment. Do not run the Windows or Colab installation recipes on the cluster.

4. Inside the GPU allocation, start the entire workflow:

```bash
bash run_training.sh
```

It verifies every shipped file, checks CUDA, verifies/extracts the original images, checks the frozen loaders, then trains E1, E2, E3 and E4 sequentially. Each model must pass an official-pretrained GPU smoke test before fitting. Completed epochs save checkpoints on persistent storage. All four validation-selected checkpoints are fixed before held-out test evaluation. The workflow writes comparison results and exports the validation-selected hybrid.

There is no valid way to start training merely by uploading the ZIP: the environment must exist and a GPU job must be allocated. The launcher gives a direct error when a prerequisite is missing. No college GPU execution has been verified by the local agent. Source tests/CPU checks cannot establish that the unknown system is error-free.

## If the college uses Slurm

Submit from the extracted `SkinDiseaseAI/` directory after environment setup:

```bash
sbatch submit_slurm.sh
```

The included template requests one GPU, four CPU cores, 32 GiB host RAM and 24 hours. The college may require account/partition/QOS options or different resource/time limits. Supply its actual values using `sbatch` options; these cannot be inferred from the project. For example, `--account=...` and `--partition=...` must be replaced with assigned values, not copied literally. Other schedulers require their own allocation wrapper around `bash run_training.sh`. Do not run GPU training on a login node. See [Slurm sbatch documentation](https://slurm.schedmd.com/sbatch.html).

## Check first, pause, and resume

Verify the transfer without a GPU or training:

```bash
python3 train.py --check-package
```

Check all four GPU model architectures without research training:

```bash
bash run_training.sh --smoke-only
```

Optionally stop after one E1 epoch to check saving and timing:

```bash
bash run_training.sh --epochs-this-session 1
```

Then rerun `bash run_training.sh` to resume automatically and finish the remaining models. Rerun the same command after a job time limit, disconnect or failure. An interrupted epoch repeats from its prior checkpoint. Never change the source, config, package versions, split files or output location during a resumed experiment; changes are rejected. Never launch two workflows against the same output directory. To pause at an epoch boundary, create a file named `PAUSE` in the active model's run directory; remove it before resuming. Cancelled jobs retain completed-epoch checkpoints, subject to the college filesystem's persistence behavior.

Optional software tests after setup: `.venv-hpc/bin/python -m pytest -q tests`. Fixtures are synthetic and do not generate research-performance evidence.

## What is trained

| Experiment | Architecture | Initialization |
| --- | --- | --- |
| E1 | EfficientNetV2-S CNN baseline | Official ImageNet |
| E2 | Swin-T Transformer baseline | Official ImageNet |
| E3 | Pooled CNN + Swin features concatenated into a classifier | Both official ImageNet backbones |
| E4 | Two branch vectors projected to 256 dimensions, learned branch embeddings, four-head attention, mean pooling and classifier | Both official ImageNet backbones |

All use the same frozen 7,011 / 1,502 / 1,502 train/validation/test split, 224-pixel letterboxing, seed 42, batch eight, three head-only warm-up epochs and up to twenty full-network epochs. AdamW, training-only inverse-frequency loss weights, validation macro-F1 selection and patience five are shared. During warm-up the entire backbone stays frozen, including its buffers and stochastic behavior. E3/E4 start independently from ImageNet; they do not import trained E1/E2 skin-lesion weights. E4 attends over two pooled feature tokens, not image pixels.

Each experiment's best checkpoint uses validation macro-F1, with the earliest epoch winning ties. The suite compares E3/E4 using validation scores; E3 wins a tied hybrid score. It records the best model across all four separately and never substitutes a baseline for the requested hybrid. All candidates and the hybrid choice are fixed before final test reporting. Fusion improvement is measured, not promised.

## Files to keep and return

All run outputs default to `artifacts/training/`:

- `E1-seed42/` through `E4-seed42/`: initial/last/best checkpoints, official initialization hashes, GPU smoke, run identity, per-epoch history/status, class mapping/preprocessing and final `evaluation/` metrics/plots/predictions/error records.
- `validation_selection.json`: hybrid/comparison selection made before reading held-out scores.
- `comparison.json`: final per-model metrics and durations.
- `selected-hybrid/`: inference weights, config, mapping, preprocessing, evaluation/model card and a CPU reload check in a fresh process. This includes no Grad-CAM implementation; explanation validation and application integration remain outstanding.
- `gpu_environment.json`, `package-freeze.txt`, `logs/` and the scheduler log: actual machine/software evidence and error details.
- `suite_status.json`: written as completed only after training, evaluation, export and clean-process verification finish.

Keep the whole `artifacts/training/` directory. To save it for return, from the project directory run `tar -czf SkinDiseaseAI-training-results.tar.gz artifacts/training`. Keep image-level data, weights and reports private. Do not upload this dataset-bearing ZIP to a public repository.

## Attribution and limitations

HAM10000 / ISIC 2018 source credit, provenance and CC BY-NC 4.0 conditions are in `docs/DATASET_SOURCE.md`; original archive notices are retained. Code licensing does not replace data/pretrained-weight terms. The primary research reference and the project-specific fusion extension are documented separately in `docs/EXPERIMENT_PLAN.md`. The package implements a dermoscopic research experiment, not clinical diagnosis. Scores are uncalibrated. Patient disjointness, clinical/smartphone generalization and multi-seed uncertainty are not established. No accuracy, speedup or successful GPU run is claimed in advance.
