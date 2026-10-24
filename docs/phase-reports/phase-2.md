# Phase 2 report

Date: 2026-10-25 (Asia/Calcutta).

Status: paused at the user's explicit "Pause now" request. Implementation is tested; full image acquisition and real-cohort verification are still pending. Phase 3 is not authorized.

## Authorization

User instruction: "start phase 2". Scope is acquisition support, source audit, leakage-aware splits, preprocessing, and loader verification. No model training or application implementation is included.

## Implemented and verified code

- Official-source acquisition with resumable serial or validated parallel byte ranges, per-file SHA-256 receipts, unchanged source archives, and bounded/path-safe extraction.
- A checked one-to-one join of ISIC diagnosis labels and lesion identifiers into the explicitly derived `metadata.csv`.
- Full-file image/label audit, source-count checks, decoded-pixel hashing, conservative near-duplicate matching, connected patient/lesion/duplicate groups, and honest missing-demographic reporting.
- Deterministic, class-aware grouped train/validation/test assignment, class coverage and overlap assertions, ordered class mapping, frozen preprocessing, and immutable checksum-protected manifest bundles.
- Shared orientation/RGB/letterbox/normalization transforms; training-only flips and color jitter; checksum-verified PyTorch Dataset and seeded DataLoader.
- CPU batch-verification entry point, Windows instructions, pinned dependencies, actual environment freeze, source attribution, and a Colab data-preparation notebook.

Code checkpoint: local Git commit `6df3a2f` (implementation before full-cohort verification).

## Source metadata findings

Harvard returned HTTP 403. The documented official ISIC 2018 Task 3 distribution was used instead; see `DATASET_SOURCE.md`. The source labels and grouping tables each contain 10,015 matching image entries and 7,470 distinct lesion IDs. No patient identifiers or age/sex/localization fields are supplied by this distribution.

| Diagnosis code | Actual source metadata rows |
| --- | ---: |
| akiec | 327 |
| bcc | 514 |
| bkl | 1099 |
| df | 115 |
| mel | 1113 |
| nv | 6705 |
| vasc | 142 |

These are measured metadata counts. They are not yet a passed audit of all image files.

## Completed checks

- All 30 automated tests passed in the local venv. Synthetic fixtures are explicitly labeled test-only, not research data or model performance evidence.
- Torch 2.9.1+cpu and Torchvision 0.24.1+cpu imported; a CPU matrix operation passed; CUDA is unavailable locally.
- NumPy 2.3.5 and Pillow 12.0.0 installed; `pip check` reported no broken requirements.
- Python source compiled. Colab notebook JSON and all code cells parsed; no Colab execution is claimed.
- Source diff whitespace checks passed. Source images/data, private chat archives, and runtime artifacts are ignored by Git.

After adding the source probe and completion runner, all 34 tests passed in 9.21 seconds. Runner tests verify completion gating and protection of an already-running job. `pip check` again reported no broken requirements. The actual-cohort pipeline is not yet verified, and no claim is made that the completion runner has already processed the full data.

## Actual image-data gate — pending

The official image ZIP is 2,771,732,744 bytes. The user confirmed slow Wi-Fi, then requested a pause. The download was stopped, retaining its contiguous prefix, entity-tag metadata, completed small files and range chunks. The latest saved byte count is in `.project/phase2_run.local.json`. A regional source probe measured only about 0.011 MiB/s; changing the endpoint did not remove the bottleneck. The completion runner was not left running. Tomorrow `scripts/run_phase2.py` can resume acquisition, check dependencies/tests, run actual-data preparation, and write the final report/checkpoint only on success. The standalone preparation command after acquisition is:

```powershell
.\.venv\Scripts\python.exe -u -m ai_model.data.pipeline prepare
```

Before closing Phase 2, record the real image audit, class coverage, detected duplicate/group counts, zero prohibited cross-split overlaps, frozen manifest hashes, and real train/val/test tensor batches. Do not mark this gate passed from synthetic tests.

## Limits

No patient-disjointness claim is possible with absent patient IDs. Perceptual duplicate detection is heuristic. Data use remains subject to CC BY-NC 4.0 attribution and noncommercial conditions. No clinical or ordinary smartphone-photo validity has been demonstrated. No training, model results, API, dashboard, Flutter app, or deployment has been produced.
