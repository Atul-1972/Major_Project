# Phase 1 report

Date: 2026-10-25 (Asia/Calcutta).

Status: Phase 1 delivered and locally verified. Awaiting user verification and explicit approval for Phase 2.

## Authorization and scope

The user supplied a master prompt explicitly asking for environment inspection, dataset planning, and Phase 1 only. The prompt is preserved in `docs/MASTER_PROJECT_PROMPT.md`. It changes the initial delivery order to model research before application development. Mobile remains deferred.

## Completed work

| Deliverable | Location and outcome |
| --- | --- |
| Named repository | `Desktop/Major Project/SkinDiseaseAI`; moved preparation records intact; parent README/AGENTS point here |
| Git setup | Local repository initialized on `main`; existing author identity is available; no remote configured or GitHub publication performed |
| Structured files | `ai_model/`, `backend/`, `frontend/`, deferred `mobile_app/`, `docs/`, `reports/`, scripts and tests locations |
| Isolated Python environment | `.venv/` created with Python 3.11.0; no third-party dependencies needed or installed for Phase 1 |
| Environment verifier | Complete runnable `scripts/doctor.py`; checks Python, structure, Git root, working disk space and development checkpoint consistency |
| Requirements and phase gates | Updated `REQUIREMENTS.md`, `APPROVALS.md`, `PHASE_PLAN.md`, `CHECKLIST.md`, and `AGENTS.md` |
| Research design | `ARCHITECTURE.md`, `DATASET_PLAN.md`, `EXPERIMENT_PLAN.md`, `API_SPEC.md`, and `UML.md` |
| Source review | `reports/literature_review.md`, with primary-source links and live-access limitations |
| Setup and recovery | `SETUP_WINDOWS.md`, `ENVIRONMENT.md`, updated `RESUME.md`, and preserved checkpoint history |
| Repository hygiene | `.gitignore`, `.gitattributes`, planned-only `.env.example`, original-code MIT license, standard-library dependency manifest |

No placeholder model implementation or fabricated inference result was added. Future component folders contain clearly labeled plans or empty source locations.

## Environment findings and user confirmation

- Intel Core Ultra 5 125H; 14 cores / 18 logical processors.
- About 15.7 GiB physical RAM; Intel Arc graphics; no NVIDIA GPU or `nvidia-smi` detected.
- Python 3.11.0 and Git 2.52.0.windows.1 available.
- About 47.4 GiB disk free at initial inspection; the later portable report measured about 43.3 GiB. Capacity must be rechecked before data extraction.
- The user confirmed Colab access and that HAM10000 is not downloaded.
- Plan: local development/CPU verification and later Colab GPU training, subject to an actual allocated runtime.

Initial sandbox WMI access failed; a read-only elevated rerun returned hardware details. This was diagnosed before continuing. No claim is made about usable GPU training memory from the WMI adapter field.

## Design decisions

- Start with HAM10000's documented seven-category dermoscopy task, verifying source/version permissions at acquisition. No broad skin-disease or smartphone-camera capability is implied.
- Audit metadata/images and split by genuine patient IDs where available, otherwise lesion groups, connecting duplicates. Proposed 70/15/15 ratios remain subject to feasible grouped class coverage.
- Compare EfficientNetV2-S, proposed Swin-T, concatenation fusion, and two-branch attention fusion on the same saved manifests. Fusion improvement is a hypothesis.
- Use validation macro-F1 for selection; keep test data out of tuning. Save training recovery state and evaluation evidence.
- Grad-CAM on the fused model must be labeled as CNN spatial contribution to the final output, not a complete spatial explanation of both branches.
- Build FastAPI after evaluated model export, then serve an HTML/CSS/browser-JavaScript dashboard without Node.js.
- Proposed initial application processes uploads in memory without accounts or retained user-image history. Development-history persistence is independent.
- Optional segmentation needs real compatible annotated masks. Flutter requires a later explicit user command.

## Executed checks

| Command/check | Actual result |
| --- | --- |
| `python -m venv .venv` | Exit 0; isolated environment created |
| `.\.venv\Scripts\python.exe scripts\doctor.py --output reports/local/environment.json` | Exit 0; every Phase 1 check passed; virtual environment true |
| `.\.venv\Scripts\python.exe -m compileall -q scripts` | Exit 0; checkpoint and environment scripts compiled |
| Doctor/checkpoint `--help` | Exit 0; both CLIs available |
| Venv `python -m pip --version` | Exit 0; pip resolves inside this repository's venv |
| Doctor `--require-ml` | Expected exit 1, checked by a subprocess assertion; absent ML packages reported and all Phase 1 checks remained green |
| `git check-ignore` probes | Expected exclusions confirmed for `.env`, venv, data, weights/exports/results, and local reports; `.env.example` and development state/history remain versionable |
| Checkpoint state/history | Latest entry matches saved state; history survives the repository move |
| Git remote check | Empty; no external publication |

Machine-specific JSON evidence is saved under ignored `reports/local/`. Package presence checks are not import/compatibility or GPU tests. No pytest suite was run; application/ML code does not exist yet and Phase 1 uses standard-library checks.

## Verification for the user

Run from the new repository folder:

```powershell
Set-Location -LiteralPath (Join-Path $env:USERPROFILE 'OneDrive\Desktop\Major Project\SkinDiseaseAI')
.\.venv\Scripts\python.exe scripts\doctor.py
git status --short --branch
```

The verifier should exit 0 and include `"passed": true`. Check Git history using `git log -1 --oneline` after the local snapshot has been saved. No server is expected to be running.

## Limitations and deferred work

- HAM10000 is not downloaded, audited, or split. No project-specific class mapping has been generated from actual data.
- No model has trained; no model performance, calibration, clinical validity, or smartphone generalization has been demonstrated.
- No Colab notebook/GPU execution, ML dependency installation, FastAPI service, dashboard, Flutter application, or deployment has occurred.
- Live PMC/publisher/Dataverse access was challenged or rate-limited; source review used accessible primary-source indexed text and the accessible PAD-UFES-20 record. Dataset-version terms still require direct confirmation at download.
- Some design defaults are proposed, not clinically established thresholds. Final dependency pins and runnable train/API commands arrive with tested implementations in their phases.
- Agent token/credit changes cannot trigger guaranteed final writes or automatic restart. Saved files and frequent checkpoints support explicit resumption.

## Proposed Phase 2

Only after approval: implement acquisition guidance, dataset audit, duplicate/group checks, reproducible grouped manifests/class mapping, shared preprocessing and a tested data loader. Verify at least one actual batch and report zero prohibited cross-split overlaps before training. Dataset access or GPU availability must never be replaced with invented verification.
