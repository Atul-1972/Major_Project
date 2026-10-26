# Resume SkinDiseaseAI

Open the `Major Project/SkinDiseaseAI` repository (or the parent workspace and enter `SkinDiseaseAI`) and send:

> Resume SkinDiseaseAI from AGENTS.md and .project/state.json. Read docs/PROGRESS.md and docs/APPROVALS.md. Continue the last approved phase and ask before starting any new phase. Use Python/FastAPI, do not use Node.js, and do not start smartphone development.

The preparation files moved into the named repository during Phase 1. The authoritative checkpoint is now `SkinDiseaseAI/.project/state.json` relative to the parent workspace. The old five-phase preparation plan was replaced by the master prompt's research-first plan.

## What persists

**Login clarification, 2026-10-26:** the college says it will provide the user a login, so the user will run training personally. `docs/SUPERCOMPUTER_BEGINNER_GUIDE.md` gives the step-by-step SSH/Slurm and portal paths. Obtain the host/portal, GPU/scheduler/account/partition instructions and persistent storage location when provided. The approximately 3 GB all-model ZIP remains unchanged and verified. No remote access or GPU execution has occurred.

**Current work, 2026-10-26:** the user clarified they must run training themselves and explicitly approved Phases 4 and 5 for **all four models**. The new `docs/TRAINING_PACKAGE.md` and `artifacts/training-package/SkinDiseaseAI-all-models-training.zip` replace the earlier E1-only handoff. E1-E4 source/configs, shared checkpoint recovery, sequential GPU workflow, validation-first selection, evaluation and hybrid export are implemented. Both official ImageNet caches and the original dataset are included in the new package. Actual pretrained CPU diagnostics passed for all four; college GPU execution and research results are still unverified. The final 2,973,268,386-byte ZIP passed receipt/CRC/integrity checks, 66 shipped-file hash checks, and 58 tests from the extracted copy; 69 repository tests passed. The deliverable is ready to transfer. See `reports/training-package-summary.json` for aggregate evidence. Old pause/Colab/staff-operated notes below are historical and do not override this instruction. Do not start application/mobile/deployment work.

**Latest compute choice, 2026-10-26:** the user confirmed their college will provide the supercomputer, then clarified that its team will run training and has supplied no access details. Use `COLLEGE_TRAINING_HANDOFF.md` with the existing ZIP for this staff-operated handoff; student login access is not required. Obtain the facility guide, GPU model, connection method, scheduler and persistent-storage details before adapting Phase 3. College execution takes precedence over the Colab upload walkthrough below; preserve that walkthrough and both transfer files as alternatives. No facility access, allocated GPU or remote execution is verified.

**Current instruction, 2026-10-26: resume Phase 3.** The user said "resume phase 3" and confirmed "Neither file is uploaded yet". This supersedes the earlier pause below. The existing 1,170,252-byte ZIP passed its receipt hash, archive/content checks, and source/config/frozen-data comparison; all seven notebook code cells parsed. Guide ZIP upload to My Drive and notebook upload to Colab first. No remote upload, GPU smoke, training or evaluation has been verified. The first training session still uses `EPOCHS_THIS_SESSION = 1`. The pause notes below are historical context.

**Saved starting point for the next session:** the user reposted the Colab handoff instructions and said "we will start from here tomarrow". Resume from that walkthrough: verify/upload `skindiseaseai-phase3.zip` to My Drive, upload/open `phase3_e1_training.ipynb` in Colab, reconnect a GPU, then run notebook cells in order. Check which uploads actually succeeded; do not assume setup or smoke passed. For the first training session, use Python `EPOCHS_THIS_SESSION = 1`, verify the saved epoch, then change it to `None` to continue. The pasted SQL code block was a scheduling note, not executable notebook code. This clarification preserves the pause and does not authorize starting now.

**Latest instruction, 2026-10-26: pause and save.** The user reported that uploads were unsuccessful and intends to continue tomorrow, 2026-10-27. Phase 3 is paused. Do not restart uploads, acquisition or training until the user asks to resume. The notebook, approximately 1.2 MB ZIP and its receipt are retained unchanged. On resumption, first identify whether the Drive ZIP upload or Colab notebook upload failed, inspect any existing remote/local files or reported error, and guide that step before starting GPU smoke/training. A previously reported available GPU may need reconnecting; no actual project GPU smoke or training has been verified.

The user approved Phase 3 with "so start phase 3" on 2026-10-25, requested pause/resume and beginner Colab guidance, then reported that Colab works and the GPU check returns True. Phase 3 implementation has 55 passing local tests and an actual-model, real-image CPU diagnostic; that diagnostic uses random initialization and is not research training. The official ImageNet download was reset by the local network; its actual GPU initialization/training must still run in Colab. Start at `docs/PHASE_3.md` and `docs/phase-reports/phase-3.md`. The private transfer file is `artifacts/colab-transfer/skindiseaseai-phase3.zip`; the notebook is `ai_model/notebooks/phase3_e1_training.ipynb`. No agent-controlled Colab session is available. Guide the user through upload, GPU smoke, one saved epoch, resume, full training and final evaluation. Keep Phase 3 in progress until actual evidence is reviewed; do not request Phase 4 approval yet.

Phase 2 is complete: 10,015 images, saved 7,011/1,502/1,502 splits, zero prohibited overlaps and real CPU loader batches. Preserve the manifests and private review evidence. There is no pending local acquisition job to restart.

The runner below is retained for recovery/reverification within Phase 2. Inspect `.project/phase2_run.local.json` and `reports/local/phase2-run.log` before any restart to avoid duplicate jobs. When a restart is actually needed, run from `SkinDiseaseAI`:

```powershell
.\.venv\Scripts\python.exe -u scripts\run_phase2.py
```

The runner resumes the official download and completes only the already-approved Phase 2 checks. It does not start training. Keep `data/ham10000/raw/*.part`, matching `.part.json` files, and saved chunks/receipts. The source must still match its saved entity tag for a safe continuation; a changed/unavailable source stops with an error rather than silently mixing files.

- Saved source files and documentation in this workspace.
- `.project/state.json`: latest saved phase, status, completed items, summary, and next action.
- `.project/history.jsonl`: chronological development checkpoint records.
- `docs/PROGRESS.md`: readable report generated from the history.
- `docs/APPROVALS.md`: explicit phase-approval record.
- `chat_history/`: private local user/assistant conversation exports, separate from the progress summaries. See `CHAT_HISTORY.md`; archives and source registration are ignored by Git and need their own workspace backup.

The checkpoint utility runs with Python's standard library; no package installation is required.

```powershell
python scripts/checkpoint.py --help
python scripts/checkpoint.py --summary "Saved upload validation" --next "Run the approved upload checks" --completed "Implemented upload validation"
```

Change `--phase` only after explicit approval has been recorded. Use `--status awaiting_approval` when a phase report is ready and the next phase needs approval.

## Interruption limits

An agent cannot guarantee a final write at the exact moment tokens or credits run out. Save files and checkpoints frequently. If interruption occurs mid-command, compare the actual files with the latest history entry and rerun only incomplete steps.

This utility does not detect token balances, buy credits, restart the agent, or make source backups. It preserves task context; saved source files preserve implementation. A later session starts when the user sends a resume message. Independently protect this workspace with version control and backups.
