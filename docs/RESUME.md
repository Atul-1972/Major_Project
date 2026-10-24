# Resume SkinDiseaseAI

Open the `Major Project/SkinDiseaseAI` repository (or the parent workspace and enter `SkinDiseaseAI`) and send:

> Resume SkinDiseaseAI from AGENTS.md and .project/state.json. Read docs/PROGRESS.md and docs/APPROVALS.md. Continue the last approved phase and ask before starting any new phase. Use Python/FastAPI, do not use Node.js, and do not start smartphone development.

The preparation files moved into the named repository during Phase 1. The authoritative checkpoint is now `SkinDiseaseAI/.project/state.json` relative to the parent workspace. The old five-phase preparation plan was replaced by the master prompt's research-first plan.

## What persists

- Saved source files and documentation in this workspace.
- `.project/state.json`: latest saved phase, status, completed items, summary, and next action.
- `.project/history.jsonl`: chronological development checkpoint records.
- `docs/PROGRESS.md`: readable report generated from the history.
- `docs/APPROVALS.md`: explicit phase-approval record.

The checkpoint utility runs with Python's standard library; no package installation is required.

```powershell
python scripts/checkpoint.py --help
python scripts/checkpoint.py --summary "Saved upload validation" --next "Run the approved upload checks" --completed "Implemented upload validation"
```

Change `--phase` only after explicit approval has been recorded. Use `--status awaiting_approval` when a phase report is ready and the next phase needs approval.

## Interruption limits

An agent cannot guarantee a final write at the exact moment tokens or credits run out. Save files and checkpoints frequently. If interruption occurs mid-command, compare the actual files with the latest history entry and rerun only incomplete steps.

This utility does not detect token balances, buy credits, restart the agent, or make source backups. It preserves task context; saved source files preserve implementation. A later session starts when the user sends a resume message. Independently protect this workspace with version control and backups.
