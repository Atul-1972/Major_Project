"""Real local Git repositories exercise synchronization; no GitHub/network requests."""

import json
import subprocess
import sys
import types
from pathlib import Path

import pytest

from scripts import github_sync


def command(root, *args):
    return subprocess.run(['git', *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def source_repo(tmp_path, monkeypatch):
    remote = tmp_path / 'remote.git'
    command(tmp_path, 'init', '--bare', str(remote))
    root = tmp_path / 'source'
    root.mkdir()
    command(root, 'init', '-b', 'main')
    command(root, 'config', 'user.name', 'Synthetic Sync Fixture')
    command(root, 'config', 'user.email', 'fixture@example.invalid')
    command(root, 'config', 'commit.gpgsign', 'false')
    command(root, 'remote', 'add', 'origin', str(remote))
    (root / '.project').mkdir()
    policy = {'enabled': True, 'remote': 'origin', 'branch': 'main', 'url': str(remote), 'max_file_bytes': 5242880}
    (root / '.project/github_sync.json').write_text(json.dumps(policy), encoding='utf-8')
    (root / '.gitignore').write_text('artifacts/\ndata/\n.env\n.project/*.local*\n', encoding='utf-8')
    (root / 'README.md').write_text('Synthetic Git integration-test fixture only.\n', encoding='utf-8')
    command(root, 'add', '--all')
    command(root, 'commit', '-m', 'Initial fixture')
    command(root, 'push', '-u', 'origin', 'main')
    monkeypatch.setattr(github_sync, 'EXPECTED_REMOTE', str(remote))
    return root, remote


def remote_head(remote):
    return command(remote, 'rev-parse', 'refs/heads/main')


def test_source_change_pushes_once_and_ignored_assets_stay_local(source_repo):
    root, remote = source_repo
    (root / 'README.md').write_text('Updated synthetic source.\n', encoding='utf-8')
    (root / '.env').write_text('private test fixture', encoding='utf-8')
    (root / 'artifacts').mkdir()
    (root / 'artifacts/model.pt').write_bytes(b'private synthetic artifact')
    result = github_sync.sync(root, 'Save synthetic changes')
    assert result['status'] == 'synced'
    assert remote_head(remote) == command(root, 'rev-parse', 'HEAD') == result['commit']
    names = command(root, 'ls-files').splitlines()
    assert '.env' not in names and 'artifacts/model.pt' not in names
    assert not any('github_sync.local' in name for name in names)
    assert command(root, 'status', '--porcelain') == ''
    again = github_sync.sync(root)
    assert again['status'] == 'synced' and again['commit'] == result['commit']


def test_secret_in_untracked_source_is_not_committed_or_logged(source_repo):
    root, remote = source_repo
    before = remote_head(remote)
    secret = 'ghp_' + 'a' * 36
    (root / 'unsafe.py').write_text('TOKEN = ' + repr(secret), encoding='utf-8')
    result = github_sync.sync(root)
    assert result['status'] == 'blocked' and 'unsafe.py' in result['reason']
    assert command(root, 'rev-parse', 'HEAD') == remote_head(remote) == before
    assert secret not in json.dumps(result)
    assert secret not in (root / '.project/github_sync.local.json').read_text()
    assert 'unsafe.py' not in command(root, 'ls-files').splitlines()


@pytest.mark.parametrize('name', ('data/private.json', 'model.pt', 'credentials.pem'))
def test_force_staged_private_files_are_refused_without_removing_user_work(source_repo, name):
    root, remote = source_repo
    before = remote_head(remote)
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('Synthetic private fixture', encoding='utf-8')
    command(root, 'add', '-f', '--', name)
    result = github_sync.sync(root)
    assert result['status'] == 'blocked'
    assert remote_head(remote) == before
    assert path.is_file() and name in command(root, 'ls-files').splitlines()


def test_changed_or_extra_remote_push_destination_is_refused(source_repo):
    root, remote = source_repo
    before = remote_head(remote)
    (root / 'README.md').write_text('Pending source edit.\n', encoding='utf-8')
    command(root, 'remote', 'set-url', 'origin', 'https://example.invalid/other.git')
    assert github_sync.sync(root)['status'] == 'blocked'
    command(root, 'remote', 'set-url', 'origin', str(remote))
    command(root, 'remote', 'set-url', '--add', '--push', 'origin', str(remote))
    command(root, 'remote', 'set-url', '--add', '--push', 'origin', 'https://example.invalid/other.git')
    assert github_sync.sync(root)['status'] == 'blocked'
    assert command(root, 'rev-parse', 'HEAD') == before


def test_other_branch_and_active_merge_are_refused(source_repo):
    root, remote = source_repo
    before = remote_head(remote)
    command(root, 'checkout', '-b', 'unapproved-branch')
    assert github_sync.sync(root)['status'] == 'blocked'
    command(root, 'checkout', 'main')
    (root / '.git/MERGE_HEAD').write_text(before + '\n', encoding='utf-8')
    assert github_sync.sync(root)['status'] == 'blocked'
    assert remote_head(remote) == before


def test_failed_push_retains_local_commit_and_retry_uses_that_commit(source_repo, monkeypatch):
    root, remote = source_repo
    before = remote_head(remote)
    (root / 'README.md').write_text('Source saved before a simulated offline push.\n', encoding='utf-8')
    real_git = github_sync.git

    def fail_push(root, *args, **kwargs):
        if args[0] == 'push':
            raise github_sync.GitFailure('Synthetic offline push failure')
        return real_git(root, *args, **kwargs)

    with monkeypatch.context() as change:
        change.setattr(github_sync, 'git', fail_push)
        result = github_sync.sync(root)
    saved = command(root, 'rev-parse', 'HEAD')
    assert result['status'] == 'pending'
    assert saved != before and remote_head(remote) == before
    assert json.loads((root / '.project/github_sync.local.json').read_text())['status'] == 'pending'
    assert github_sync.sync(root)['status'] == 'synced'
    assert command(root, 'rev-parse', 'HEAD') == remote_head(remote) == saved


def test_remote_changes_are_preserved_until_reviewed_merge(source_repo, tmp_path):
    root, remote = source_repo
    collaborator = tmp_path / 'collaborator'
    command(tmp_path, 'clone', '--branch', 'main', str(remote), str(collaborator))
    command(collaborator, 'config', 'user.name', 'Synthetic Collaborator')
    command(collaborator, 'config', 'user.email', 'collaborator@example.invalid')
    (collaborator / 'remote-note.md').write_text('Synthetic remote edit\n', encoding='utf-8')
    command(collaborator, 'add', '--all')
    command(collaborator, 'commit', '-m', 'Collaborator fixture change')
    command(collaborator, 'push', 'origin', 'main')
    remote_revision = remote_head(remote)
    (root / 'README.md').write_text('Local independent source edit\n', encoding='utf-8')
    result = github_sync.sync(root)
    assert result['status'] == 'blocked' and 'absent locally' in result['reason']
    assert remote_head(remote) == remote_revision
    command(root, 'merge', '--no-edit', 'origin/main')
    assert github_sync.sync(root)['status'] == 'synced'
    assert (root / 'remote-note.md').is_file()


def test_secret_in_intermediate_unpushed_commit_is_refused(source_repo):
    root, remote = source_repo
    before = remote_head(remote)
    path = root / 'temporary-secret.txt'
    path.write_text('ghp_' + 'b' * 36, encoding='utf-8')
    command(root, 'add', '--all')
    command(root, 'commit', '-m', 'Synthetic unsafe historical fixture')
    path.unlink()
    command(root, 'add', '--all')
    command(root, 'commit', '-m', 'Remove synthetic fixture')
    assert command(root, 'status', '--porcelain') == ''
    result = github_sync.sync(root)
    assert result['status'] == 'blocked' and 'GitHub token' in result['reason']
    assert remote_head(remote) == before


def test_disabled_policy_skips_without_committing(source_repo, monkeypatch):
    root, remote = source_repo
    before = remote_head(remote)
    (root / 'README.md').write_text('Uncommitted fixture edit\n', encoding='utf-8')
    monkeypatch.setenv('SKINAI_GITHUB_SYNC', '0')
    assert github_sync.sync(root)['status'] == 'skipped'
    assert command(root, 'rev-parse', 'HEAD') == before


def test_checkpoint_is_saved_when_automatic_sync_is_pending(tmp_path, monkeypatch):
    from scripts import checkpoint

    project = tmp_path / '.project'
    project.mkdir()
    monkeypatch.setattr(checkpoint, 'ROOT', tmp_path)
    monkeypatch.setattr(checkpoint, 'STATE_DIR', project)
    monkeypatch.setattr(checkpoint, 'STATE_FILE', project / 'state.json')
    monkeypatch.setattr(checkpoint, 'HISTORY_FILE', project / 'history.jsonl')
    fake_exporter = types.ModuleType('export_chat')
    fake_exporter.refresh_archives = lambda: 0
    monkeypatch.setitem(sys.modules, 'export_chat', fake_exporter)
    monkeypatch.setitem(sys.modules, 'github_sync', github_sync)
    monkeypatch.setattr(github_sync, 'sync', lambda *_a, **_kw: {'status': 'pending', 'reason': 'Synthetic offline fixture'})
    monkeypatch.setattr(sys, 'argv', ['checkpoint', '--summary', 'Synthetic saved work', '--next', 'Retry synthetic sync'])
    checkpoint.main()
    assert json.loads((project / 'state.json').read_text())['summary'] == 'Synthetic saved work'
    assert len((project / 'history.jsonl').read_text().splitlines()) == 1
    assert (tmp_path / 'docs/PROGRESS.md').is_file()
