# SkinDiseaseAI development instructions

## At the beginning of every session

1. Read `README.md`, `.project/state.json`, `docs/PROGRESS.md`, and `docs/APPROVALS.md`.
2. Read `docs/REQUIREMENTS.md` and `docs/PHASE_PLAN.md` before choosing work.
3. Inspect the workspace and any Git changes before editing; preserve user work.
4. Resume the recorded next action only within the last explicitly approved phase.

## User constraints

- Python backend, preferably FastAPI. No Node.js, npm, or Node-based build tooling.
- Web application only. Do not implement a smartphone application until the user explicitly commands it.
- Ask before each new phase. Do not treat silence, an expired session, or a request to resume as approval for a new phase.
- Record explicit phase approvals in `docs/APPROVALS.md` and report each phase's changes, validation, limitations, and next step.
- Keep files structured and preserve progress across sessions.
- The attached master prompt (`docs/MASTER_PROJECT_PROMPT.md`) authorizes Phase 1 only and changes the order to dataset preparation, E1 CNN, E2 Transformer, E3/E4 fusion, explanation/export, backend, then the web dashboard. Read the revised phase plan; the preparation plan is superseded.
- User confirmed Google Colab access and no HAM10000 download on 2026-10-25. Use local CPU checks and Colab GPU training, subject to actual runtime availability.
- Repository root is `SkinDiseaseAI/` inside the parent Desktop workspace. Do not recreate project records at the parent level.
- User reaffirmed PMC11939559 as the primary research reference and CNN–Transformer fusion as required. E1/E2 are comparison baselines; implement E3/E4 hybrid candidates and evaluate honestly. Do not silently replace the hybrid with a baseline. This clarification does not approve Phase 2.

## Saving and resuming

- Save files and run `python scripts/checkpoint.py` after meaningful completed work, before a phase boundary, and before ending a session.
- Supply a concrete `--summary`, `--next`, and relevant `--completed` items. Update requirements and decisions when they change.
- Record validation results and incomplete work accurately. Never label unexecuted checks as passed.
- The script updates `.project/state.json`, appends `.project/history.jsonl`, and regenerates `docs/PROGRESS.md`.
- If interrupted, inspect actual files and the history before relying on the latest checkpoint. A process may end between file writes.
- Do not claim that token exhaustion can always be detected or that credits automatically restart an agent. Frequent checkpoints reduce lost context; they do not guarantee an uninterrupted process.

## Application integrity

- Never present random, placeholder, or untrained output as a real model prediction.
- If validated weights are absent, state that inference is unavailable.
- Distinguish model confidence from calibrated probability and clinical risk.
- Clearly scope Grad-CAM explanations to the branch/layer that was actually explained.
- Do not commit uploaded skin images, datasets, model weights, secrets, or personal information.
- Reference research claims only after checking their source. Document dataset permissions and evaluation limitations.
