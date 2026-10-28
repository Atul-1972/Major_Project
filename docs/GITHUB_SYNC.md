# Automatic GitHub synchronization

On 2026-10-26 the user authorized automatic pushes after project changes and phase completion. The approved destination is `origin/main` at `https://github.com/Atul-1972/Major_Project.git`. This authorization persists across agent sessions; routine pushes do not need another confirmation.

## When it runs

After each completed saved batch of work and at phase boundaries, the agent runs the appropriate checks and saves the usual development checkpoint:

```powershell
python scripts/checkpoint.py --summary "Describe saved work and actual validation" --next "Describe the next action"
```

The checkpoint saves project state/history/progress and refreshes the private conversation archive first. Then the sync helper audits source, stages changes, creates a commit if needed, fetches the configured branch, checks that the push preserves GitHub history, pushes normally and verifies the exact remote commit. A clean working tree can still have a previously unpushed commit; retrying sync pushes that commit without generating a duplicate commit.

The helper does not run the test suite itself. The agent must perform checks appropriate to the change before invoking the checkpoint and record unexecuted/incomplete checks honestly. This automation does not grant approval for a new development phase.

The helper only runs when a checkpoint or retry command is invoked. No background file watcher, scheduled task or startup service is installed. Unsaved editor buffers and manual edits made while no agent/checkpoint is running are not automatically uploaded; save a checkpoint to synchronize them. Network access and the user's GitHub authentication must be available.

## Files and boundaries

- `.project/github_sync.json`: tracked enable switch, approved remote/branch and 5 MiB maximum source-file size.
- `scripts/github_sync.py`: standard-library-only audit/commit/fetch/push/verification helper; Git is required.
- `.project/github_sync.local.json`: ignored last sync result and retry information.
- `.project/github_sync.local.lock`: ignored process lock preventing simultaneous sync helpers.

The helper respects Git ignores and independently rejects protected runtime directories, datasets, images, weights, archives, credential files, local records and common secret formats, including in staged files and intermediate outgoing commits. Secret values are omitted from guard messages. The source object audit is bounded to 64 MiB per pass. These checks support the existing repository rules and cannot certify every possible kind of sensitive information; keep private content out of source/docs.

Only the configured repository and `main` branch are authorized. Different/multiple push destinations, another branch, symlinks/submodules, unresolved conflicts or an active merge/rebase require review. The helper never force-pushes, resets, rebases, automatically merges remote changes or deletes user work. It uses a command-local trust setting for the verified project path to handle Windows sandbox/user ownership; global Git trust settings and credentials are not changed.

The private training ZIP, dataset, manifests/reviews, initialization/trained weights, environments and full chat history remain on disk and excluded. Automatic GitHub sync does not back up those assets or run on the college training process. Their separate backup/return workflow is unchanged.

## Retry and failure recovery

If network/authentication fails, checkpoint saving still succeeds and any created local commit is retained. Read the status:

```powershell
Get-Content -LiteralPath '.project/github_sync.local.json'
git status --short --branch
```

Retry without creating another development-history entry:

```powershell
python scripts/github_sync.py
```

Use the same local environment that normally runs project scripts. Within the agent sandbox, Windows credentials or network access may require the normal sandbox escalation for this retry. The standing user authorization covers the same source-only destination; no token should be pasted into source, chat or Git configuration.

If GitHub has commits absent locally, sync stops and preserves both histories. The agent reviews/fetches and merges appropriate remote work, resolves any conflicts while preserving user changes, then retries. A content guard stops before upload and identifies the file/category without exposing a secret. Do not bypass the guard by force-pushing or deleting local history.

For an intentionally local-only checkpoint:

```powershell
python scripts/checkpoint.py --summary "Saved locally" --next "Retry when ready" --no-github-sync
```

Set `enabled` to `false` in `.project/github_sync.json` to disable automatic attempts, or set `SKINAI_GITHUB_SYNC=0` in the environment for a temporary opt-out. Changing destination/branch or removing data protections requires an explicit user instruction.
