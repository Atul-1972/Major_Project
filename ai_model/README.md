# AI research component

Phase 2 data preparation is complete. The approved E1 EfficientNetV2-S, E2 Swin-T, E3 concatenation fusion and E4 attention fusion implementations share durable checkpoint/resume, validation selection and separate final-test evaluation. See `../docs/TRAINING_PACKAGE.md` and `../docs/SUPERCOMPUTER_BEGINNER_GUIDE.md`. Local software and official-pretrained CPU diagnostics passed; actual college GPU training/evaluation remain pending. No evaluated skin-lesion weights are present. Private data, manifests, initialization/trained weights and transfer ZIPs are excluded from GitHub.

| Directory | Purpose in later approved phases |
| --- | --- |
| `config/` | Source class/count specification and shared preprocessing configuration |
| `data/` | Implemented acquisition, audit, grouped splitting, preprocessing and PyTorch loaders |
| `models/` | E1/E2 baselines and E3/E4 fusion definitions |
| `training/` | Training, validation, and resumable checkpoints |
| `evaluation/` | Metrics, error analysis, calibration, and comparison |
| `explainability/` | Grad-CAM and compatible explanations |
| `notebooks/` | Phase 2 preparation and Phase 3 E1 training notebooks; not executed remotely by the agent |
| `checkpoints/` | Local/private model checkpoints; excluded from Git |
| `exports/` | Evaluated inference bundles; excluded from Git |
| `results/` | Local run artifacts; publish only reviewed non-sensitive reports |

See `docs/DATASET_PLAN.md` and `docs/EXPERIMENT_PLAN.md`. Image files belong under ignored `data/ham10000/`, not under these source directories.
