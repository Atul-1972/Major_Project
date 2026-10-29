# API specification — backend and dashboard

FastAPI routes are implemented under the explicit 2026-10-28 approval to prepare Phase 6 while training is deferred. Phase 7 dashboard preparation was approved on 2026-10-29. No real skin-lesion prediction has been verified. The default server has no model and returns 503 for valid prediction uploads. The same service now serves the dashboard and API on one origin.

| Endpoint | Implemented behavior |
| --- | --- |
| `GET /` | Local dashboard HTML; no image or result is embedded |
| `GET /static/{path}` | Public dashboard CSS/JavaScript/vector asset only; no source/data mount |
| `GET /health` | 200 if the process is live; report `model_ready` separately |
| `GET /model-info` | Readiness, version, architecture, input domain, ordered classes, score semantics, calibration and explanation support; unavailable fields are null/empty when no model is loaded |
| `POST /predict` | Multipart image upload; validates the image, then returns 503 unless the evaluated export is ready |
| `GET /docs` | FastAPI development documentation; exposure controlled at deployment |

## Predict request

Use exactly one multipart file field `image`, with no extra fields. JPEG and PNG only. Limits: 10 MiB encoded image bytes, 20 million decoded pixels, and minimum dimensions 128 × 128. The entire request is capped at 10 MiB + 64 KiB before multipart parsing, including when Content-Length is absent or inaccurate. Validate the actual decoded format instead of trusting filename or MIME. Reject unreadable, animated/multiframe, excessive-size, or unsupported images. Technical acceptance does not certify image-domain suitability or medical quality.

Normalize orientation and apply the exact exported deterministic preprocessing. Grad-CAM is unavailable in this implementation; no explanation request parameter is supported yet. Upload validation runs before the readiness check, so invalid uploads still return the appropriate 4xx while weights are absent.

## Successful response fields

- `request_id`: generated identifier without patient information.
- `model_version` and `input_domain` from the validated bundle.
- `predicted_class`: class ID/code/display name for the actual maximum score.
- `scores`: class scores in the exported class order, with `index`, `code`, `name`, and `score`; `score_type` is `uncalibrated_softmax`, with `calibrated: false`.
- `explanation`: availability, method, target class, scope/layer, and image payload only when actually generated. No reference to nonexistent overlay files.
- `quality`: technical checks and any defined quality warnings; no unsupported claim that an image depicts skin or lies in distribution.
- `limitations`: research/dermoscopy scope and professional-care guidance.

Never supply illustrative confidence numbers as real API results. Pydantic schemas and the binary upload contract are exposed in OpenAPI. Test success responses use explicitly labeled isolated fixtures, not research predictions.

## Failure contract

| Condition | HTTP status |
| --- | ---: |
| Missing multipart image / invalid request schema | 422 |
| Unsupported decoded image format | 415 |
| Encoded bytes or decoded pixel limit exceeded | 413 |
| Corrupt, animated, or insufficient-size image | 422 |
| Missing/incompatible model bundle | 503 |
| Invalid Content-Length | 400 |
| Internal inference failure | 500 with safe message and request ID |

Errors contain `request_id` and `error: {code, message}`. Every response has `X-Request-ID` and `Cache-Control: no-store`. No raw request fields, paths or tracebacks are included in prediction errors. Uploaded images and EXIF are not logged or retained; capped multipart files remain in memory and their handles are closed. Grad-CAM always reports unavailable pending implementation/validation.

## Startup and readiness

Only an explicitly configured trusted local `SKINAI_MODEL_BUNDLE` is considered. Check required files/hashes, E3/E4 architecture, training/source identity, validation-only selection, matching research evaluation, fixed HAM10000 class order, preprocessing, strict tensor state, and clean-process export evidence. Load once per worker on CPU, with `pretrained=False` and tensor-only loading; there is no download or random fallback. Readiness requires a local finite-output smoke inference matching the exported probe. Invalid/missing bundles keep the process live with `model_ready: false`. Startup diagnostics expose only `model_not_configured` or `model_bundle_rejected` publicly. The adapter is verified using labeled synthetic fixtures; a real returned export still needs review and acceptance.

Use `SKINAI_DOCS=0` to disable both `/docs` and `/openapi.json`. Binding to localhost is the documented development configuration. Deployment/authentication/hosting decisions belong to later approval.

## Dashboard integration

The dashboard calls health/model-info without uploading an image. File selection and preview stay local until consent and explicit submit; `/predict` receives exactly one `image` field. Upload percentage uses native XHR events; waiting for the service is indeterminate, with no invented analysis percentage. Requests time out after two minutes. Cancel restores controls but cannot guarantee the server stopped processing an already-received upload.

Responses are inserted as text, without HTML interpolation. The current prediction schema supports only unavailable explanations; the page never invents a heatmap. Missing or malformed success responses hide scores and show an error. Images, results and consent are not persisted in browser storage. Removing/replacing the selection releases its blob URL and clears old result fields. The HTML response restricts scripts/styles/connections to the same origin and permits blob previews through its content security policy.
