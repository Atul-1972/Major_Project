# SkinDiseaseAI

Explainable AI-Based Skin Disease Screening Using CNN–Transformer Fusion.

Research prototype for preliminary screening of supported skin-lesion categories. It is not a medical diagnosis or a replacement for a qualified dermatologist.

## Current status

Phase 1 is complete and locally verified. Waiting for the user's verification and explicit Phase 2 approval. Dataset processing, model training, backend implementation, and the dashboard have not started.

Read the [Phase 1 report](docs/phase-reports/phase-1.md), [setup guide](docs/SETUP_WINDOWS.md), and [running checklist](docs/CHECKLIST.md).

The repository is `Desktop/Major Project/SkinDiseaseAI`. Run all commands from `SkinDiseaseAI`, not its parent folder.

## Agreed constraints

- Deliver a web application. Follow the master prompt's research-first order: dataset, CNN, Transformer, fusion, evaluated export, FastAPI, then the web dashboard. Begin smartphone/Flutter work only on an explicit later command.
- Use a Python backend, preferably FastAPI, with PyTorch for machine learning.
- Do not use Node.js. Plan for server-rendered HTML, CSS, and browser JavaScript without a Node build toolchain.
- Keep a durable record of changes, decisions, validation, remaining work, and phase approvals.
- Report the completed work in each phase and ask before starting the next phase.

## Project layout

```text
backend/app/          Future FastAPI application and inference integration
frontend/templates/  Future HTML templates
frontend/static/     Future CSS, browser JavaScript, and static assets
ai_model/            Dataset, training, evaluation, explanation, and model artifacts
mobile_app/          Deferred-scope note only; no Flutter implementation
tests/               Future meaningful automated tests
scripts/             Development and checkpoint utilities
docs/                Requirements, plans, decisions, approvals, and reports
reports/             Environment evidence, literature review, and experiment reports
data/                Local runtime data; excluded from version control
artifacts/           Local trained models and evaluation artifacts; excluded
.project/            Persistent development state and checkpoint history
```

## Continue development

Read [the resume guide](docs/RESUME.md), [requirements](docs/REQUIREMENTS.md), and [phase plan](docs/PHASE_PLAN.md). The current checkpoint is `.project/state.json`; its history is `.project/history.jsonl`.

To save a development checkpoint using Python's standard library:

```powershell
python scripts/checkpoint.py --summary "Describe the work saved" --next "Describe the next action"
```

The utility records development metadata. Source files must be saved separately; it does not make backups, run the application, or monitor an agent's token balance. Git records source changes; checkpoint files record development context. Neither replaces an independent backup.

Files remain on disk when a session ends. Token-credit changes cannot automatically restart this agent. After credits return, open this workspace and send: **Resume SkinDiseaseAI from AGENTS.md and .project/state.json. Respect the phase approval gates.**

## Run the current phase

No application dependencies are needed for Phase 1. See [Windows setup](docs/SETUP_WINDOWS.md) for exact commands and [the checklist](docs/CHECKLIST.md) for completed and remaining work.

```powershell
python scripts/doctor.py
```

The web application has no run command yet. Its implementation follows the evaluated model in the approved phase plan. No trained skin-lesion model is included.
