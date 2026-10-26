# SkinDiseaseAI

Explainable AI-Based Skin Disease Screening Using CNN–Transformer Fusion.

Research prototype for preliminary screening of supported skin-lesion categories. It is not a medical diagnosis or a replacement for a qualified dermatologist.

Primary research reference: [Enhanced Skin Disease Classification via Dataset Refinement and Attention-Based Vision Approach](https://pmc.ncbi.nlm.nih.gov/articles/PMC11939559/). Our required extension is EfficientNetV2-S + Transformer feature fusion, with Swin-T proposed for the Transformer branch. Standalone models provide comparison baselines; fusion improvement must be measured rather than assumed.

## Current status

Phase 2 is complete. The user explicitly authorized the full E1-E4 training package, including Phase 4 Transformer and Phase 5 fusion, on 2026-10-26. All four architectures, resumable sequential fitting, validation-first hybrid selection, evaluation and inference export are implemented. The [complete supercomputer guide](docs/TRAINING_PACKAGE.md) replaces the earlier E1-only handoff. Official ImageNet CPU diagnostics passed on real images for all four models; actual GPU/research training, metrics and explanation validation remain pending. Backend, dashboard and mobile work have not started.

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
backend/app/          Future FastAPI application and inference integration
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

The utility records development metadata. Source files must be saved separately; it does not make backups, run the application, or monitor an agent's token balance. Git records source changes; checkpoint files record development context. Neither replaces an independent backup.

Files remain on disk when a session ends. Token-credit changes cannot automatically restart this agent. After credits return, open this workspace and send: **Resume SkinDiseaseAI from AGENTS.md and .project/state.json. Respect the phase approval gates.**

## Run the current phase

For your own college login, start with the [supercomputer beginner guide](docs/SUPERCOMPUTER_BEGINNER_GUIDE.md). It explains the Windows-to-server transfer and first GPU job before the full E1-E4 run. Login host/portal, GPU allocation and scheduler settings must come from the college.

The current full E1-E4 deliverable is `artifacts/training-package/SkinDiseaseAI-all-models-training.zip`; follow [TRAINING_PACKAGE.md](docs/TRAINING_PACKAGE.md). It includes source/configs, original dataset archives/receipts, frozen manifests and both ImageNet caches. Extract on persistent college storage, run `bash setup_training.sh` once, then `bash run_training.sh` in a suitable GPU allocation. Scheduler-specific account/partition settings must come from the college. The training ZIP includes `START_HERE.md`; rerunning the launcher resumes saved epochs. Python/CUDA dependencies are installed separately for the target machine.

The smaller E1-only Colab snapshot below is retained as an earlier alternative; it does not contain the new all-model suite.

Phase 3 commands and Colab instructions are in [the training guide](docs/PHASE_3.md). The small private transfer file is generated by:

```powershell
python scripts/build_colab_bundle.py
```

Phase 2 commands remain in [the data-preparation guide](docs/PHASE_2.md); preserve its frozen manifests. The web application has no run command yet. Its implementation follows the evaluated model in the approved phase plan. No evaluated skin-lesion model is included.
