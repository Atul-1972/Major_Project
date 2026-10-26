"""Atomic files and exclusive local/Drive run locks; checkpoints contain safe types."""

import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

import torch


def replace_with_retry(source, target):
    for attempt in range(10):
        try:
            Path(source).replace(target)
            return
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.1 * (attempt + 1))


def atomic_save(path, value, *, tensor=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if tensor:
        with temporary.open("wb") as handle:
            torch.save(value, handle)
            handle.flush()
            os.fsync(handle.fileno())
    else:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    replace_with_retry(temporary, path)


@contextmanager
def run_lock(directory):
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    with (path / ".run.lock").open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
