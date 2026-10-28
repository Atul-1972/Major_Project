"""HTTP checks use generated images and explicit test doubles, never research results."""

from io import BytesIO
import tempfile

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from backend.app.main import create_app
from backend.app.inference import ModelService
from backend.app.schemas import ClassLabel, ClassScore, ModelInfo
from backend.app.settings import MAX_IMAGE_BYTES, MAX_REQUEST_BYTES, Settings


def image_bytes(fmt='PNG', size=(128, 160), **kwargs):
    stream = BytesIO()
    Image.new('RGB', size, (120, 100, 90)).save(stream, format=fmt, **kwargs)
    return stream.getvalue()


@pytest.fixture
def client():
    with TestClient(create_app(Settings())) as result:
        yield result


def upload(client, data, filename='image.png', mime='image/png'):
    return client.post('/predict', files={'image': (filename, data, mime)})


def assert_error(response, status):
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {'request_id', 'error'}
    assert body['request_id'] == response.headers['x-request-id']
    assert response.headers['cache-control'] == 'no-store'
    assert len(body['request_id']) == 32
    assert 'scores' not in body and 'predicted_class' not in body
    return body


def test_unconfigured_liveness_metadata_and_no_fallback(client):
    assert client.get('/health').json() == {'status': 'ok', 'model_ready': False}
    info = client.get('/model-info').json()
    assert info['model_ready'] is False
    assert info['classes'] == [] and info['model_version'] is None
    assert info['score_type'] is None and info['calibrated'] is False
    assert info['explanation_available'] is False
    first = upload(client, image_bytes())
    second = upload(client, image_bytes('JPEG'))
    assert_error(first, 503)
    assert_error(second, 503)
    assert first.headers['x-request-id'] != second.headers['x-request-id']


def test_invalid_bundle_starts_live_but_stays_unavailable(tmp_path):
    private_path = tmp_path / 'private-model'
    with TestClient(create_app(Settings(model_bundle=private_path))) as client:
        assert client.get('/health').json()['model_ready'] is False
        assert client.get('/model-info').json()['unavailable_reason'] == 'model_bundle_rejected'
        result = upload(client, image_bytes())
        assert_error(result, 503)
        assert str(private_path) not in result.text


@pytest.mark.parametrize('data,status', [
    (b'', 422), (b'not an image', 422),
    (image_bytes('GIF'), 415), (image_bytes('BMP'), 415),
    (image_bytes(size=(127, 160)), 422),
    (image_bytes()[:60], 422),
    (b'x' * (MAX_IMAGE_BYTES + 1), 413),
], ids=['empty', 'unreadable', 'gif', 'bmp', 'too_small', 'truncated', 'encoded_limit'])
def test_invalid_images_are_rejected_even_without_weights(client, data, status):
    assert_error(upload(client, data), status)


def test_decoded_format_overrides_filename_and_mime(client):
    assert_error(upload(client, image_bytes('JPEG'), 'wrong.txt', 'text/plain'), 503)
    assert_error(upload(client, b'not jpeg', 'image.jpg', 'image/jpeg'), 422)


def test_animated_png_is_rejected(client):
    stream = BytesIO()
    first = Image.new('RGB', (128, 128), 'red')
    second = Image.new('RGB', (128, 128), 'blue')
    first.save(stream, 'PNG', save_all=True, append_images=[second], duration=50, loop=0)
    assert_error(upload(client, stream.getvalue()), 422)


def test_pixel_cap_is_checked_before_decode(client, monkeypatch):
    from backend.app import uploads
    monkeypatch.setattr(uploads, 'MAX_PIXELS', 20_000)
    assert_error(upload(client, image_bytes(size=(150, 150))), 413)


def test_missing_duplicate_wrong_field_and_extra_fields(client):
    for response in (
        client.post('/predict'),
        client.post('/predict', files={'wrong': ('x.png', image_bytes())}),
        client.post('/predict', files=[('image', ('a.png', image_bytes())), ('image', ('b.png', image_bytes()))]),
        client.post('/predict', files={'image': ('x.png', image_bytes())}, data={'note': 'private content'}),
        client.post('/predict', data={'image': 'not a file'}),
        client.post('/predict', content=b'bad multipart', headers={'content-type': 'multipart/form-data'}),
    ):
        assert_error(response, 422)
        assert 'private content' not in response.text


