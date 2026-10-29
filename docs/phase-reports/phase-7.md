# Phase 7: dashboard preparation delivered; real-model acceptance pending

The subsequently authorized chatbot-only extension has its own current evidence in `chatbot-integration.md`: 64 backend tests, 145 repository tests and 52 Chrome checks passed. The earlier dashboard-only results below are retained as historical evidence. Live LLM configuration/acceptance and real evaluated-model context remain pending.

Date: 2026-10-29 (Asia/Calcutta). Explicit approval: "yes start wit hthe phase 7", with training deferred. The partial dashboard was saved at "can we pause here and start later", then resumed on "start from where we left the projet". Local dashboard preparation is delivered and verified. Full Phase 7 real-prediction/explanation acceptance remains pending.

## Delivered behavior and files

- `frontend/templates/index.html`: research dashboard, navigation, upload/preview area, consent, results panel, model status, privacy and limitations.
- `frontend/static/dashboard.css`: white/light-blue layout, responsive breakpoints, readable consent/limitations, focus styles and reduced-motion support.
- `frontend/static/dashboard.js`: local JPEG/PNG preview and preliminary checks, selection reset, consent gating, same-origin API status, actual upload progress, timeout/cancellation, safe error/unavailable feedback and response-driven score presentation. No mock model is configured. Removing/replacing an image releases its blob URL, clears consent and clears visible/hidden result values. Completion focuses the actual result or feedback for keyboard users. A 503 clears stale ready-model metadata.
- `frontend/static/brand.svg`: original code-authored vector brand asset; no patient image or generated lesion image.
- `backend/app/main.py`: serves `/` and `/static` from repository-relative paths and supplies dashboard security headers. Existing API contracts remain available.
- `backend/tests/test_dashboard.py`: three new delivery/asset/private-path checks, including operation outside the repository working directory and with API docs disabled.
- `scripts/verify_dashboard.py`, `requirements/browser-test.txt`: repeatable isolated Chrome/Edge verification using Python CDP and websocket-client 1.9.2, without Node or a downloaded browser driver.
- `docs/PHASE_7.md`, README/frontend/backend/API guides, approval/requirements/decisions/checklist/resume records: current run commands, behavior, evidence and pending dependencies.

The normal backend still returns unavailable predictions without a configured evaluated export. No training or Grad-CAM validation was performed. Results render only schema-checked API responses and identify uncalibrated model scores; missing/malformed output displays no prediction. The current API's explanation state is unavailable, so no overlay is invented. Images are sent only after explicit submission with consent; no browser storage or third-party image service is used.

## Actual validation

| Check | Observed result |
| --- | --- |
| Focused backend/API/adapter/dashboard suite | 34 passed in 10.92 seconds |
| Complete repository suite | 115 passed in 125.74 seconds |
| Local Chrome verification | 39 checks passed on Chrome 156.0.8078.49 |
| Layout checks | No horizontal overflow at 320, 390, 768, 1024 and 1440 px; desktop/mobile screenshots visually inspected |
| Live API requests from browser | Root/static/readiness: 200; generated-pattern upload: expected 503; animated PNG upload: actual 422 |
| Dependency consistency | `pip check`: no broken requirements |
| Whitespace validation | `git diff --check` passed; Windows line-ending notices only |

Browser checks cover selection, invalid/corrupt/too-small/oversized/multiple files, valid drop, literal filename rendering, preview URL cleanup, file replacement/consent, no submission before consent, real upload events, unavailable-model feedback/request IDs, cancellation, timeouts, failed networks, safe errors, malformed success payloads, ready/unavailable metadata, keyboard focus and absence of storage/runtime exceptions/external requests. Success, ready-model and selected failure responses are explicitly labeled browser-intercepted fixtures; timeout verification temporarily accelerates the browser-only timer. They are not trained predictions or research evidence. No fixture route or model was added to the normal app.

The existing Starlette/httpx deprecation warning remains; no test failed. The prior sandbox installation failure was resolved through normal authorized network access. Chrome initially could not start GPU subprocesses inside the restricted Windows agent sandbox; normal authorized execution passed without disabling Chrome's own sandbox. A timeout-harness restore expression initially tried to serialize a browser prototype; returning void fixed the harness before the final passing run. The owned test server and isolated headless browser were stopped after verification; screenshots/logs/profile scratch files remain excluded from Git.

## Limitations and next action

Use `../PHASE_7.md` to start and review the local dashboard. Chrome desktop with emulated mobile widths is verified; Safari/Firefox, physical mobile devices and assistive-technology audits have not been tested. This is a responsive web client, not a smartphone application. Technical validation does not establish whether an image depicts skin or is medically suitable.

Return and review the actual college E1-E4 GPU/recovery/evaluation evidence and the selected evaluated hybrid export. Complete backend real-model acceptance, implement/validate accurately scoped Grad-CAM, then verify real browser prediction/explanation flows. Keep Phases 3-7 incomplete where that evidence is missing. Phase 8 acceptance would require separately approved QA/hosting/privacy/access and handover scope; no deployment, mobile development or Phase 8 work is authorized by this report.

Implementation references consulted: [FastAPI StaticFiles](https://fastapi.tiangolo.com/tutorial/static-files/) for static serving and [MDN XMLHttpRequest upload](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/upload) for actual upload progress events. Final browser verification remains pending.
