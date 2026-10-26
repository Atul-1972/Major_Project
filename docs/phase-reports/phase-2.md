# Phase 2 report

Date: 2026-10-25 (Asia/Calcutta).

Status: complete and locally verified. Awaiting explicit Phase 3 approval; no training has started.

## Delivered

Official ISIC acquisition/provenance, canonical metadata, actual image audit, duplicate-aware grouped splits, immutable mapping/preprocessing/manifests, PyTorch loaders, tests, Windows instructions and a statically checked Colab notebook. See `../PHASE_2.md` and `../../reports/phase2-data-summary.json` for reproducible commands and aggregate evidence.

## Actual cohort audit

Audited images: 10015. Original lesion IDs: 7470. Connected groups after duplicate handling: 7436. Exact pixel-duplicate groups: 2. Conservative near-duplicate pairs: 58.

| Class | Source images | Train | Validation | Test |
| --- | ---: | ---: | ---: | ---: |
| nv | 6705 | 4693 | 1006 | 1006 |
| mel | 1113 | 779 | 167 | 167 |
| bkl | 1099 | 769 | 165 | 165 |
| df | 115 | 81 | 17 | 17 |
| akiec | 327 | 229 | 49 | 49 |
| bcc | 514 | 360 | 77 | 77 |
| vasc | 142 | 100 | 21 | 21 |

Technical duplicate review: 11 cross-label perceptual candidates were reviewed as distinct images. Source labels and conservative connected grouping were retained. Review SHA-256: `baf5bcffa8fdf240526e1a2e9fe1e950c71f010cff35e6026b16225c2df44d6b`. The original failed audit, private contact sheet and hash-bound review remain under ignored local data/reports; see `../DUPLICATE_REVIEW.md` for the procedure and limits.

Split totals: {"train": 7011, "val": 1502, "test": 1502}. All classes are present in each split. Zero prohibited image, connected-group, lesion, or exact-pixel overlap; patient-level overlap is unknown when source IDs are unavailable.

Manifest fingerprint: `59c4dc4192093bb29e33e7d1d79c8937819d7d4e0fd05a0e552009d76e3a43fd`.

## Verification

The completion runner requires successful acquisition/extraction, `pip check`, the full pytest suite, and actual-data `pipeline prepare` before generating this report. Detailed command output is in ignored `reports/local/phase2-run.log`. Each split produced a real finite float32 image batch and int64 labels, with deterministic evaluation transforms. The full saved audit and manifest files are under ignored `data/ham10000/processed/`.

Final verification: all 42 tests passed in 14.45 seconds after adding the frozen-review completion check (the runner's immediately preceding full run passed 41 tests). `pip check` reported no broken requirements. Notebook JSON and every code cell parsed successfully; no remote Colab execution is claimed. Each actual split returned an `[8, 3, 224, 224]` float32 image batch with int64 labels. Completion evidence, review hashes and manifest checksums were independently rechecked after the runner finished. Data, private review/contact-sheet evidence and chat archives remain ignored by Git.

Recovery during resumption: the first connection was blocked by the sandbox; the network-enabled retry resumed saved bytes. A Windows status-file replacement lock interrupted acquisition at 94.35%; bounded atomic-write retries were implemented and tested before restarting. A later socket timeout recovered automatically. The initial full audit failed on eleven cross-label perceptual candidates; its report was preserved and the technical review above was applied before a second full audit passed. No source image or label was changed.

## Limitations

- No patient identifiers: lesion-disjoint splits cannot establish patient-disjointness.
- Technical visual review identified 11 cross-label perceptual candidates as distinct images; source labels are unchanged and every candidate remains grouped. This does not validate diagnoses or establish different patient identities.
- Perceptual matching is a heuristic; absence of flagged pairs does not prove absence of all related images.
- Harvard API access returned HTTP 403; the official ISIC alternate source and CC BY-NC 4.0 attribution are documented in `../DATASET_SOURCE.md`.
- Demographics absent from this distribution are not inferred. No clinical, smartphone-photo, calibration, or model-accuracy results exist.
- Colab cells were statically checked, not executed remotely by the agent. Local tests use clearly labeled synthetic fixtures only; actual-data verification is recorded separately above.
- No training, API, dashboard, mobile implementation, or deployment was run.

## Next phase

Request explicit approval for Phase 3: EfficientNetV2-S baseline setup, Colab GPU smoke test, resumable training, validation selection, evaluation and error analysis. Do not start it automatically.
