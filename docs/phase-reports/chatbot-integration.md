# Chatbot integration: implemented; live provider acceptance pending

Date: 2026-10-29 (Asia/Calcutta). Authorized by the user's explicit chatbot-only integration prompt. The existing website was retained; no classifier, preprocessing, training, dataset or weight changes were made. No Phase 8, hosting or mobile scope was started.

## Delivered

- Scoped `chatbot.js`/`chatbot.css` add a floating button, collapsible responsive panel, user/assistant bubbles, suggested questions, typing indicator, language selection, sharing consent and clear control. The original dashboard layout is retained. The short-height mobile panel scrolls so consent and Send stay reachable.
- `backend/app/chat/` provides independent configuration, bounded session storage, provider adapter, curated retrieval, medical safety checks, routes and prediction-response observation. `main.py` adds only registration/configuration imports and an optional app-factory argument; its `/predict` function and response schema are unchanged.
- `POST /chat` uses server-owned history and optional trusted screening context. Extra client prediction/history fields are rejected. A same-origin header, HttpOnly/SameSite cookie, request bounds, rate/concurrency limits, total provider timeout and safe error messages protect the local integration.
- Successful backend predictions yield only a short in-memory class/score/version/request summary. No image, EXIF or path goes to an LLM. Opt-in controls context forwarding; failed/new uploads, selection removal, clear, expiry and context revisions invalidate old context. A slow LLM does not acquire the prediction path's lock.
- OpenAI or configured compatible Chat Completions endpoints use environment keys/model IDs. No model/key is supplied and no paid model is chosen automatically. Unconfigured ordinary conversation returns 503; selected urgent-symptom guidance is explicitly local `mode:safety`, never disguised as an LLM answer.
- A small, manually paraphrased NHS/AAD/DermNet note library supplies lexical retrieval and source IDs. Invalid citations fail closed; URLs are server-owned and the widget allowlists their hosts. Input triage and output checks supplement the safety prompt; they are not a clinically validated triage or prescribing-prevention system.
- `.env.example`, `docs/CHATBOT.md`, README/API/frontend/backend/privacy/requirements/approval/decision/checklist/resume records document activation, disabling, session/privacy behavior and tests. Existing environment-template settings were retained.

## Actual validation

| Check | Observed result |
| --- | --- |
| Focused backend suite, including 30 chatbot cases | 64 passed in 16.91 seconds |
| Final complete repository suite | 145 passed in 131.58 seconds |
| Final Chrome verification | 52 checks passed on Chrome 156.0.8078.49 |
| Existing dashboard browser behavior | Upload/preview/consent/progress/reset/cancel/error/unavailable checks remained passing |
| Chat UI browser checks | Open/collapse, focus, typing/duplicate-send control, clear, literal safe text, allowlisted links, consent, disabled widget and mobile widths/short-height composer passed |
| Real local chat API checks in browser | Urgent guidance works without provider credentials; ordinary unconfigured conversation returns honest 503 |
| Provider/session/backend tests | Context/history, isolation, cookie flags, expiry/bounds, clear/revocation, forged-context rejection, trusted fixture prediction capture, context sharing opt-in, Hindi routing, urgent patterns, negation, unsafe output, provider timeout/auth/rate/parse/size/refusal failures, invalid citations and changed in-flight context passed |
| Dependency consistency | `pip check`: no broken requirements |
| Python source parsing / diff check | Passed; Windows line-ending notices only |
| Source-only publication audit | Passed before checkpoint; no private runtime assets selected |
| Classifier/data/artifact diff | Empty; existing model/training/preprocessing files unchanged |

The existing Starlette/httpx deprecation warning remains. An initial browser assertion tried to return a DOM object through the JSON CDP harness; using a boolean corrected the harness. Screenshot review then exposed clipped controls at 320 × 568; adding short-height panel scrolling fixed it before the passing final run. The later context-revision improvement was verified with a new regression and the final full/backend/browser runs. No initial failed check is presented as passing evidence.

All success responses, provider calls and prediction capture checks in software tests use explicitly labeled fixtures or HTTP mock transports. Browser fixtures are isolated to the private test session, not application routes. The verifier strips real provider credentials from its temporary server. Test server/browser were stopped; generated patterns, screenshots and logs stay ignored under `reports/local/`.

## Remaining acceptance

Neither LLM credentials nor a chat model is configured in the environment. **No live LLM request was made.** Follow `../CHATBOT.md` to set the key privately in the server environment, select an accessible compatible model, restart Uvicorn and reload the site. Then verify real English/Hindi conversation quality, grounded condition explanations, follow-up behavior, latency, refusals and adversarial prompts with that selected provider. Local Clear cannot retract text already transmitted to the provider; its retention policy applies separately.

The classifier is still untrained on the supercomputer. Trusted prediction integration is verified only with an explicitly synthetic backend fixture; a real evaluated export and real screening explanation acceptance remain pending. Grad-CAM remains unavailable and unchanged. Browser coverage is Chrome with emulated mobile dimensions, not every physical device/browser or assistive-technology audit. Public multi-worker/shared-session deployment, authentication and production medical safety validation are outside the approved local integration.

Source references and setup details are linked in `../CHATBOT.md`. The chatbot can be disabled with `SKINAI_CHAT_ENABLED=0`, restart and reload, without changing classification behavior.
