"""Bounded, worker-local, idle-expiring memory. No chat or image is written to disk."""

import asyncio
from collections import OrderedDict, deque
from dataclasses import dataclass, field
import secrets
import time


COOKIE = 'skinai_chat'


@dataclass
class Session:
    token: str
    touched: float
    history: list = field(default_factory=list)
    prediction: dict | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    requests: deque = field(default_factory=deque)
    revoked: bool = False
    shared_context: bool = False
    context_revision: int = 0

    def erase(self):
        self.revoked = True
        self.history.clear()
        self.prediction = None


class SessionStore:
    def __init__(self, config, clock=time.monotonic):
        self.config = config
        self.clock = clock
        self.sessions = OrderedDict()

    def get(self, token=None):
        now = self.clock()
        for key, session in list(self.sessions.items()):
            if now - session.touched >= self.config.session_seconds:
                self.sessions.pop(key).erase()
        session = self.sessions.get(token)
        if session is None:
            while len(self.sessions) >= self.config.max_sessions:
                _, old = self.sessions.popitem(last=False)
                old.erase()
            session = Session(secrets.token_urlsafe(32), now)
            self.sessions[session.token] = session
        session.touched = now
        self.sessions.move_to_end(session.token)
        return session

    def delete(self, token):
        session = self.sessions.pop(token, None)
        if session:
            session.erase()

    def append(self, session, message, reply):
        session.history.extend([{'role': 'user', 'content': message}, {'role': 'assistant', 'content': reply}])
        session.history[:] = session.history[-2 * self.config.max_turns:]


def set_cookie(response, session, config):
    response.set_cookie(COOKIE, session.token, httponly=True, samesite='strict',
                        secure=config.secure_cookie, path='/')
