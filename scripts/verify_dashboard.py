"""Verify the local dashboard in installed Chrome/Edge using Python CDP, without Node.

All images are generated test patterns. Success/error fixtures are intercepted only in
this private browser session; they are never installed in the application or its model.
Run from the repository: python scripts/verify_dashboard.py
Install optional requirements/browser-test.txt first. Evidence stays in reports/local/.
"""

from __future__ import annotations

import argparse
import base64
from contextlib import suppress
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit
from urllib.request import urlopen

from PIL import Image
import websocket


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'reports' / 'local' / 'phase7-browser'


def wait_for(action, timeout=15):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        try:
            result = action()
            if result:
                return result
        except (OSError, ValueError, websocket.WebSocketException) as error:
            last = error
        time.sleep(0.05)
    raise AssertionError(f'Timed out waiting for browser/server condition ({type(last).__name__}).')


def read_json(url):
    with urlopen(url, timeout=2) as response:
        return json.load(response)


class Browser:
    def __init__(self, url):
        self.socket = websocket.create_connection(url, timeout=15, suppress_origin=True)
        self.sequence = 0
        self.replies = {}
        self.routes = {}
        self.held = []
        self.exceptions = []
        self.requests = []
        self.uploads = []

    def call(self, method, **params):
        self.sequence += 1
        number = self.sequence
        self.socket.send(json.dumps({'id': number, 'method': method, 'params': params}))
        while number not in self.replies:
            message = json.loads(self.socket.recv())
            if 'id' in message:
                self.replies[message['id']] = message
            elif message.get('method') == 'Runtime.exceptionThrown':
                self.exceptions.append(message['params']['exceptionDetails'])
            elif message.get('method') == 'Network.requestWillBeSent':
                request = message['params']['request']
                self.requests.append(request['url'])
                if request['method'] == 'POST':
                    self.uploads.append(request['url'])
            elif message.get('method') == 'Fetch.requestPaused':
                self.intercept(message['params'])
        response = self.replies.pop(number)
        if 'error' in response:
            raise RuntimeError(f'{method}: {response["error"]}')
        return response.get('result', {})

    def intercept(self, event):
        request_id = event['requestId']
        route = self.routes.get(urlsplit(event['request']['url']).path)
        if route == 'hold':
            self.held.append(request_id)
        elif route == 'fail':
            self.call('Fetch.failRequest', requestId=request_id, errorReason='ConnectionFailed')
        elif route:
            status, body = route
            self.call('Fetch.fulfillRequest', requestId=request_id, responseCode=status,
                      responseHeaders=[{'name': 'Content-Type', 'value': 'application/json'}],
                      body=base64.b64encode(json.dumps(body).encode()).decode())
        else:
            self.call('Fetch.continueRequest', requestId=request_id)

    def evaluate(self, expression):
        result = self.call('Runtime.evaluate', expression=expression, returnByValue=True, awaitPromise=True)
        if 'exceptionDetails' in result:
            raise AssertionError(result['exceptionDetails'])
        return result.get('result', {}).get('value')

    def wait(self, expression):
        return wait_for(lambda: self.evaluate(expression))

    def click(self, element):
        self.evaluate(f'document.getElementById({json.dumps(element)}).click()')

    def upload(self, path):
        node = self.call('DOM.getDocument')['root']['nodeId']
        field = self.call('DOM.querySelector', nodeId=node, selector='#image-input')['nodeId']
        self.call('DOM.setFileInputFiles', nodeId=field, files=[str(path)])

    def screenshot(self, name):
        data = self.call('Page.captureScreenshot', format='png', captureBeyondViewport=False)['data']
        (OUTPUT / name).write_bytes(base64.b64decode(data))

    def release_held(self):
        for request_id in self.held:
            with suppress(RuntimeError):
                self.call('Fetch.continueRequest', requestId=request_id)
        self.held.clear()


