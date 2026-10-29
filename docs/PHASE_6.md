# Phase 6: backend while supercomputer training is deferred

Approved on 2026-10-28: "Yes, start Phase 6 with training deferred". The service is runnable independently of model availability. Phases 3-5 remain pending actual GPU training, evaluation, trained export and explanation evidence. Phase 6 remains in progress until real-model acceptance passes. Phase 7 dashboard preparation was separately approved on 2026-10-29; see `PHASE_7.md`. Mobile development and deployment remain unapproved.

## Run locally

Run from `Major Project/SkinDiseaseAI`, in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/backend-test.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Keep that terminal open while using the API. Ctrl+C stops the server.

- `http://127.0.0.1:8000/health`: process status with `model_ready: false` by default.
- `http://127.0.0.1:8000/model-info`: unavailable reason and empty model metadata until loaded.
- `http://127.0.0.1:8000/docs`: interactive API documentation; expand `POST /predict`, select **Try it out**, and upload a JPEG or PNG.

A technically valid upload currently returns **503 model_unavailable**. This is the expected outcome while training is deferred. Corrupt/unsupported/oversized images return the documented 4xx errors. No confidence scores or Grad-CAM overlays are fabricated. A dashboard is not included in Phase 6.

The backend packages are pinned in `requirements/backend.txt`, with test dependencies in `backend-test.txt`. The actual Windows Python 3.11 environment is frozen in `requirements/locks/backend-windows-py311.txt`. Missing-model operation needs no training/GPU; loading returned weights also needs the matched PyTorch/Torchvision environment already described in `requirements/phase3-windows.txt`.

## Code locations

| Path | Purpose |
| --- | --- |
| `backend/app/main.py` | App factory, startup/shutdown, routes, request cap and safe errors |
| `backend/app/uploads.py` | In-memory multipart parsing, decoding, dimensions and orientation checks |
| `backend/app/inference.py` | Hybrid export integrity/provenance checks, load once and CPU prediction |
| `backend/app/schemas.py` | Public JSON response schemas |
| `backend/app/settings.py` | Environment settings and upload limits |
| `backend/tests/` | HTTP validation/failure contracts and explicitly synthetic adapter fixtures |

The dataset, initialization caches and existing training ZIP are unchanged. Work does not run training or upload any image to another service. Accepted request bodies remain bounded in memory; multipart handles and decoded images are closed after processing. No upload directory or patient history is created.

## When the supercomputer results return

1. Follow `TRAINING_PACKAGE.md` and `SUPERCOMPUTER_BEGINNER_GUIDE.md` to retrieve the complete results, logs, evaluation, selection, checksums and `selected-hybrid/` export. Keep these private artifacts out of Git.
2. Review E1-E4 GPU/recovery evidence, validation-only hybrid selection, held-out metrics and the research limitations. Verify the original training/export source identity. A checksum match alone is not evidence of model quality or clinical validity.
3. Keep `selected-hybrid/` intact, including `model_card.json`, `weights.pt`, `config.json`, `class_mapping.json`, `preprocessing.json`, `evaluation.json`, `verification_probe.pt`, and `export_verification.json`. Use only the trusted project-generated export. The service rejects changes to its required hashed files, unsupported class order, source mismatch, baseline substitution, fixture evaluation purpose, or probe mismatch.
4. After review, configure the returned directory and restart the backend:

```powershell
$env:SKINAI_MODEL_BUNDLE = (Resolve-Path 'artifacts/training/selected-hybrid').Path
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

The default device is CPU. Construction does not download ImageNet weights. The model loads once per worker and inference is serialized per worker. Missing or rejected exports keep `/health` live and predictions unavailable. `model_ready: true` means software loading/smoke checks passed, not that clinical validity was established. If the card's training source hashes differ from the current `ai_model/` source, investigate compatibility before enabling that export.

5. Verify real prediction outputs against the returned model in a separate acceptance check, including preprocessing, class order and repeatability. Record the actual results. Keep Grad-CAM unavailable until its branch/layer scope is implemented and validated; this backend never invents explanations. Finish the remaining Phase 6 acceptance/report and the real-model dashboard checks. The 2026-10-29 ordering override permits dashboard preparation before this evidence returns.

To remove a configured bundle from the current shell:

```powershell
Remove-Item Env:SKINAI_MODEL_BUNDLE -ErrorAction SilentlyContinue
```

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe -m pytest -q
```

The focused suite covers unavailable models, bounded/chunked uploads, bad formats, corrupt and animated images, orientation, memory-only cleanup, safe inference failures, docs configuration, startup loading, integrity checks and synthetic adapter scoring. Synthetic fixtures are injected only by tests and are not shipped as a model or exposed by the normal app.

The app uses FastAPI's documented [lifespan mechanism](https://fastapi.tiangolo.com/advanced/events/) to load shared model resources before handling requests. Final evidence and limitations are recorded in `phase-reports/phase-6.md`.
