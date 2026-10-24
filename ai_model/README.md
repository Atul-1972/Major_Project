# AI research component

Phase 2 implements acquisition, audit, immutable group splits, preprocessing, and data loaders. See `docs/PHASE_2.md` and the latest phase report/checkpoint for actual-data verification status. No training has run and no trained skin-lesion weights are present.

| Directory | Purpose in later approved phases |
| --- | --- |
| `config/` | Source class/count specification and shared preprocessing configuration |
| `data/` | Implemented acquisition, audit, grouped splitting, preprocessing and PyTorch loaders |
| `models/` | E1/E2 baselines and E3/E4 fusion definitions |
| `training/` | Training, validation, and resumable checkpoints |
| `evaluation/` | Metrics, error analysis, calibration, and comparison |
| `explainability/` | Grad-CAM and compatible explanations |
| `notebooks/` | Phase 2 Colab data-preparation entry point; not executed remotely by the agent |
| `checkpoints/` | Local/private model checkpoints; excluded from Git |
| `exports/` | Evaluated inference bundles; excluded from Git |
| `results/` | Local run artifacts; publish only reviewed non-sensitive reports |

See `docs/DATASET_PLAN.md` and `docs/EXPERIMENT_PLAN.md`. Image files belong under ignored `data/ham10000/`, not under these source directories.
