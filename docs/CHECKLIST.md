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
- [ ] Receive user verification and explicit Phase 2 approval before starting dataset work.

## Remaining phases

- [ ] Phase 2: acquire/audit HAM10000, grouped splits, preprocessing and a verified loader batch.
- [ ] Phase 3: train/evaluate E1 and verify training resume.
- [ ] Phase 4: train/evaluate E2 under the same protocol.
- [ ] Phase 5: E3/E4, scoped explanations, optional mask-backed segmentation, selection/export.
- [ ] Phase 6: implement/test FastAPI against real evaluated weights.
- [ ] Phase 7: implement/test the no-Node responsive web client.
- [ ] Phase 8: complete QA, approved deployment, academic reports and handover.
- [ ] Mobile: deferred until an explicit new user command and approved mobile plan.

Training, model metrics, dataset audit, prediction success and deployment remain unverified until their actual phases run. No placeholder result satisfies these checklist items.
