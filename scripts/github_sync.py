"""Commit and normally push approved source checkpoints; retain local work on failure."""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_REMOTE = 'https://github.com/Atul-1972/Major_Project.git'
PROTECTED = ('data/', 'artifacts/', 'chat_history/', 'reports/local/', '.venv/', '.venv-hpc/', 'venv/',
             'ai_model/checkpoints/', 'ai_model/exports/', 'ai_model/results/', 'backend/uploads/', '.ssh/', '.aws/')
PLACEHOLDERS = {'data/.gitkeep', 'artifacts/.gitkeep', 'ai_model/checkpoints/.gitkeep',
                'ai_model/exports/.gitkeep', 'ai_model/results/.gitkeep'}
PRIVATE_SUFFIXES = ('.zip', '.tar', '.gz', '.7z', '.pt', '.pth', '.ckpt', '.onnx', '.pem', '.key', '.log',
                    '.sqlite', '.sqlite3', '.db', '.jpg', '.jpeg', '.png', '.csv', '.npy', '.npz', '.pkl', '.pickle', '.parquet')
SECRETS = {
    'GitHub token': rb'\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b',
    'private key': rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    'AWS key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'API key': rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b',
    'credential URL': rb'https?://[^\s/@:]+:[^\s/@]+@',
}


class SyncBlocked(ValueError):
    pass


class GitFailure(RuntimeError):
    pass


def git(root, *args, check=True, input=None):
    env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'never'}
    result = subprocess.run(['git', '-c', f'safe.directory={Path(root).resolve().as_posix()}',
                             '-c', 'credential.interactive=never', *args], cwd=root, env=env,
                            capture_output=True, timeout=60, input=input)
    if check and result.returncode:
        # Git output can contain credentials or machine paths; do not publish it in checkpoints.
        raise GitFailure(f'Git {args[0]} failed (exit {result.returncode}); inspect network/authentication or repository state, then retry.')
    return result


def text(root, *args):
    return git(root, *args).stdout.decode('utf-8', errors='replace').strip()


def audit_blob(name, data, max_bytes):
    normalized = name.replace('\\', '/').lower()
    path = PurePosixPath(normalized)
    if path.is_absolute() or '..' in path.parts or name.startswith('"') or any(char in name for char in '\r\n\0'):
        raise SyncBlocked(f'Unsafe source path: {name}')
    if any(normalized.startswith(prefix) for prefix in PROTECTED) and normalized not in PLACEHOLDERS:
        raise SyncBlocked(f'Private runtime path cannot be published: {name}')
    if path.name.startswith('.env') and path.name != '.env.example':
        raise SyncBlocked(f'Environment/credential file cannot be published: {name}')
    if normalized.endswith(PRIVATE_SUFFIXES) or path.name in ('id_rsa', 'id_ed25519', 'credentials'):
        raise SyncBlocked(f'Private data/model/archive file cannot be published: {name}')
    if normalized.startswith('.project/') and ('.local.' in path.name or path.name.endswith('.tmp')):
        raise SyncBlocked(f'Local-only project record cannot be published: {name}')
    if len(data) > max_bytes:
        raise SyncBlocked(f'File exceeds the configured source size limit: {name}')
    for label, pattern in SECRETS.items():
        if re.search(pattern, data):
            raise SyncBlocked(f'Potential {label} in {name}; review the file before syncing. Value omitted.')


