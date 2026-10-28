"""Explicit local configuration; no automatic discovery of model weights."""

from dataclasses import dataclass
import os
from pathlib import Path


MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_REQUEST_BYTES = MAX_IMAGE_BYTES + 64 * 1024
MAX_PIXELS = 20_000_000
MIN_DIMENSION = 128


@dataclass(frozen=True)
class Settings:
    model_bundle: Path | None = None
    docs_enabled: bool = True

    @classmethod
    def from_environment(cls):
        bundle = os.environ.get('SKINAI_MODEL_BUNDLE', '').strip()
        return cls(
            model_bundle=Path(bundle).expanduser().resolve() if bundle else None,
            docs_enabled=os.environ.get('SKINAI_DOCS', '1') == '1',
        )
