"""Server-only LLM configuration. Secrets never enter public settings or prompts."""

from dataclasses import dataclass, field
import os
from urllib.parse import urlsplit


@dataclass(frozen=True)
class ChatConfig:
    enabled: bool = True
    provider: str = 'openai'
    model: str = ''
    api_key: str = field(default='', repr=False)
    base_url: str = 'https://api.openai.com/v1'
    secure_cookie: bool = False
    session_seconds: int = 1200
    max_sessions: int = 128
    max_turns: int = 10
    timeout_seconds: float = 30

    @property
    def ready(self):
        try:
            parsed = urlsplit(self.base_url)
            parsed.port
        except ValueError:
            return False
        local = parsed.hostname in ('localhost', '127.0.0.1', '::1')
        valid = parsed.hostname and (parsed.scheme == 'https' or (parsed.scheme == 'http' and local)) and not (
            parsed.username or parsed.password or parsed.query or parsed.fragment)
        return bool(valid and self.model and self.provider in ('openai', 'openai_compatible') and
                    (self.api_key or (self.provider == 'openai_compatible' and local)) and
                    (self.provider != 'openai' or self.base_url.rstrip('/') == 'https://api.openai.com/v1'))

    @classmethod
    def from_environment(cls):
        return cls(
            enabled=os.environ.get('SKINAI_CHAT_ENABLED', '1') == '1',
            provider=os.environ.get('SKINAI_CHAT_PROVIDER', 'openai'),
            model=os.environ.get('SKINAI_CHAT_MODEL', '').strip(),
            api_key=os.environ.get('SKINAI_CHAT_API_KEY', '') or os.environ.get('OPENAI_API_KEY', ''),
            base_url=os.environ.get('SKINAI_CHAT_BASE_URL', 'https://api.openai.com/v1').rstrip('/'),
            secure_cookie=os.environ.get('SKINAI_CHAT_SECURE_COOKIE', '0') == '1',
        )
