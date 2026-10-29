# Web dashboard

The optional floating English/Hindi chat panel lives in `static/chatbot.js` and `static/chatbot.css`. It reads enabled/configured state from the backend, requires text-sharing consent and renders plain-text replies and allowlisted sources. The two selection lifecycle notifications in `dashboard.js` contain no prediction data; the server owns screening context. See [chatbot setup](../docs/CHATBOT.md). Set `SKINAI_CHAT_ENABLED=0`, restart and reload to omit the widget.

FastAPI serves `templates/index.html` at `/` and public assets under `/static/`. HTML, CSS and browser JavaScript require no Node, npm, build process or external asset service.

Start the service from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/. The page supports local image preview, consent, actual upload progress, cancel/reset, model status, safe errors and response-driven results. The normal application never injects test predictions. Without a verified evaluated export, submissions return model unavailable.

See [the usage and verification guide](../docs/PHASE_7.md) and [Phase 7 evidence](../docs/phase-reports/phase-7.md). Training, real predictions and scoped Grad-CAM acceptance remain pending. This is a local web client; deployment and smartphone development are separately gated.
