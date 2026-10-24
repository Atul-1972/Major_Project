# API specification — proposed, not implemented

FastAPI routes will be built in Phase 6 after evaluated model export. The same service will serve the web dashboard in Phase 7. JSON fields below define the intended contract, not sample successful predictions.

| Endpoint | Planned behavior |
| --- | --- |
| `GET /health` | 200 if the process is live; report `model_ready` separately |
| `GET /model-info` | Readiness, version, architecture, input domain, ordered classes, score semantics, calibration and explanation support; unavailable fields are null/empty when no model is loaded |
| `POST /predict` | Multipart image upload; validated image processed by the selected real model |
| `GET /docs` | FastAPI development documentation; exposure controlled at deployment |

## Predict request

Use multipart field `image`. Support JPEG and PNG only initially. Proposed limits: 10 MiB encoded bytes, 20 million decoded pixels, and minimum dimensions 128 × 128. Validate the actual decoded format instead of trusting filename or MIME. Reject unreadable, animated/multiframe, excessive-size, or unsupported images. Technical acceptance does not certify image-domain suitability or medical quality.

Normalize orientation and apply the exact exported deterministic preprocessing. Requesting an explanation is optional; its compute cost and concurrency policy will be measured before enabling it by default.

## Successful response fields

- `request_id`: generated identifier without patient information.
- `model_version` and `input_domain` from the validated bundle.
- `predicted_class`: class ID/code/display name for the actual maximum score.
- `scores`: ordered/ranked class scores computed from the model; explicitly identify `score_type` as uncalibrated softmax unless independently calibrated.
- `explanation`: availability, method, target class, scope/layer, and image payload only when actually generated. No reference to nonexistent overlay files.
- `quality`: technical checks and any defined quality warnings; no unsupported claim that an image depicts skin or lies in distribution.
- `limitations`: research/dermoscopy scope and professional-care guidance.

Never supply illustrative confidence numbers as real API results. Final schemas and OpenAPI examples will be implemented/tested with the service.

## Planned failure contract

| Condition | HTTP status |
| --- | ---: |
| Missing multipart image / invalid request schema | 422 |
| Unsupported decoded image format | 415 |
| Encoded bytes or decoded pixel limit exceeded | 413 |
| Corrupt, animated, or insufficient-size image | 422 |
| Missing/incompatible model bundle | 503 |
| Internal inference failure | 500 with safe message and request ID |

If explanation generation alone fails after a valid prediction, return the real prediction with explanation unavailable and a safe reason. Do not expose filesystem paths or stack traces to clients. Log operational metadata without images, EXIF, request bodies, or credentials.

## Startup and readiness

Validate bundle schema, architecture, weights, preprocessing, class order and hashes; load once per worker. Readiness does not become true until a smoke inference passes. A live server with missing weights returns 503 for prediction, never a random fallback. Backend tests will cover this case and successful inference using deliberately labeled test fixtures or an actual trusted export.
