# Experiment and evaluation plan

Status: the user explicitly authorized all E1-E4 training implementations on 2026-10-26. All four architectures and the shared sequential training/evaluation/export workflow are implemented and locally checked; actual GPU research training and performance results remain pending.

## Ordered experiments

| ID | Model | Question |
| --- | --- | --- |
| E1 | EfficientNetV2-S | What is the CNN baseline on our locked protocol? |
| E2 | Swin-T | What is the Transformer baseline under comparable conditions? |
| E3 | CNN + Transformer pooled-feature concatenation | Does feature fusion help over both baselines? |
| E4 | Projected two-branch attention fusion | Does learned interaction help over simple concatenation? |
| E5 | Optional supervised segmentation | Can annotated masks support a separate validated task? |

Swin-T is proposed; measure feasibility with a GPU smoke test before committing the training budget. Do not substitute models or change splits without recording a new experiment/version. Fusion is required by the user; E1/E2 are comparisons, and E3/E4 are the hybrid candidates. Select between validated fusion configurations using validation evidence. Report negative or inconclusive results even if a baseline wins; do not claim superiority or silently substitute a standalone model. If no fusion candidate passes export/verification checks, report the limitation and resolve it with the user before integration.

## Initial configuration to validate

- Same audited class mapping, grouped manifests, deterministic evaluation transforms, and proposed 224-pixel input for E1–E4.
- Transfer learning with documented ImageNet initialization. Record the exact weights enum and downloaded file checksum; no skin-lesion checkpoint is presumed.
- Start with cross-entropy; compute any inverse-frequency weights from the training split only and use the same imbalance policy across comparable runs. Do not combine weighted sampling and weighted loss by default.
- Proposed optimizer: AdamW, with head warm-up at 1e-3 and backbone fine-tuning at 1e-4, weight decay 1e-4. Values are starting hypotheses, not tuned results.
- Start GPU batch size at 8, then measure memory. Record gradient accumulation/effective batch size if needed. Set `num_workers=0` for initial Windows checks.
- Proposed budgets: 3 warm-up epochs and up to 20 fine-tuning epochs, early-stopping patience 5, best checkpoint selected by validation macro-F1. Confirm time/compute constraints after the first smoke test.
- Seed Python, NumPy, and PyTorch; record nondeterminism and environment. Use additional seeds when feasible; do not report variability from a single run.

The E1 runnable config is `../ai_model/config/e1.json`; its training/resume behavior is locally tested using synthetic fixtures and an actual-network CPU diagnostic. This does not validate the hyperparameters or establish GPU compatibility/performance. The corresponding `e2.json`, `e3.json` and `e4.json` now share the starting protocol. E3/E4 independently initialize both branches from ImageNet, not trained E1/E2 checkpoints. See `TRAINING_PACKAGE.md`; compatibility still requires the actual GPU smoke tests.

## Evaluation

Use validation macro-F1 as the primary model-selection metric. For the selected configuration, unlock the test set once for final reporting. If a final comparison table includes test results for other preselected models, fix their configurations using validation first and do not use their test scores to switch the winner. Any later exploratory test-driven change requires disclosure and new independent evaluation.

Report confusion matrices with fixed class order, per-class precision, recall/sensitivity, specificity, F1 and support, plus macro-F1, balanced accuracy, overall accuracy, and one-vs-rest ROC-AUC per class/macro where defined. Specificity for a class is TN/(TN+FP) in the one-vs-rest table. Mark undefined metrics as unavailable with a reason rather than inventing values.

Record trainable/total parameters, training duration, early-stopping epoch, peak GPU memory where available, and inference latency with device, warm-up, batch size, synchronization, and timing scope. Treat images from the same group as dependent when deriving uncertainty intervals; bootstrap groups rather than images if intervals are included.

Save each run's config, code revision/dirty-state indicator, package freeze, hardware, split/config hashes, metrics, plots, checkpoint hash, and an error-analysis report. Error examples stay in private ignored storage unless their redistribution is permitted and deliberately approved.

## Confidence and explanation

Softmax outputs are model scores. They are not calibrated probabilities of disease. If calibration is added, fit it using a documented validation/calibration subset, evaluate calibration independently, and export the fitted parameters. Never tune using the locked test set. A low maximum score is not a validated out-of-distribution detector.

Grad-CAM must target the selected class and actual final model logit. Verify output dimensions, finite values, and meaningful perturbation/randomization controls where practical. An attractive overlay is not a segmentation mask or proof of causal reasoning. The fusion explanation scope is documented in `ARCHITECTURE.md`.

## Training recovery

Write atomic last/best checkpoints to durable storage at least every epoch, with optional step checkpoints when compute warrants them. Include weights, optimizer, scheduler, scaler if used, epoch/global step, validation history, RNG states, and immutable config/split identifiers. Verify an interrupted-run resume during the CNN phase before long experiments. Resume must reject architecture, class mapping, or split changes unless explicitly starting a new run.

## Export gate

No API integration until the chosen checkpoint loads in a clean process, reproduces deterministic predictions on a known input, matches the recorded class/preprocessing config, and has an evaluation/model-card record. Export plain inference weights separately from resumable training state. No minimum accuracy is invented in advance; deployment suitability depends on the documented evidence and limitations.
