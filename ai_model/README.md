# AI research component

Phase 1 establishes the experiment design only. No dataset has been audited, no training has run, and no trained skin-lesion weights are present.

| Directory | Purpose in later approved phases |
| --- | --- |
| `config/` | Dataset/class specification and experiment configuration |
| `data/` | Dataset loading, auditing, preprocessing, and splitting code |
| `models/` | E1/E2 baselines and E3/E4 fusion definitions |
| `training/` | Training, validation, and resumable checkpoints |
| `evaluation/` | Metrics, error analysis, calibration, and comparison |
| `explainability/` | Grad-CAM and compatible explanations |
| `notebooks/` | Runnable Colab entry points when training is implemented |
| `checkpoints/` | Local/private model checkpoints; excluded from Git |
| `exports/` | Evaluated inference bundles; excluded from Git |
| `results/` | Local run artifacts; publish only reviewed non-sensitive reports |

See `docs/DATASET_PLAN.md` and `docs/EXPERIMENT_PLAN.md`. Image files belong under ignored `data/ham10000/`, not under these source directories.
