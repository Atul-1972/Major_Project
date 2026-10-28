# SkinDiseaseAI

Explainable AI-Based Skin Disease Screening Using CNN–Transformer Fusion.

Research prototype for preliminary screening of supported skin-lesion categories. It is not a medical diagnosis or a replacement for a qualified dermatologist.

Primary research reference: [Enhanced Skin Disease Classification via Dataset Refinement and Attention-Based Vision Approach](https://pmc.ncbi.nlm.nih.gov/articles/PMC11939559/). Our required extension is EfficientNetV2-S + Transformer feature fusion, with Swin-T proposed for the Transformer branch. Standalone models provide comparison baselines; fusion improvement must be measured rather than assumed.

## Current status

Phase 2 is complete. The E1-E4 training package is ready for the college supercomputer; actual GPU training, metrics, explanation validation and a trained export remain pending. On 2026-10-28 the user approved **Phase 6 with training deferred**. The FastAPI backend now provides health/model metadata, bounded in-memory image validation, development API docs, and an export-loading adapter. With no verified evaluated model configured, predictions return **503 unavailable**. Backend real-model acceptance remains pending; dashboard and mobile work have not started. See [the backend guide](docs/PHASE_6.md) and [the full supercomputer package](docs/TRAINING_PACKAGE.md).

Read the [Phase 2 report](docs/phase-reports/phase-2.md), [Phase 1 report](docs/phase-reports/phase-1.md), and [running checklist](docs/CHECKLIST.md).

The [chat history guide](docs/CHAT_HISTORY.md) explains the full local conversation archive under `chat_history/`, its live refresh command, and how it differs from development checkpoints.

The repository is `Desktop/Major Project/SkinDiseaseAI`. Run all commands from `SkinDiseaseAI`, not its parent folder.

## Agreed constraints

- Deliver a web application. Follow the master prompt's research-first order: dataset, CNN, Transformer, fusion, evaluated export, FastAPI, then the web dashboard. Begin smartphone/Flutter work only on an explicit later command.
- Use a Python backend, preferably FastAPI, with PyTorch for machine learning.
- Do not use Node.js. Plan for server-rendered HTML, CSS, and browser JavaScript without a Node build toolchain.
- Keep a durable record of changes, decisions, validation, remaining work, and phase approvals.
- Report the completed work in each phase and ask before starting the next phase.

## Project layout

```text
backend/app/          FastAPI application, upload checks and evaluated-export adapter
backend/tests/        API and synthetic export-adapter verification
frontend/templates/  Future HTML templates
frontend/static/     Future CSS, browser JavaScript, and static assets
ai_model/            Dataset, training, evaluation, explanation, and model artifacts
mobile_app/          Deferred-scope note only; no Flutter implementation
tests/               Dataset, model, checkpoint, evaluation and export tests
scripts/             Development and checkpoint utilities
docs/                Requirements, plans, decisions, approvals, and reports
reports/             Environment evidence, literature review, and experiment reports
data/                Local runtime data; excluded from version control
artifacts/           Local trained models and evaluation artifacts; excluded
.project/            Persistent development state and checkpoint history
```

## Continue development

GitHub contains the source, tests, configuration, documentation and aggregate research/preparation records. Datasets, private frozen manifests/reviews, pretrained/trained weights, virtual environments, complete training ZIPs and chat archives stay in ignored local storage. A clone alone does not restore those assets. The college training package remains a separate private transfer; see [the training guide](docs/TRAINING_PACKAGE.md).

Read [the resume guide](docs/RESUME.md), [requirements](docs/REQUIREMENTS.md), and [phase plan](docs/PHASE_PLAN.md). The current checkpoint is `.project/state.json`; its history is `.project/history.jsonl`.

To save a development checkpoint using Python's standard library:

```powershell
python scripts/checkpoint.py --summary "Describe the work saved" --next "Describe the next action"
```

The utility records development metadata; save source files before invoking it. Git records source changes and checkpoint files record development context. It does not run the application or monitor an agent's token balance. GitHub synchronization covers committed source, while private assets still need an independent backup.

Automatic GitHub sync is enabled at the user's request. After completed saved changes and phase checkpoints, the checkpoint command audits, commits and pushes source/docs to `origin/main`; local checkpoints/commits survive a failed push. See [GitHub sync and retry instructions](docs/GITHUB_SYNC.md). It runs at checkpoints, not as a background watcher for every editor keystroke. Private data, weights, training ZIPs and chat archives remain excluded and need separate backup.

Files remain on disk when a session ends. Token-credit changes cannot automatically restart this agent. After credits return, open this workspace and send: **Resume SkinDiseaseAI from AGENTS.md and .project/state.json. Respect the phase approval gates.**

## Run the current phase

For your own college login, start with the [supercomputer beginner guide](docs/SUPERCOMPUTER_BEGINNER_GUIDE.md). It explains the Windows-to-server transfer and first GPU job before the full E1-E4 run. Login host/portal, GPU allocation and scheduler settings must come from the college.

The current full E1-E4 deliverable is `artifacts/training-package/SkinDiseaseAI-all-models-training.zip`; follow [TRAINING_PACKAGE.md](docs/TRAINING_PACKAGE.md). It includes source/configs, original dataset archives/receipts, frozen manifests and both ImageNet caches. Extract on persistent college storage, run `bash setup_training.sh` once, then `bash run_training.sh` in a suitable GPU allocation. Scheduler-specific account/partition settings must come from the college. The training ZIP includes `START_HERE.md`; rerunning the launcher resumes saved epochs. Python/CUDA dependencies are installed separately for the target machine.

To run the approved backend locally, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/backend-test.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the API or `/health` for liveness. This is the backend, with no dashboard yet. Model inference remains unavailable until the returned export passes review and startup checks; see [Phase 6](docs/PHASE_6.md).

The smaller E1-only Colab snapshot below is retained as an earlier alternative; it does not contain the new all-model suite.

Phase 3 commands and Colab instructions are in [the training guide](docs/PHASE_3.md). The small private transfer file is generated by:

```powershell
python scripts/build_colab_bundle.py
```

Phase 2 commands remain in [the data-preparation guide](docs/PHASE_2.md); preserve its frozen manifests. The dashboard remains a separately approved future phase. No evaluated skin-lesion model is included.
