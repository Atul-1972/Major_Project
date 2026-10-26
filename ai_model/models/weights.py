"""Official Torchvision initialization with cached-file hash verification."""

import time
import urllib.error
from pathlib import Path

import torch

from ai_model.data.acquire import sha256_file


DEFAULT_CACHE = Path(__file__).resolve().parents[2] / 'artifacts/torch-cache'


def load_official_weights(model, weights, cache_dir=DEFAULT_CACHE):
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    filename = weights.url.rsplit('/', 1)[1]
    path = cache / filename
    prefix = filename.rsplit('-', 1)[1].split('.')[0]
    if not path.exists():
        temporary = path.with_suffix('.download')
        for attempt in range(3):
            try:
                torch.hub.download_url_to_file(weights.url, temporary, hash_prefix=prefix, progress=True)
                break
            except (OSError, urllib.error.URLError):
                if attempt == 2:
                    raise
                time.sleep(1)
        temporary.replace(path)
    digest = sha256_file(path)
    if not digest.startswith(prefix):
        raise ValueError('ImageNet initialization checksum mismatch; cached file was preserved')
    model.load_state_dict(torch.load(path, map_location='cpu', weights_only=True))
    return {'weights_enum': f'{type(weights).__name__}.{weights.name}', 'sha256': digest, 'url': weights.url}
