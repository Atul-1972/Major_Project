"""Dashboard delivery must preserve the API and expose only intended public assets."""

from html.parser import HTMLParser

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.settings import Settings


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ('href', 'src') and value and value.startswith('/static/'):
                self.paths.add(value)


def test_dashboard_delivers_referenced_assets_and_safe_headers():
    with TestClient(create_app(Settings())) as client:
        response = client.get('/')
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('text/html')
        assert response.headers['cache-control'] == 'no-store'
        assert response.headers['referrer-policy'] == 'no-referrer'
        assert response.headers['x-content-type-options'] == 'nosniff'
        policy = response.headers['content-security-policy']
        assert "connect-src 'self'" in policy and "img-src 'self' blob:" in policy
        assert "frame-ancestors 'none'" in policy and 'unsafe-inline' not in policy
        assets = Assets()
        assets.feed(response.text)
        assert len(assets.paths) == 3
        for path in assets.paths:
            asset = client.get(path)
            assert asset.status_code == 200 and asset.content
        assert client.get('/health').json() == {'status': 'ok', 'model_ready': False}
        assert client.get('/model-info').json()['classes'] == []
        assert '/predict' in client.get('/openapi.json').json()['paths']


def test_public_asset_mount_does_not_expose_source_or_directory_listing():
    with TestClient(create_app(Settings())) as client:
        for path in ('/static/', '/static/missing.js', '/static/%2e%2e/templates/index.html',
                     '/static/..%2f..%2fbackend/app/main.py', '/data/ham10000/metadata.csv',
                     '/frontend/templates/index.html', '/.project/state.json'):
            assert client.get(path).status_code == 404, path


def test_dashboard_works_with_api_docs_disabled_and_another_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with TestClient(create_app(Settings(docs_enabled=False))) as client:
        assert client.get('/').status_code == 200
        assert client.get('/static/dashboard.js').status_code == 200
        assert client.get('/docs').status_code == 404
        assert client.get('/openapi.json').status_code == 404
