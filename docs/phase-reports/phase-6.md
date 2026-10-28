# Phase 6: backend prepared; real-model acceptance pending

Date: 2026-10-28 (Asia/Calcutta). User approval: "Yes, start Phase 6 with training deferred". This explicitly permits backend preparation before college research training finishes. It does not mark Phases 3-5 complete or approve the dashboard, mobile application or deployment.

## Delivered behavior

The local FastAPI server provides `/health`, `/model-info`, `/predict`, development `/docs` and OpenAPI. Liveness and model readiness are separate. With no verified evaluated hybrid configured, valid image uploads return 503 with a safe error and request ID. There are no random/ImageNet/test-fixture predictions or fabricated explanations in the normal app.

Uploads support decoded JPEG/PNG only, exactly one multipart file named `image`, 10 MiB encoded image bytes, 20 million decoded pixels and minimum 128 x 128 dimensions. A 10 MiB + 64 KiB total request cap is enforced on actual received bytes before parsing, including chunked/misdeclared bodies. Corrupt, animated/multiframe and unsupported images are rejected. Processing normalizes EXIF orientation and removes metadata from the RGB image passed to inference. Capped multipart files remain in memory and handles/images are closed after processing. No upload storage, account or patient history is introduced.

An explicitly configured trusted local hybrid export is checked for required hashes, E3/E4 architecture, immutable training/source identity, validation-only candidate selection, matching research evaluation, HAM10000 class order, deterministic preprocessing, strict tensor state and clean-process export evidence. Startup loads once per worker on CPU, without downloading weights, then requires finite logits matching the saved probe. Invalid exports remain unavailable. Model inference is serialized within a worker; scores are explicitly uncalibrated softmax, not clinical risk. Grad-CAM remains unavailable.

## Files

- `backend/app/main.py`: app factory/lifespan, routes, streaming request cap and safe responses.
- `backend/app/uploads.py`: in-memory multipart/image validation.
- `backend/app/inference.py`: trusted returned-export adapter and CPU inference.
- `backend/app/schemas.py`, `settings.py`: typed public contracts and environment configuration.
- `backend/tests/test_api.py`, `test_inference.py`: HTTP checks and synthetic export-adapter fixtures.
- `requirements/backend.txt`, `backend-test.txt`, `locks/backend-windows-py311.txt`: verified dependencies and actual combined environment freeze.
- `docs/PHASE_6.md`, `API_SPEC.md`, approval/resume/requirements/checklist records and README: current behavior, run commands, limitations and return workflow.
- `pytest.ini`: includes backend tests in the default repository suite.

The dataset, frozen manifests, existing models/training source and private all-model training ZIP are unchanged. Source-only GitHub sync setup saved in the prior session was reviewed; its 12 isolated Git integration tests passed and its real authenticated push was verified. This does not upload the private training deliverable.

## Actual validation

| Check | Observed result |
| --- | --- |
| Existing Git synchronization integration suite | 12 passed in 18.95 seconds |
| Focused Phase 6 API/export-adapter tests | 31 passed in 9.03 seconds |
| Complete repository suite, including backend and sync tests | 112 passed in 60.23 seconds |
| `python -m pip check` | No broken requirements |
| `git diff --check` | Passed; Git emitted only Windows line-ending notices |
| Real Uvicorn loopback HTTP smoke | `/health`, `/model-info`, `/docs`, `/openapi.json`: 200; valid synthetic PNG `/predict`: expected 503 |
| Smoke server cleanup | Server stopped and socket closed; no persistent server launched |

One dependency deprecation warning appears: Starlette's test client recommends `httpx2` instead of its currently supported `httpx` compatibility path. No test failed; the actual working dependency versions are pinned/frozen. An initial test run had Windows setup errors from overly long automatically generated parameter IDs; descriptive IDs fixed the test harness before the passing results above.

Synthetic HTTP and tensor fixtures are explicitly injected only in tests. They verify schemas, upload behavior, adapter loading/scoring and rejection of modified/incompatible artifacts. They are not evidence of trained skin-lesion accuracy, clinical validity, actual supercomputer execution or successful real-export integration.

## Remaining evidence and next action

Training is deferred to the college supercomputer. Obtain the facility details and run the existing all-model package when access is available. Return and review GPU smoke/recovery logs, E1-E4 training/evaluation results, validation-selected hybrid and intact inference export. Complete real-model API acceptance against independently verified outputs. Grad-CAM still needs implementation and validation with accurately scoped branch/layer information. Phase 6 remains in progress while this evidence is absent; request Phase 7 approval only at the agreed boundary or after an explicit further ordering override.

To run the current backend and inspect its code locations, follow `../PHASE_6.md`. Local development can exercise the documented service and unavailable-model behavior without training. No GPU job, external training upload, dashboard, mobile application or deployment was started in this session.
