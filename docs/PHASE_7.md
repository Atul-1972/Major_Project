# Phase 7: local web dashboard

The later explicitly authorized chatbot extension is documented in [CHATBOT.md](CHATBOT.md) and [its integration report](phase-reports/chatbot-integration.md). It preserves the original layout and classification behavior. The original 39-check/115-test results describe the pre-chatbot preparation; use the integration report for current results.

Approved on 2026-10-29: "yes start wit hthe phase 7", with supercomputer training and real-model acceptance deferred. The user paused the partial implementation, then resumed with "start from where we left the projet". The local dashboard is now implemented and verified for missing-model operation. Training, actual prediction quality and scoped Grad-CAM remain pending.

## Start and use

From `Major Project/SkinDiseaseAI` in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/backend-test.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/**. Keep the terminal open; Ctrl+C stops the server. No frontend build or Node toolchain is needed. The dashboard and API use the same origin; no CORS configuration is needed for this local setup.

1. Choose or drop one JPEG/PNG. The preview stays on your device. Basic checks reject empty/unsupported/corrupt, oversized or insufficient-dimension files; the server remains authoritative, including for animated images.
2. Review the preview and consent. Removing or replacing the image clears consent and results. Limits: 10 MiB encoded, minimum 128 × 128 pixels, maximum 20 million pixels.
3. Select **Analyze image** to send it to the service. Upload progress reflects real bytes sent; waiting for a response is indeterminate. You may cancel the request. A two-minute timeout restores controls if the service does not respond; cancellation cannot guarantee an already-received image stopped processing.
4. With no verified evaluated model configured, the expected response is **Model not available yet**, with no class scores or explanation. The request ID helps distinguish separate requests.
5. **Refresh status** checks service/model readiness. An unreachable service is distinct from an available server without a model. Review **About the model** and **Privacy & screening limitations** for context.

There are no saved accounts, image history or local/session storage in this client. The optional chatbot uses an opaque HttpOnly session cookie and short-lived server text/screening-summary memory, with explicit consent before text or opted-in labels go to a configured LLM. No image goes to a third-party AI service. Accepted uploads are processed in memory by the existing API. The app does not establish that an image depicts skin or lies within the HAM10000 dermoscopy domain.

## Source and behavior

| File | Responsibility |
| --- | --- |
| `frontend/templates/index.html` | Semantic page, file control, consent, results, navigation and limitations |
| `frontend/static/dashboard.css` | Responsive white/light-blue layout, focus styles and reduced-motion support |
| `frontend/static/dashboard.js` | Blob preview lifecycle, consent/state, actual XHR progress, timeout/cancel and API rendering |
| `frontend/static/brand.svg` | Code-authored vector identity; no lesion/patient image |
| `backend/app/main.py` | Repository-relative root/static delivery and dashboard security headers |
| `backend/tests/test_dashboard.py` | Delivery, asset references, API coexistence and private-path boundaries |
| `scripts/verify_dashboard.py` | Isolated local Chrome/Edge browser checks using generated patterns and browser-only fixtures |

Results use only schema-checked API scores, labeled as uncalibrated model scores rather than clinical risk. Text is inserted without HTML interpolation. Unexpected success payloads clear the old result. The current API supports only unavailable explanations; no sample prediction, overlay or fallback model is installed.

## Repeat verification

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

For browser checks, install the optional test dependency and use an installed Chrome or Edge:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/browser-test.txt
.\.venv\Scripts\python.exe scripts/verify_dashboard.py
```

The verifier accepts `--browser` with an executable path if automatic Windows detection is unsuitable. It launches a temporary loopback Uvicorn server and an isolated headless browser profile, then closes both. It excludes any inherited `SKINAI_MODEL_BUNDLE` so actual API checks exercise unavailable inference. Generated patterns and browser-intercepted success/error/ready fixtures are explicitly synthetic. The timeout check uses a temporary browser-only accelerated timeout. These checks do not establish trained-model performance.

Screenshots, process logs and `verification.json` stay in ignored `reports/local/phase7-browser/`. This Windows agent sandbox prevents Chrome GPU subprocess startup; normal authorized execution was required for the passing browser run. It does not require disabling Chrome's own sandbox.

See [the Phase 7 report](phase-reports/phase-7.md) for outcomes and remaining dependencies. Real-model end-to-end acceptance needs the reviewed college export; Grad-CAM needs implementation and validation with its actual branch/layer scope. Phase 8, hosting/deployment and mobile development require separate approval.
