"""Bounded session-based chatbot routes; the client cannot submit prediction/history objects."""

import asyncio
import re
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from .knowledge import NOTES, retrieve, sources
from .provider import LLMProvider, ProviderUnavailable
from .safety import blocked_reply, safety_reply, triage, unsafe_output
from .state import COOKIE, SessionStore, set_cookie


class ChatInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message: str = Field(min_length=1, max_length=1500)
    language: Literal['auto', 'en', 'hi'] = 'auto'
    consent: Literal[True]
    include_prediction: bool = False


class ChatService:
    def __init__(self, config, provider=None):
        self.config = config
        self.store = SessionStore(config)
        self.provider = provider or LLMProvider(config)
        self.capacity = asyncio.Semaphore(4)

    async def reply(self, session, body):
        if session.lock.locked():
            raise HTTPException(429, 'Another request is in progress. Please wait.')
        async with session.lock:
            now = self.store.clock()
            while session.requests and now - session.requests[0] > 60:
                session.requests.popleft()
            if len(session.requests) >= 12:
                raise HTTPException(429, 'Please wait before sending more chat messages.')
            session.requests.append(now)
            message = body.message.strip()
            if not message:
                raise HTTPException(422, 'Enter a question before sending.')
            language = body.language
            if language == 'auto':
                language = 'hi' if re.search(r'[\u0900-\u097f]', message) else 'en'
            # Revoke previously shared screening context when the sharing choice changes.
            if session.shared_context != body.include_prediction:
                session.history.clear()
            session.shared_context = body.include_prediction
            prediction = dict(session.prediction) if body.include_prediction and session.prediction else None
            revision = session.context_revision
            level = triage(message)
            if level:
                notes = [note for note in NOTES if note.id in
                         (('anaphylaxis', 'blistering') if level == 'emergency' else ('infection',))]
                result = {'reply': safety_reply(level, language), 'mode': 'safety', 'urgency': level,
                          'sources': sources(notes), 'prediction_used': False, 'language': language}
            else:
                if not self.config.ready:
                    raise HTTPException(503, 'The AI chat provider is not configured. No AI answer is available.')
                if self.capacity.locked():
                    raise HTTPException(429, 'The chat service is busy. Please try again shortly.')
                notes = retrieve(message, prediction)
                try:
                    async with self.capacity:
                        answer = await asyncio.wait_for(self.provider.generate(
                            list(session.history), message, language, prediction, notes), self.config.timeout_seconds)
                except (ProviderUnavailable, asyncio.TimeoutError):
                    raise HTTPException(503, 'The AI provider could not answer. Please try again later.') from None
                raw = answer['answer'] + '\n' + answer['follow_up']
                if unsafe_output(raw):
                    result = {'reply': blocked_reply(language), 'mode': 'safety', 'urgency': 'routine',
                              'sources': [], 'prediction_used': False, 'language': language}
                else:
                    allowed = {note.id for note in notes}
                    selected = set(answer['source_ids']) & allowed
                    cited = [note for note in notes if note.id in selected]
                    # An answer with no valid grounding reference fails closed rather than inventing citations.
                    if not cited:
                        raise HTTPException(503, 'The AI answer could not be grounded in the reference library. Try a skin-care question.')
                    disclaimer = ('केवल सामान्य जानकारी; यह निदान नहीं है।' if language == 'hi' else
                                  'General information only; this is not a diagnosis.')
                    intro = ''
                    if body.include_prediction:
                        if prediction:
                            intro = (f"स्क्रीनिंग में '{prediction['name']}' श्रेणी सुझाई गई है; यह पक्का निदान नहीं है।\n\n" if language == 'hi' else
                                     f"The screening suggested '{prediction['name']}'; this is not a confirmed diagnosis.\n\n")
                        else:
                            intro = ('इस सत्र में कोई जाँचा गया बैकएंड स्क्रीनिंग परिणाम उपलब्ध नहीं है।\n\n' if language == 'hi' else
                                     'No verified backend screening result is available in this session.\n\n')
                    result = {'reply': intro + raw.strip() + '\n\n' + disclaimer, 'mode': 'llm', 'urgency': 'routine',
                              'sources': sources(cited), 'prediction_used': prediction is not None, 'language': language}
            if session.revoked or session.context_revision != revision:
                raise HTTPException(409, 'This chat was cleared or expired. Please start again.')
            self.store.append(session, message, result['reply'])
            return result


def require_same_origin(request):
    origin = request.headers.get('origin')
    expected = str(request.base_url).rstrip('/')
    if request.headers.get('x-skinai-chat') != '1' or (origin and origin != expected):
        raise HTTPException(403, 'Use the chat from this website.')
    if request.headers.get('sec-fetch-site') == 'cross-site':
        raise HTTPException(403, 'Use the chat from this website.')


def build_router(service):
    router = APIRouter(tags=['chat'])

    @router.get('/chat/status')
    def status():
        return {'enabled': service.config.enabled, 'configured': service.config.ready if service.config.enabled else False,
                'provider': service.config.provider if service.config.enabled else None,
                'history_seconds': service.config.session_seconds}

    if not service.config.enabled:
        return router

    @router.get('/chat/session')
    async def session_info(request: Request, response: Response):
        require_same_origin(request)
        session = service.store.get(request.cookies.get(COOKIE))
        set_cookie(response, session, service.config)
        return {'messages': list(session.history), 'prediction_available': session.prediction is not None}

    @router.delete('/chat/session')
    async def clear(request: Request, response: Response):
        require_same_origin(request)
        service.store.delete(request.cookies.get(COOKIE))
        response.delete_cookie(COOKIE, path='/', httponly=True, samesite='strict', secure=service.config.secure_cookie)
        return {'cleared': True}

    @router.delete('/chat/context')
    async def clear_context(request: Request):
        require_same_origin(request)
        session = service.store.sessions.get(request.cookies.get(COOKIE))
        if session:
            session.context_revision += 1
            session.prediction = None
            session.history.clear()
        return {'cleared': True}

    @router.post('/chat')
    async def chat(body: ChatInput, request: Request, response: Response):
        require_same_origin(request)
        session = service.store.get(request.cookies.get(COOKIE))
        set_cookie(response, session, service.config)
        result = await service.reply(session, body)
        return {'request_id': request.state.request_id, **result}

    return router
