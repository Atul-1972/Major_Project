# Delivery phases — revised by the master prompt

The attached master prompt explicitly approved Phase 1 only and requires research before the application. This plan supersedes the original five-phase preparation proposal, archived in `phase-reports/initial-proposed-plan.md`. Ask for approval and verify each phase before starting the next. Smartphone implementation remains separately deferred.

| Phase | Scope | Exit evidence |
| --- | --- | --- |
| Preparation | Structure and persistent development records | Preparation report and saved checkpoint |
| 1 | Environment, Git, requirements, source review, dataset plan, architecture | Runnable environment verifier, documented decisions, setup guide, phase report |
| 2 | Dataset acquisition support, audit, grouped splits, preprocessing, loader | Actual audit report, immutable manifests/mapping, zero group leakage, one verified batch |
| 3 | E1 EfficientNetV2-S baseline | GPU smoke test, resumable training, validation-selected checkpoint, metrics and error analysis |
| 4 | E2 Swin-T Transformer baseline | Same saved splits, comparable training/evaluation records, baseline comparison |
| 5 | E3/E4 fusion, explainability, model selection/export; optional mask-backed E5 | Recorded positive/negative results, explanation validation, evaluated reproducible inference bundle |
| 6 | FastAPI implementation and inference tests | Health/model info/predict/docs, one-time model load, real predictions, safe failures and upload validation |
| 7 | Responsive no-Node web dashboard and API integration | Verified upload/preview/progress/result/explanation flow, consent and limitations |
| 8 | End-to-end QA, approved hosting, documentation and academic handover | Verified run/deployment records, privacy/access decisions, final report, user manual and presentation |

## Current boundary

Phase 2 is authorized by the user's "start phase 2" instruction on 2026-10-25. Dataset acquisition support, auditing, grouped splits, preprocessing, and data-loader verification are in scope. Training, application implementation, publication, and mobile implementation require their later approvals.

## Essential dependencies

- Phase 2 needs the actual source files and confirmed dataset permissions/version; download instructions can be implemented without pretending the files are already present.
- Phases 3–5 need a usable GPU runtime, storage, real data, and compatible tested dependencies. Colab access is confirmed; an allocated GPU and uninterrupted runtime are not guaranteed.
- Phase 5 must implement the required CNN–Transformer fusion. Select a fusion candidate using the predeclared validation protocol and compare it honestly with both baselines. Do not assume fusion wins or silently replace it with a standalone model. If the hybrid fails verification, resolve that limitation before integration.
- Phases 6–7 must not substitute fake predictions when weights are missing. Clearly unavailable inference is the correct behavior.
- Phase 8 needs the approved hosting/access plan and relevant credentials; it must distinguish research-demo validation from clinical validation.

## Phase report and approval process

At each boundary, write `docs/phase-reports/phase-N.md` with completed scope, files/features changed, decisions and evidence, exact checks and outcomes, unresolved dependencies/limitations, and the next phase's acceptance criteria. Update `CHECKLIST.md`, `.project/state.json`, and the chronological checkpoint history before asking for the next approval. Record the user's actual approval in `APPROVALS.md` before proceeding.

## Mobile work

The master prompt's Flutter brief is preserved for later. Its numbered mobile steps do not trigger implementation now. When the user explicitly commands mobile work, propose and obtain approval for a separate plan after checking image-domain and API suitability.