def audit_worktree(root, policy):
    names = git(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z').stdout.split(b'\0')
    for value in dict.fromkeys(names):
        if not value:
            continue
        name = value.decode('utf-8')
        path = Path(root) / name
        if not path.exists():
            continue  # Source deletions are allowed.
        if path.is_symlink() or not path.resolve().is_relative_to(Path(root).resolve()):
            raise SyncBlocked(f'Symlink or external source path requires review: {name}')
        if path.stat().st_size > policy['max_file_bytes']:
            raise SyncBlocked(f'File exceeds the configured source size limit: {name}')
        audit_blob(name, path.read_bytes(), policy['max_file_bytes'])


def audit_objects(root, entries, policy):
    if not entries:
        return
    request = ''.join(oid + '\n' for oid, _name in entries).encode()
    metadata = git(root, 'cat-file', '--batch-check', input=request).stdout.splitlines()
    if len(metadata) != len(entries):
        raise SyncBlocked('Unable to inspect every outgoing/indexed object')
    blobs = []
    total = 0
    for line, (oid, name) in zip(metadata, entries):
        parts = line.decode().split()
        if len(parts) != 3:
            raise SyncBlocked(f'Unable to inspect object for {name}')
        if parts[1] != 'blob':
            continue
        size = int(parts[2])
        if size > policy['max_file_bytes']:
            raise SyncBlocked(f'File exceeds source size limit: {name}')
        total += size
        blobs.append((oid, name, size))
    if total > 64 * 1024**2:
        raise SyncBlocked('Source audit exceeds 64 MiB; review this unusually large change manually')
    if not blobs:
        return
    request = ''.join(oid + '\n' for oid, _name, _size in blobs).encode()
    stream = io.BytesIO(git(root, 'cat-file', '--batch', input=request).stdout)
    for oid, name, size in blobs:
        if stream.readline().decode().split() != [oid, 'blob', str(size)]:
            raise SyncBlocked(f'Unexpected object metadata for {name}')
        data = stream.read(size)
        if len(data) != size or stream.read(1) != b'\n':
            raise SyncBlocked(f'Incomplete object for {name}')
        audit_blob(name, data, policy['max_file_bytes'])


def audit_index(root, policy):
    entries = []
    for entry in git(root, 'ls-files', '--stage', '-z').stdout.split(b'\0'):
        if not entry:
            continue
        metadata, raw_name = entry.split(b'\t', 1)
        mode, oid, stage = metadata.decode().split()
        name = raw_name.decode('utf-8')
        if stage != '0' or mode in ('120000', '160000'):
            raise SyncBlocked(f'Unmerged/symlink/submodule index entry requires review: {name}')
        entries.append((oid, name))
    audit_objects(root, entries, policy)


def audit_outgoing(root, policy, revision):
    # Includes blobs in intermediate commits, even if a later commit deletes the secret.
    objects = text(root, 'rev-list', '--objects', f"{policy['remote']}/{policy['branch']}..{revision}")
    entries = []
    for line in objects.splitlines():
        parts = line.split(' ', 1)
        if len(parts) != 2:
            continue
        entries.append(tuple(parts))
    audit_objects(root, entries, policy)


@contextmanager
def sync_lock(root):
    path = Path(root) / '.project/github_sync.local.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def save_status(root, result):
    path = Path(root) / '.project/github_sync.local.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps({**result, 'checked_at_utc': datetime.now(timezone.utc).isoformat()}, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def _sync(root, policy, message):
    if Path(text(root, 'rev-parse', '--show-toplevel')).resolve() != root:
        raise SyncBlocked('Sync must run from the exact configured project repository')
    if text(root, 'branch', '--show-current') != policy['branch']:
        raise SyncBlocked('Automatic sync is only authorized on the configured main branch')
    remote = policy['remote']
    for options in ((remote,), ('--push', '--all', remote)):
        if text(root, 'remote', 'get-url', *options).splitlines() != [policy['url']]:
            raise SyncBlocked('The fetch/push destination differs from the authorized GitHub repository')
    for marker in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply', 'BISECT_LOG'):
        path = Path(text(root, 'rev-parse', '--git-path', marker))
        if (path if path.is_absolute() else root / path).exists():
            raise SyncBlocked('Finish the active Git operation before automatic synchronization')
    if text(root, 'ls-files', '--unmerged'):
        raise SyncBlocked('Resolve Git conflicts before automatic synchronization')
    audit_worktree(root, policy)
    audit_index(root, policy)  # Respect and validate already staged work before staging anything else.
    git(root, 'add', '--all')
    audit_index(root, policy)
    changed = git(root, 'diff', '--cached', '--quiet', check=False).returncode
    if changed not in (0, 1):
        raise GitFailure('Unable to inspect the staged changes')
    if changed:
        subject = ' '.join(message.split())[:120] or 'Save project checkpoint'
        git(root, 'commit', '-m', subject)
    revision = text(root, 'rev-parse', 'HEAD')
    # Preserve local commits when network/authentication fails; retry the same commit later.
    git(root, 'fetch', '--no-tags', remote, policy['branch'])
    tracking = f"{remote}/{policy['branch']}"
    if git(root, 'merge-base', '--is-ancestor', tracking, revision, check=False).returncode:
        raise SyncBlocked('GitHub has commits absent locally. Fetch and review/merge them before retrying; no force push was attempted.')
    audit_outgoing(root, policy, revision)
    git(root, 'push', remote, f"{revision}:refs/heads/{policy['branch']}")
    received = text(root, 'ls-remote', remote, f"refs/heads/{policy['branch']}").split()
    if not received or received[0] != revision:
        raise GitFailure('The remote commit could not be verified; retry synchronization')
    return {'status': 'synced', 'commit': revision, 'remote': policy['url'], 'branch': policy['branch']}


def sync(root=ROOT, message='Save project checkpoint'):
    root = Path(root).resolve()
    path = root / '.project/github_sync.json'
    if not path.is_file() or os.environ.get('SKINAI_GITHUB_SYNC') == '0':
        return {'status': 'skipped', 'reason': 'Automatic GitHub sync is not enabled here'}
    try:
        policy = json.loads(path.read_text(encoding='utf-8'))
        if not policy.get('enabled'):
            return {'status': 'skipped', 'reason': 'Automatic GitHub sync is disabled'}
        if policy.get('url') != EXPECTED_REMOTE or policy.get('remote') != 'origin' or policy.get('branch') != 'main':
            raise SyncBlocked('Only the user-authorized origin/main repository is allowed')
        if type(policy.get('max_file_bytes')) is not int or not 0 < policy['max_file_bytes'] <= 5 * 1024**2:
            raise SyncBlocked('Invalid source file size limit')
        with sync_lock(root):
            try:
                result = _sync(root, policy, message)
            except SyncBlocked as error:
                result = {'status': 'blocked', 'reason': str(error)}
            except (GitFailure, OSError, subprocess.SubprocessError) as error:
                result = {'status': 'pending', 'reason': str(error) if isinstance(error, GitFailure) else type(error).__name__,
                          'recovery': 'Local checkpoint/commits are retained. Retry scripts/github_sync.py when the issue is resolved.'}
            save_status(root, result)
            return result
    except (OSError, ValueError, KeyError) as error:
        return {'status': 'blocked', 'reason': str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--message', default='Save project checkpoint')
    args = parser.parse_args()
    result = sync(message=args.message)
    print(json.dumps(result, indent=2))
    return 0 if result['status'] in ('synced', 'skipped') else 1


if __name__ == '__main__':
    raise SystemExit(main())
