# Project checklist

## Preparation

- [x] Persistent checkpoint/history utility and resume guide.
- [x] User requirements and phase gates recorded.

## Phase 1

- [x] Read and preserve the master prompt; record explicit Phase 1 approval.
- [x] Inspect Python, Git, CPU, RAM, GPU and disk.
- [x] Confirm Colab access and dataset-download state with the user.
- [x] Create named repository and required source/report structure.
- [x] Initialize Git on `main`; exclude secrets, runtime data and weights.
- [x] Define requirements, model experiments, dataset/split protocol, architecture and API design.
- [x] Review accessible primary-source material and record access limitations.
- [x] Add a complete standard-library environment verifier and Windows setup guide.
- [x] Verify the local venv, environment checker, optional missing-ML gate, ignore rules, script compilation, and checkpoint consistency; record actual results in the phase report.
- [x] Save final Phase 1 checkpoint and stop at the approval boundary.
- [x] Receive explicit Phase 2 approval: "start phase 2" on 2026-10-25.

## Phase 2

- [x] Verify official alternate distribution and license after Harvard HTTP 403.
- [x] Download/join actual labels and lesion grouping (10,015 entries / 7,470 lesions).
- [x] Implement acquisition/resume, image/metadata audit, exact/perceptual grouping, and immutable splits.
- [x] Implement shared preprocessing and PyTorch Dataset/DataLoader with meaningful tests.
- [x] Verify local dependency imports/CPU operation, package consistency, and all 42 tests (including Windows file-lock and duplicate-review checks).
- [x] Preserve the first failed actual audit and record hash-bound technical review of eleven cross-label perceptual candidates; retain source labels and conservative grouping.
- [x] Add Windows guide, attribution, package freeze, and statically checked Colab notebook.
- [x] Finish the actual image download/extraction and audit every source image.
- [x] Verify class coverage, actual zero-overlap splits, and real train/val/test batches.
- [x] Record actual aggregate results and finalize Phase 2 report/checkpoint.
- [x] Receive explicit Phase 3 approval before starting training.

## Phase 3

Resumed on 2026-10-26. The user subsequently authorized the complete E1-E4 supercomputer training package, including Phases 4 and 5. Source/data/pretrained assets are prepared; GPU execution remains pending.

- [x] Receive explicit approval: "so start phase 3" on 2026-10-25.
- [x] Implement EfficientNetV2-S, train-only class weights, warm-up/fine-tuning and validation macro-F1 checkpoint selection.
- [x] Implement durable initial/last/best checkpoints with optimizer/scheduler/scaler/RNG state and immutable resume identity.
- [x] Verify epoch-boundary resume and interrupted-epoch recovery against uninterrupted synthetic runs.
- [x] Implement final-test gate, metrics, confusion/ROC/training plots, latency and private error analysis.
- [x] Pass all 55 local tests and the actual-network, real-image CPU diagnostic; keep diagnostic outputs separate from research results.
- [x] Create step-by-step Colab notebook and small private transfer bundle; statically validate cells and transfer checksums.
- [x] User reports Colab connection restored and `torch.cuda.is_available()` is True (not an agent-run GPU smoke test).
- [ ] Pass actual ImageNet-initialized GPU smoke on the allocated college GPU.
- [ ] Save one real training epoch to persistent college storage and verify a resumed session.
- [ ] Finish E1 training, select by validation and run the fixed final-test evaluation.
- [ ] Review actual metrics/error analysis and finalize Phase 3 report/checkpoint.
- [x] Receive explicit Phase 4 and Phase 5 approval for the full training package on 2026-10-26.

## All-model training package

- [x] Implement E2 Swin-T, E3 pooled concatenation and E4 two-token attention with shared frozen splits/protocol.
- [x] Download and checksum-verify official ImageNet initialization for both backbones.
- [x] Pass actual pretrained CPU forward/backward/checkpoint diagnostics on real images for all four models.
- [x] Implement sequential fitting, automatic epoch recovery, validation-before-test suite selection and hybrid export.
- [x] Verify clean-process E4 export compatibility and tamper rejection using explicitly untrained test fixtures.
- [x] Provide Linux setup/run launchers, a configurable Slurm template and complete ZIP builder.
- [x] Verify ZIP CRC/receipt, all 66 shipped-file hashes and extracted-source imports; 58 included tests passed. Complete repository suite: 69 passed.
- [ ] Review actual GPU training/evaluation/export evidence; complete explanation validation before application integration.

## Phase 6 preparation (approved 2026-10-28)

- [x] Record explicit approval to start Phase 6 with supercomputer training deferred.
- [x] Implement FastAPI health/model-info/predict/docs with one-time startup model loading.
- [x] Validate JPEG/PNG uploads, encoded/decoded limits, multipart fields, orientation and memory-only cleanup.
- [x] Return safe unavailable-model responses; do not expose placeholder predictions or explanations.
- [x] Implement evaluated hybrid export integrity/provenance checks and CPU smoke/reload adapter.
- [x] Pass 31 focused API/adapter tests with explicitly synthetic fixtures; dependency consistency passed.
- [x] Pass all 112 repository tests and a real Uvicorn HTTP smoke; stop the temporary server afterward.
- [ ] Review the real returned GPU/training/evaluation/export evidence and verify actual prediction acceptance.
- [ ] Implement and validate scoped explanations before claiming Grad-CAM support.
- [ ] Finalize real-model Phase 6 acceptance and request Phase 7 approval.

## Phase 7 preparation (approved 2026-10-29)

- [x] Record explicit approval to prepare the dashboard with training and real-model acceptance deferred.
- [ ] Implement FastAPI-served responsive HTML/CSS/browser JavaScript without Node tooling.
- [ ] Implement accessible upload/preview, consent, reset/cancel and actual request progress.
- [ ] Integrate readiness, safe API errors, unavailable-model feedback and response-driven results.
- [ ] Verify browser interactions and desktop/mobile-width layout; record actual evidence.
- [ ] Verify real prediction and explanation flows once trained weights and scoped explanations are available.
- [ ] Deliver the Phase 7 report and checkpoint; keep Phase 8 behind separate approval.

## Overall phase completion

- [x] Phase 2: acquire/audit HAM10000, grouped splits, preprocessing and a verified loader batch.
- [ ] Phase 3: train/evaluate E1 and verify training resume.
- [ ] Phase 4: train/evaluate E2 under the same protocol.
- [ ] Phase 5: E3/E4, scoped explanations, optional mask-backed segmentation, selection/export.
- [ ] Phase 6: implement/test FastAPI against real evaluated weights.
- [ ] Phase 7: implement/test the no-Node responsive web client.
- [ ] Phase 8: complete QA, approved deployment, academic reports and handover.
- [ ] Mobile: deferred until an explicit new user command and approved mobile plan.

The actual dataset audit, grouped manifests and CPU loader batches passed in Phase 2. Training, model metrics, prediction success and deployment remain unverified until their actual phases run. No placeholder result satisfies these checklist items.
