# Dermatology information chatbot

This is a modular extension to the existing FastAPI/dashboard application. It adds a floating bottom-right assistant, collapsible chat window, suggestions, typing state, clear control, English/Hindi selection, and current-session text conversation. The classifier, preprocessing, training code and prediction response schema are unchanged. The assistant cannot view images, confirm diagnoses, prescribe medicines or guarantee harmlessness.

## Configure and run

Run from the `SkinDiseaseAI` repository. The only added runtime dependency is the already test-pinned `httpx==0.28.1` HTTP client:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/backend-test.txt

$env:SKINAI_CHAT_ENABLED = '1'
$env:SKINAI_CHAT_PROVIDER = 'openai'
$env:SKINAI_CHAT_BASE_URL = 'https://api.openai.com/v1'
$env:SKINAI_CHAT_MODEL = Read-Host 'Chat model ID available to your API account'
$chatSecret = Read-Host 'LLM API key' -AsSecureString
$env:SKINAI_CHAT_API_KEY = [System.Net.NetworkCredential]::new('', $chatSecret).Password

.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/** and click the blue floating chat button. Review the text-sharing consent before sending. Select **हिंदी**, or use **Auto** to detect Devanagari input; Romanized Hindi should use the explicit Hindi selection. The model must support Chat Completions and JSON-object output. This is configurable rather than a fixed model recommendation; account access and usage charges depend on the provider. No API key or model is included in the repository, and ChatGPT access does not configure this application's API credentials.

`.env.example` documents names and defaults; the application does **not** automatically load `.env` files. Set process environment variables as above or use your own private environment loader. Restart Uvicorn after changing configuration. Keys remain server-side, are excluded from source/control, and are never returned in status, prompts or errors.

| Variable | Behavior |
| --- | --- |
| `SKINAI_CHAT_ENABLED` | `1` enables the module; `0` disables chat routes/context capture and hides the widget after restart/reload |
| `SKINAI_CHAT_PROVIDER` | `openai` or `openai_compatible` |
| `SKINAI_CHAT_MODEL` | Required model ID; no automatic default or model download |
| `SKINAI_CHAT_API_KEY` | Provider key; `OPENAI_API_KEY` is accepted as a server-only fallback |
| `SKINAI_CHAT_BASE_URL` | Base URL ending in `/v1`, without `/chat/completions`; OpenAI uses the official default shown above |
| `SKINAI_CHAT_SECURE_COOKIE` | Set `1` behind HTTPS; default `0` is for documented loopback HTTP development |

For a separately installed local or other compatible server, set `SKINAI_CHAT_PROVIDER=openai_compatible`, its base URL and model ID. Only localhost may use plain HTTP and omit a key. Remote compatible endpoints require HTTPS and a key. The compatible adapter sends `max_tokens` and JSON-object response format; OpenAI uses `max_completion_tokens` and `store:false`. A compatible provider must support those request fields. No local model/server is installed or started by this integration.

Without valid key/model configuration, ordinary chat returns **503** with an honest unavailable message. There is no canned answer masquerading as LLM output. Deterministic emergency/urgent-symptom guidance still works without a provider, is marked `mode:safety`, and does not send that message to an LLM.

## Prediction connection

The existing `POST /predict` implementation is untouched. A small optional middleware observes its successful, schema-validated **server response** and stores only class/name, uncalibrated score semantics, model version and request ID in the same session. It never saves an image, EXIF, file path or raw upload. The classifier does not wait on a chat generation lock.

Open the assistant after a real prediction and opt into **Include my current backend screening result**. The server uses its own stored summary, not a browser-supplied class or score. A client cannot submit prediction/history/system-role objects to `/chat`; extra fields are rejected. The response clearly frames the class as a screening possibility and asks relevant follow-up questions. When there is no result, the server adds an explicit missing-context notice if result sharing was requested. Training is still deferred, so the normal current application has no prediction to share.

Removing/replacing a selection requests context invalidation. A new prediction attempt clears prior context/history, even if that attempt fails. Context revision checks prevent old in-flight replies from being committed after the screening context changes. Changing the include-result choice resets backend conversation history to avoid silently forwarding previously shared screening context; prior text already sent to a provider cannot be recalled.

## Sessions, privacy and API

The application now uses an opaque **HttpOnly, SameSite=Strict, browser-session cookie** for the assistant. It contains no medical information. Server memory is bounded to 128 sessions, 10 conversation pairs per session and a 20-minute idle validity window; expired sessions are erased during subsequent store access, and all memory is lost on process restart. There is no patient account or persistent chat database. Multiple tabs in the same browser share this cookie/session; separate browser sessions are isolated. Use one Uvicorn worker for this local implementation; multi-worker/shared-session hosting is not implemented or approved.

Chat text and explicitly shared screening labels leave the server only for the configured LLM endpoint after user consent. Images never go to the LLM. No transcript, uploaded image, provider key or upstream error body is logged by the module. Clear chat revokes server context and history and deletes the cookie; it also aborts the browser request and prevents a late response from reappearing. Idle validity limits access, not a guarantee of immediate physical memory erasure at a precise time. Provider retention is governed separately by that provider; `store:false` is not a promise of zero provider retention.

| Endpoint | Purpose |
| --- | --- |
| `GET /chat/status` | Enabled/configured state; no key, endpoint secret, model path or conversation |
| `GET /chat/session` | Own session history and whether a trusted result exists |
| `POST /chat` | One message, server-owned history and optional backend context |
| `DELETE /chat/session` | Revoke and clear history/context and delete cookie |
| `DELETE /chat/context` | Invalidate current prediction/history after selection changes |

Chat session operations require `X-SkinAI-Chat: 1`. Same-origin checks reject hostile Origin/Sec-Fetch-Site values; cookies are not supplied as a body session ID. `/chat` accepts only:

```json
{"message":"How can I care for dry skin?","language":"en","consent":true,"include_prediction":false}
```

`language` is `auto`, `en` or `hi`. Messages are limited to 1,500 characters, request bodies to 16 KiB. Responses include `request_id`, `reply`, `mode`, `urgency`, `language`, `prediction_used` and allowlisted `sources`. Up to 12 requests per minute/session and four concurrent LLM generations are permitted; concurrent sends in one session return 429. Provider time is bounded to 30 seconds, browser wait to 40 seconds, and upstream responses to 64 KiB. Configuration/auth/rate-limit/timeout/malformed/ungrounded provider failures return safe errors without raw provider detail. Existing API `Cache-Control: no-store` and request IDs remain active.

## Retrieval and safety

`backend/app/chat/knowledge.py` contains a small, manually paraphrased library reviewed on 2026-10-29, with NHS, AAD and DermNet URLs. Keyword retrieval selects up to three notes, prioritizing the trusted HAM10000 class where shared. It uses no embedding download, vector database, runtime scraping or external medical search. Source IDs in LLM output are checked against the selected notes; only their server-owned titles/URLs are exposed. Unknown-only citations fail closed. This is a deliberately small RAG implementation, not comprehensive clinical retrieval or a guarantee that every sentence is entailed by a cited source.

The system prompt restricts diagnosis, prescribing, reassurance, image claims and instruction injection. Bilingual input rules detect selected urgent patterns before calling an LLM. Output rules replace detected doses, prescription instructions, definitive diagnoses, false reassurance and invented links with a conservative local response. Sources include [NHS anaphylaxis](https://www.nhs.uk/conditions/anaphylaxis/), [NHS cellulitis](https://www.nhs.uk/conditions/cellulitis/), [NHS serious blistering reactions](https://www.nhs.uk/conditions/stevens-johnson-syndrome/) and [AAD changing-lesion warning signs](https://www.aad.org/public/diseases/skin-cancer/abcdes-melanoma). Guidance uses local emergency services rather than assuming the user's country/telephone number.

Rules, prompts and retrieved notes do **not** constitute a clinically validated triage system. They cannot recognize every emergency, prevent every unsafe LLM output or validate translated medical content. Physical symptoms take priority over chat and screening scores. Selected-provider English/Hindi quality and prompt-injection behavior need evaluation before broader use. The official [Chat Completions reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) defines the provider request contract.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_chat.py -q
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check

# Optional installed Chrome/Edge verification, including the existing dashboard flow:
.\.venv\Scripts\python.exe -m pip install -r requirements/browser-test.txt
.\.venv\Scripts\python.exe scripts/verify_dashboard.py
```

Backend tests inject labeled provider/classifier fixtures and HTTP mock transports. Browser tests remove real LLM credentials from the test server, use real unconfigured-provider/urgent routes, and isolate synthetic success replies in the private browser session. No live LLM call, paid usage, real trained prediction or clinical validation is implied by those results. Screenshots/logs remain under ignored `reports/local/phase7-browser/`. Actual results and limitations are recorded in `phase-reports/chatbot-integration.md`.

## Disable without affecting screening

```powershell
$env:SKINAI_CHAT_ENABLED = '0'
```

Restart the server and reload the page. The bootstrap sees `enabled:false` and creates no widget; `/chat` and session/context routes are absent, and prediction capture is removed. The dashboard, upload validation and model availability behavior continue unchanged. The two small chatbot asset references can remain in the HTML; no framework or website redesign is required.