def run_checks(browser, base, temporary):
    checks = []

    def check(name, expression):
        assert browser.evaluate(expression), name
        checks.append(name)

    image = temporary / 'synthetic-test-pattern.png'
    Image.frombytes('RGB', (256, 256), os.urandom(256 * 256 * 3)).save(image)
    tiny = temporary / 'too-small.png'
    Image.new('RGB', (64, 64), 'gray').save(tiny)
    invalid = temporary / 'not-an-image.png'
    invalid.write_bytes(b'TEST_FIXTURE_NOT_AN_IMAGE')
    oversized = temporary / 'too-large.png'
    oversized.write_bytes(b'x' * (10 * 1024 * 1024 + 1))
    corrupt = temporary / 'truncated.png'
    corrupt.write_bytes(b'\x89PNG\r\n\x1a\nTEST_FIXTURE_TRUNCATED')
    animated = temporary / 'animated.png'
    Image.new('RGB', (128, 128), 'gray').save(animated, save_all=True,
        append_images=[Image.new('RGB', (128, 128), 'white')], duration=100, loop=0)

    browser.call('Page.enable')
    browser.call('Runtime.enable')
    browser.call('Network.enable')
    browser.call('Emulation.setDeviceMetricsOverride', width=1440, height=1100, deviceScaleFactor=1, mobile=False)
    browser.call('Page.addScriptToEvaluateOnNewDocument', source='''
        window.__testProgress = [];
        const send = XMLHttpRequest.prototype.send;
        XMLHttpRequest.prototype.send = function(body) {
          this.upload.addEventListener('progress', e => window.__testProgress.push({loaded:e.loaded,total:e.total}));
          return send.call(this, body);
        };
    ''')
    browser.call('Page.navigate', url=base)
    browser.wait("document.getElementById('availability-title')?.textContent === 'Model not available yet'")
    check('initial no-model state without predictions', "document.getElementById('prediction').hidden && document.getElementById('analyze').disabled")
    check('desktop has no horizontal overflow', 'document.documentElement.scrollWidth <= innerWidth')
    browser.screenshot('desktop.png')
    browser.call('Input.dispatchKeyEvent', type='keyDown', key='Tab', code='Tab', windowsVirtualKeyCode=9)
    browser.call('Input.dispatchKeyEvent', type='keyUp', key='Tab', code='Tab', windowsVirtualKeyCode=9)
    check('keyboard skip link is first focus target', "document.activeElement.className === 'skip-link'")
    browser.evaluate('document.activeElement.blur()')
    for width in (390, 320, 768, 1024):
        browser.call('Emulation.setDeviceMetricsOverride', width=width, height=844, deviceScaleFactor=1, mobile=width < 640)
        check(f'layout fits {width}px viewport', 'document.documentElement.scrollWidth <= innerWidth')
        if width == 390:
            browser.screenshot('mobile.png')
    browser.call('Emulation.setDeviceMetricsOverride', width=1440, height=1100, deviceScaleFactor=1, mobile=False)

    for path, expected in ((invalid, 'Unsupported file'), (tiny, 'at least 128'),
                           (oversized, 'exceeds 10 MiB'), (corrupt, 'could not be opened')):
        browser.upload(path)
        browser.wait("!document.getElementById('file-error').hidden")
        check(f'client rejects {path.name}', f"document.getElementById('file-error').textContent.includes({json.dumps(expected)}) && document.getElementById('analyze').disabled")

    browser.upload(image)
    browser.wait("!document.getElementById('preview').hidden")
    check('preview requires consent and sends no image', "document.getElementById('analyze').disabled && !document.getElementById('consent').checked")
    assert not browser.uploads, 'Image sent before consent'
    browser.click('consent')
    browser.upload(tiny)
    browser.wait("!document.getElementById('file-error').hidden")
    check('replacement invalidates prior image and consent', "document.getElementById('preview').hidden && !document.getElementById('consent').checked && document.getElementById('analyze').disabled")
    browser.upload(image)
    browser.wait("!document.getElementById('preview').hidden")
    browser.evaluate("window.__oldPreviewUrl = document.getElementById('preview-image').src")
    browser.click('consent')
    check('consent enables submission', "!document.getElementById('analyze').disabled")
    browser.click('remove-image')
    check('remove clears preview, consent and results', "document.getElementById('preview').hidden && !document.getElementById('consent').checked && document.getElementById('analyze').disabled && !document.getElementById('preview-image').hasAttribute('src')")
    check('removed blob URL is released', "fetch(window.__oldPreviewUrl).then(()=>false,()=>true)")

    browser.evaluate('''(() => {
      const files = new DataTransfer();
      files.items.add(new File(['TEST_FIXTURE'], 'first.png', {type:'image/png'}));
      files.items.add(new File(['TEST_FIXTURE'], 'second.png', {type:'image/png'}));
      document.getElementById('drop-zone').dispatchEvent(new DragEvent('drop', {dataTransfer:files,bubbles:true,cancelable:true}));
    })()''')
    check('multiple dropped files are rejected', "document.getElementById('file-error').textContent.includes('one image') && document.getElementById('analyze').disabled")
    pattern = base64.b64encode(image.read_bytes()).decode()
    browser.evaluate('''(() => {
      const bytes = Uint8Array.from(atob(%s), c => c.charCodeAt(0));
      const files = new DataTransfer();
      files.items.add(new File([bytes], '<b>TEST_FIXTURE_FILENAME</b>.png', {type:'image/png'}));
      document.getElementById('drop-zone').dispatchEvent(new DragEvent('drop', {dataTransfer:files,bubbles:true,cancelable:true}));
    })()''' % json.dumps(pattern))
    browser.wait("!document.getElementById('preview').hidden")
    check('valid drop previews literal filename without markup', "document.getElementById('file-name').textContent === '<b>TEST_FIXTURE_FILENAME</b>.png' && !document.querySelector('#file-name b') && document.getElementById('analyze').disabled")

    browser.upload(image)
    browser.wait("!document.getElementById('preview').hidden")
    browser.click('consent')
    browser.call('Network.emulateNetworkConditions', offline=False, latency=0, downloadThroughput=1048576, uploadThroughput=100000)
    browser.click('analyze')
    browser.wait("document.getElementById('feedback-title').textContent === 'Model not available yet' && !document.getElementById('request-feedback').hidden")
    browser.wait("document.getElementById('results').getAttribute('aria-busy') === 'false'")
    browser.call('Network.emulateNetworkConditions', offline=False, latency=0, downloadThroughput=-1, uploadThroughput=-1)
    check('real backend 503 displays request ID without scores', "document.getElementById('request-id').textContent.length > 32 && document.getElementById('prediction').hidden && document.getElementById('class-scores').children.length === 0")
    check('request outcome receives keyboard focus', "document.activeElement.id === 'request-feedback'")
    check('actual upload progress events observed', 'window.__testProgress.some(e => e.total > 0 && e.loaded > 0)')
    assert browser.uploads == [base + 'predict'], browser.uploads
    checks.append('exactly one real image request after consent')

    browser.upload(animated)
    browser.wait("document.getElementById('file-name').textContent === 'animated.png'")
    browser.click('consent')
    browser.click('analyze')
    browser.wait("document.getElementById('feedback-title').textContent === 'Please check your image'")
    check('server rejects animated image in actual upload', "document.getElementById('feedback-copy').textContent.includes('Animated') && document.getElementById('prediction').hidden")

    browser.upload(image)
    browser.wait("document.getElementById('file-name').textContent === 'synthetic-test-pattern.png'")
    browser.click('consent')
    browser.call('Fetch.enable', patterns=[{'urlPattern': base + path} for path in ('predict', 'health', 'model-info')])
    browser.routes['/predict'] = 'hold'
    browser.click('analyze')
    browser.wait("document.getElementById('results').getAttribute('aria-busy') === 'true'")
    check('in-flight request disables selection and exposes cancellation', "document.getElementById('image-input').disabled && document.getElementById('consent').disabled && !document.getElementById('cancel-request').hidden && !document.getElementById('request-progress').hidden")
    browser.click('cancel-request')
    browser.wait("document.getElementById('feedback-title').textContent === 'Request cancelled'")
    check('cancel restores controls without predictions', "!document.getElementById('image-input').disabled && document.getElementById('prediction').hidden")
    browser.release_held()

    # Speed up only the browser test's timeout, without changing application code.
    browser.evaluate('''(() => {
      window.__testTimeoutDescriptor = Object.getOwnPropertyDescriptor(XMLHttpRequest.prototype, 'timeout');
      const original = window.__testTimeoutDescriptor;
      Object.defineProperty(XMLHttpRequest.prototype, 'timeout', {...original, set(value) { original.set.call(this, 100); }});
    })()''')
    browser.click('analyze')
    browser.wait("document.getElementById('feedback-title').textContent === 'The request timed out'")
    check('timeout restores controls without fabricated result', "!document.getElementById('image-input').disabled && document.getElementById('prediction').hidden")
    browser.evaluate("void Object.defineProperty(XMLHttpRequest.prototype, 'timeout', window.__testTimeoutDescriptor)")
    browser.release_held()

    browser.routes['/predict'] = 'fail'
    browser.click('analyze')
    browser.wait("document.getElementById('feedback-title').textContent === 'Could not reach the service'")
    checks.append('network failure gives retryable feedback without prediction')
    browser.routes['/predict'] = (500, {'request_id': 'TEST_FIXTURE_ERROR', 'error': {'message': 'TEST_FIXTURE_SAFE_ERROR'}})
    browser.click('analyze')
    browser.wait("document.getElementById('feedback-title').textContent === 'Screening could not finish'")
    check('safe server error rendering', "document.getElementById('feedback-copy').textContent === 'TEST_FIXTURE_SAFE_ERROR'")

    fixture_label = {'index': 0, 'code': 'fixture', 'name': '<b>TEST_FIXTURE_ONLY</b>'}
    fixture = {'request_id': 'TEST_FIXTURE_ONLY', 'model_version': 'TEST_FIXTURE_ONLY',
        'input_domain': 'SYNTHETIC_BROWSER_FIXTURE_ONLY', 'predicted_class': fixture_label,
        'scores': [{**fixture_label, 'score': 1.0}], 'score_type': 'uncalibrated_softmax', 'calibrated': False,
        'explanation': {'available': False, 'reason': 'TEST_FIXTURE: explanation unavailable'},
        'quality': {'warnings': ['TEST_FIXTURE: not research evidence']},
        'limitations': ['TEST_FIXTURE_ONLY. No trained prediction.']}
    browser.routes['/predict'] = (200, fixture)
    browser.click('analyze')
    browser.wait("!document.getElementById('prediction').hidden")
    check('isolated success fixture renders literal safe text and scores', "document.getElementById('predicted-class').textContent === '<b>TEST_FIXTURE_ONLY</b>' && !document.querySelector('#predicted-class b') && document.getElementById('class-scores').children.length === 1 && document.getElementById('explanation-copy').textContent.includes('unavailable')")
    check('success result receives keyboard focus', "document.activeElement.id === 'predicted-class'")
    browser.routes['/predict'] = (200, {'unexpected': 'TEST_FIXTURE_MALFORMED'})
    browser.click('analyze')
    browser.wait("document.getElementById('feedback-title').textContent === 'The response could not be verified'")
    check('malformed response clears old result', "document.getElementById('prediction').hidden && document.getElementById('class-scores').children.length === 0")

    browser.routes['/health'] = (200, {'status': 'ok', 'model_ready': True})
    browser.routes['/model-info'] = (200, {'model_ready': True, 'model_version': 'TEST_FIXTURE_ONLY', 'architecture': 'TEST_FIXTURE_ONLY'})
    browser.click('refresh-status')
    browser.wait("document.getElementById('availability').classList.contains('ready')")
    check('isolated ready metadata uses loaded model information', "document.getElementById('model-architecture').textContent === 'TEST_FIXTURE_ONLY'")
    browser.routes.pop('/predict')
    browser.click('analyze')
    browser.wait("document.getElementById('feedback-title').textContent === 'Model not available yet'")
    check('503 clears stale ready model metadata', "document.getElementById('model-architecture').textContent === 'Not available' && !document.getElementById('availability').classList.contains('ready')")
    browser.routes.pop('/health')
    browser.routes.pop('/model-info')

    browser.routes['/health'] = 'fail'
    browser.click('refresh-status')
    browser.wait("document.getElementById('availability-title').textContent === 'Screening service is unreachable'")
    checks.append('readiness network failure is distinct from unavailable model')
    browser.routes.pop('/health')
    browser.click('refresh-status')
    browser.wait("document.getElementById('availability-title').textContent === 'Model not available yet'")
    checks.append('readiness refresh recovers')
    browser.call('Fetch.disable')
    browser.routes.clear()
    browser.click('remove-image')
    check('remove releases hidden result text as well as preview', "document.getElementById('predicted-class').textContent === '' && document.getElementById('feedback-title').textContent === ''")
    browser.click('refresh-status')
    browser.wait("!document.getElementById('refresh-status').disabled")
    check('no persisted screening data', 'localStorage.length === 0 && sessionStorage.length === 0 && document.cookie === ""')
    assert not browser.exceptions, browser.exceptions
    checks.append('no runtime JavaScript exceptions')
    assert all(url.startswith(base) or url.startswith('blob:' + base) for url in browser.requests), 'Unexpected external request'
    checks.append('dashboard uses only same-origin requests')
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', type=Path, help='Installed Chrome/Edge executable')
    args = parser.parse_args()
    candidates = [args.browser, Path('C:/Program Files/Google/Chrome/Application/chrome.exe'),
        Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')]
    browser_path = next((path for path in candidates if path and path.is_file()), None)
    if not browser_path:
        parser.error('Pass --browser with an installed Chrome/Edge executable.')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='run-', dir=OUTPUT)).resolve()
    server = chrome = browser = None
    log = (OUTPUT / 'process.log').open('w', encoding='utf-8')
    try:
        with socket.socket() as reservation:
            reservation.bind(('127.0.0.1', 0))
            port = reservation.getsockname()[1]
        base = f'http://127.0.0.1:{port}/'
        environment = os.environ.copy()
        environment.pop('SKINAI_MODEL_BUNDLE', None)
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.app.main:app',
            '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env=environment,
            stdout=log, stderr=log, creationflags=flags)
        wait_for(lambda: server.poll() is None and read_json(base + 'health') == {'status': 'ok', 'model_ready': False})
        profile = temporary / 'chrome-profile'
        chrome = subprocess.Popen([str(browser_path), '--headless=new', '--remote-debugging-port=0',
            f'--user-data-dir={profile}', '--no-first-run', '--no-default-browser-check',
            '--disable-background-networking', '--disable-extensions', 'about:blank'],
            stdout=log, stderr=log, creationflags=flags)
        active = profile / 'DevToolsActivePort'
        debug_port = wait_for(lambda: active.read_text().splitlines()[0] if active.is_file() else None)
        targets = read_json(f'http://127.0.0.1:{debug_port}/json/list')
        target = next(item for item in targets if item['type'] == 'page')
        browser = Browser(target['webSocketDebuggerUrl'])
        checks = run_checks(browser, base, temporary)
        evidence = {'browser': browser.call('Browser.getVersion')['product'],
            'checks': checks, 'passed': len(checks), 'real_model_tested': False,
            'fixture_scope': 'Browser-intercepted, explicitly synthetic. No production model configured.'}
        (OUTPUT / 'verification.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(evidence, indent=2))
    finally:
        if browser:
            with suppress(Exception):
                browser.call('Browser.close')
            browser.socket.close()
        for process in (chrome, server):
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=8)
        log.close()
        # Only remove the unique run directory after checking its resolved workspace boundary.
        if temporary.is_relative_to(OUTPUT.resolve()) and temporary.name.startswith('run-'):
            with suppress(OSError):
                shutil.rmtree(temporary)


if __name__ == '__main__':
    main()
