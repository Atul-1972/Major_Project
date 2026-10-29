"""Observe trusted prediction responses without changing the classifier or predict route."""

from contextlib import suppress

from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ..schemas import Prediction
from .routes import ChatService, build_router
from .state import COOKIE, set_cookie


class ChatBoundary:
    def __init__(self, app, service):
        self.app = app
        self.service = service

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        if scope['path'] == '/chat' and scope['method'] == 'POST':
            data = bytearray()
            while True:
                chunk = await receive()
                if chunk['type'] == 'http.disconnect':
                    return
                data.extend(chunk.get('body', b''))
                if len(data) > 16384:
                    return await JSONResponse(status_code=413, content={
                        'request_id': scope.get('state', {}).get('request_id', ''),
                        'error': {'code': 'chat_too_large', 'message': 'Chat request exceeds the size limit.'}
                    })(scope, receive, send)
                if not chunk.get('more_body', False):
                    break
            done = False

            async def replay():
                nonlocal done
                if done:
                    return await receive()
                done = True
                return {'type': 'http.request', 'body': bytes(data), 'more_body': False}
            return await self.app(scope, replay, send)

        if scope['path'] != '/predict' or scope['method'] != 'POST':
            return await self.app(scope, receive, send)
        session = self.service.store.get(Request(scope).cookies.get(COOKIE))
        # Prediction never waits for a slow chat request. Revision checks reject stale replies.
        session.context_revision += 1
        revision = session.context_revision
        session.prediction = None
        session.history.clear()
        captured = bytearray()
        status = 0

        async def capture(message):
            nonlocal status
            if message['type'] == 'http.response.start':
                status = message['status']
                cookie = Response()
                set_cookie(cookie, session, self.service.config)
                message = {**message, 'headers': list(message.get('headers', [])) +
                           [(key, value) for key, value in cookie.raw_headers if key == b'set-cookie']}
            elif message['type'] == 'http.response.body' and status == 200:
                if len(captured) <= 131072:
                    captured.extend(message.get('body', b'')[:131073 - len(captured)])
                if len(captured) <= 131072 and not message.get('more_body', False):
                    with suppress(ValidationError, ValueError, StopIteration):
                        result = Prediction.model_validate_json(captured)
                        score = next(item.score for item in result.scores if item.code == result.predicted_class.code)
                        if not session.revoked and session.context_revision == revision:
                            session.prediction = {'code': result.predicted_class.code, 'name': result.predicted_class.name,
                                'model_score': score, 'score_type': result.score_type,
                                'model_version': result.model_version, 'request_id': result.request_id,
                                'not_a_diagnosis': True}
            await send(message)
        await self.app(scope, receive, capture)


def install_chat(app, config):
    service = ChatService(config)
    app.state.chat_service = service
    app.include_router(build_router(service))
    if config.enabled:
        app.add_middleware(ChatBoundary, service=service)
