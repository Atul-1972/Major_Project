"""Run with: python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000."""

from contextlib import asynccontextmanager
from pathlib import Path
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

from .inference import LIMITATIONS, ModelService
from .schemas import ErrorResponse, Health, ModelInfo, Prediction
from .settings import MAX_REQUEST_BYTES, Settings
from .uploads import decode_image, read_upload


FRONTEND = Path(__file__).resolve().parents[2] / 'frontend'
DASHBOARD_HEADERS = {
    'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; "
    "img-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; "
    "frame-ancestors 'none'; form-action 'self'",
    'Referrer-Policy': 'no-referrer',
    'X-Content-Type-Options': 'nosniff',
}


def error_response(status, request_id, message):
    codes = {400: 'invalid_request', 413: 'image_too_large', 415: 'unsupported_image',
             422: 'invalid_image_upload', 503: 'model_unavailable', 500: 'internal_error', 404: 'not_found'}
    return JSONResponse(status_code=status, content={
        'request_id': request_id,
        'error': {'code': codes.get(status, 'request_failed'), 'message': message},
    })


class RequestBoundary:
    """Cap actual streamed bytes before parsing; assign IDs and prohibit result caching."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        request_id = uuid.uuid4().hex
        scope.setdefault('state', {})['request_id'] = request_id
        started = False

        async def safe_send(message):
            nonlocal started
            if message['type'] == 'http.response.start':
                started = True
                message['headers'] = list(message.get('headers', [])) + [
                    (b'x-request-id', request_id.encode()), (b'cache-control', b'no-store'),
                ]
            await send(message)

        async def reject(status, message):
            await error_response(status, request_id, message)(scope, receive, safe_send)

        if scope['path'] == '/predict':
            length = dict(scope['headers']).get(b'content-length')
            if length is not None:
                try:
                    if int(length) < 0:
                        raise ValueError
                    if int(length) > MAX_REQUEST_BYTES:
                        return await reject(413, 'Request exceeds the upload limit.')
                except ValueError:
                    return await reject(400, 'Invalid request length.')
            body = bytearray()
            while True:
                message = await receive()
                if message['type'] == 'http.disconnect':
                    return
                chunk = message.get('body', b'')
                if len(body) + len(chunk) > MAX_REQUEST_BYTES:
                    return await reject(413, 'Request exceeds the upload limit.')
                body.extend(chunk)
                if not message.get('more_body', False):
                    break
            replayed = False

            async def buffered_receive():
                nonlocal replayed
                if replayed:
                    return await receive()
                replayed = True
                return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
            downstream_receive = buffered_receive
        else:
            downstream_receive = receive
        try:
            await self.app(scope, downstream_receive, safe_send)
        except Exception:
            if started:
                raise
            await reject(500, 'The request could not be processed.')


def create_app(settings=None):
    settings = settings or Settings.from_environment()

    @asynccontextmanager
    async def lifespan(app):
        app.state.model_service = ModelService()
        await run_in_threadpool(app.state.model_service.load, settings.model_bundle)
        yield
        app.state.model_service.close()

    app = FastAPI(
        title='SkinDiseaseAI research API', version='0.1.0', lifespan=lifespan,
        description='Research screening API. Inference requires a verified evaluated hybrid export.',
        docs_url='/docs' if settings.docs_enabled else None, redoc_url=None,
        openapi_url='/openapi.json' if settings.docs_enabled else None,
    )
    app.add_middleware(RequestBoundary)
    app.mount('/static', StaticFiles(directory=FRONTEND / 'static'), name='static')

    @app.get('/', include_in_schema=False)
    def dashboard():
        return FileResponse(FRONTEND / 'templates' / 'index.html', headers=DASHBOARD_HEADERS)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, error):
        return error_response(error.status_code, request.state.request_id, str(error.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        return error_response(422, request.state.request_id, 'Invalid request parameters.')

    @app.get('/health', response_model=Health)
    def health(request: Request):
        return Health(model_ready=request.app.state.model_service.info.model_ready)

    @app.get('/model-info', response_model=ModelInfo)
    def model_info(request: Request):
        return request.app.state.model_service.info

    @app.post('/predict', response_model=Prediction,
              responses={status: {'model': ErrorResponse} for status in (413, 415, 422, 500, 503)},
              openapi_extra={'requestBody': {'required': True, 'content': {'multipart/form-data': {'schema': {
                  'type': 'object', 'required': ['image'], 'additionalProperties': False,
                  'properties': {'image': {'type': 'string', 'format': 'binary'}},
              }}}}})
    async def predict(request: Request):
        data = await read_upload(request)
        image, quality = await run_in_threadpool(decode_image, data)
        try:
            service = request.app.state.model_service
            if not service.info.model_ready:
                raise HTTPException(503, 'Inference is unavailable until a verified evaluated model is configured.')
            try:
                label, scores = await run_in_threadpool(service.predict, image)
                return Prediction(
                    request_id=request.state.request_id, model_version=service.info.model_version,
                    input_domain=service.info.input_domain, predicted_class=label, scores=scores,
                    quality=quality, limitations=LIMITATIONS,
                )
            except Exception:
                raise HTTPException(500, 'Model inference failed. No prediction is available.') from None
        finally:
            image.close()

    return app


app = create_app()