def test_actual_chunked_size_is_capped_without_content_length(client):
    def chunks():
        for _ in range(12):
            yield b'x' * (1024 * 1024)
    result = client.post('/predict', content=chunks(), headers={'content-type': 'multipart/form-data; boundary=x'})
    assert_error(result, 413)


def test_declared_oversize_and_invalid_length(client):
    assert_error(client.post('/predict', content=b'', headers={'content-length': str(MAX_REQUEST_BYTES + 1)}), 413)
    assert_error(client.post('/predict', content=b'', headers={'content-length': 'invalid'}), 400)


def test_uploads_never_roll_to_disk_and_close(client, monkeypatch):
    from starlette import formparsers
    handles = []
    original = tempfile.SpooledTemporaryFile

    def record(*args, **kwargs):
        handle = original(*args, **kwargs)
        handles.append(handle)
        return handle

    monkeypatch.setattr(formparsers, 'SpooledTemporaryFile', record)
    # More than Starlette's default 1 MiB spool threshold; parser must remain in memory.
    payload = image_bytes() + b'\0' * (2 * 1024 * 1024)
    assert_error(upload(client, payload), 503)
    assert handles and all(handle.closed and not handle._rolled for handle in handles)


def test_openapi_has_binary_upload_contract_and_docs_toggle(client):
    assert client.get('/docs').status_code == 200
    schema = client.get('/openapi.json').json()
    endpoint = schema['paths']['/predict']['post']
    assert endpoint['requestBody']['content']['multipart/form-data']['schema']['required'] == ['image']
    assert '503' in endpoint['responses']
    with TestClient(create_app(Settings(docs_enabled=False))) as private_client:
        assert private_client.get('/docs').status_code == 404
        assert private_client.get('/openapi.json').status_code == 404


class ExplicitHTTPFixture:
    """Injected only into this test; these scores are not model predictions."""
    def __init__(self):
        self.info = ModelInfo(
            model_ready=True, model_version='TEST_FIXTURE_ONLY', architecture='TEST_FIXTURE_ONLY',
            input_domain='SYNTHETIC_HTTP_TEST_ONLY', score_type='uncalibrated_softmax',
            classes=[ClassLabel(index=0, code='fixture', name='Synthetic HTTP fixture')],
        )

    def predict(self, image):
        assert image.mode == 'RGB' and not image.info
        return self.info.classes[0], [ClassScore(**self.info.classes[0].model_dump(), score=1.0)]

    def close(self):
        pass


def test_success_schema_with_explicit_http_fixture_and_exif_orientation(client):
    client.app.state.model_service = ExplicitHTTPFixture()
    exif = Image.Exif()
    exif[274] = 6
    exif[270] = 'PRIVATE_EXIF_TEST_STRING'
    result = upload(client, image_bytes('JPEG', size=(128, 160), exif=exif))
    assert result.status_code == 200, result.text
    body = result.json()
    assert body['model_version'] == 'TEST_FIXTURE_ONLY'
    assert (body['quality']['width'], body['quality']['height']) == (160, 128)
    assert body['explanation']['available'] is False
    assert body['calibrated'] is False
    assert 'PRIVATE_EXIF_TEST_STRING' not in result.text
    assert body['request_id'] == result.headers['x-request-id']
    assert body['limitations'] and body['quality']['warnings']


def test_inference_failure_does_not_leak_exception(client):
    fixture = ExplicitHTTPFixture()
    def fail(image):
        raise RuntimeError('PRIVATE_PATH_OR_MODEL_DETAILS')
    fixture.predict = fail
    client.app.state.model_service = fixture
    result = upload(client, image_bytes())
    assert_error(result, 500)
    assert 'PRIVATE_PATH_OR_MODEL_DETAILS' not in result.text


def test_startup_load_occurs_once_per_lifespan(monkeypatch):
    calls = []
    original = ModelService.load
    def record(service, bundle):
        calls.append(bundle)
        return original(service, bundle)
    monkeypatch.setattr(ModelService, 'load', record)
    with TestClient(create_app(Settings())) as client:
        client.get('/health')
        client.get('/model-info')
        upload(client, image_bytes())
        assert calls == [None]
