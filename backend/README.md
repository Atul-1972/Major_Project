# FastAPI backend

Phase 6 was explicitly approved on 2026-10-28 with supercomputer training deferred. The API runs now and reports inference unavailable until a verified evaluated hybrid export is configured.

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/backend-test.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` for the dashboard or `/docs` for API documentation. API routes: `/health`, `/model-info`, `/predict`; dashboard assets: `/static/`. Run `.\.venv\Scripts\python.exe -m pytest backend/tests -q` for focused checks.

See [the backend guide](../docs/PHASE_6.md), [dashboard guide](../docs/PHASE_7.md), [API contract](../docs/API_SPEC.md), and [phase report](../docs/phase-reports/phase-6.md). Source is in `backend/app/`; tests are in `backend/tests/`. Phase 7 dashboard preparation was approved on 2026-10-29 with training deferred; real-model acceptance remains pending.
