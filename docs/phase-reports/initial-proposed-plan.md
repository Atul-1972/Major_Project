# Initial proposed delivery phases — superseded

Historical preparation proposal only. The master prompt changed the order to research before the application. The authoritative plan is now `docs/PHASE_PLAN.md`.

Every phase requires explicit user approval before it starts. Scope and acceptance criteria will be refined during Phase 1.

## Preparation — completed

Established the local folder structure, recorded the user's requirements, and added durable checkpoints and resume instructions. No application or training code is implemented.

## Phase 1 — requirements and research design

- Verify the supplied paper and document how this project relates to it.
- Resolve dataset access, permitted uses, class definitions, compute availability, image handling, accounts/history, and deployment goals.
- Define the architecture, CNN–Transformer fusion approach, explanation scope, and model evaluation plan.
- Produce acceptance criteria and a concrete implementation backlog.

Exit: a reviewable specification and architecture, with unresolved dependencies clearly identified. Report the phase and request Phase 2 approval.

## Phase 2 — Python web foundation

- Establish FastAPI, configuration, dependency management, storage migrations where needed, and the no-Node frontend structure.
- Implement the responsive dashboard and a validated upload flow.
- Define API contracts and show truthful unavailable/processing/error states until a trained model is integrated.
- Add meaningful checks for upload handling, persistence, and error behavior.

Exit: a locally runnable web foundation with setup instructions and verified upload behavior. Report and request Phase 3 approval.

## Phase 3 — model training, evaluation, and integration

- Prepare the approved dataset and reproducible train/validation/test splits.
- Implement CNN and Transformer feature extraction and fusion; train or integrate approved, documented weights.
- Evaluate with suitable class-level metrics and document limitations.
- Integrate inference, confidence presentation, and correctly scoped Grad-CAM.

Exit: reproducible model artifacts and verified predictions/explanations through the API. Completion depends on actual dataset and compute access. Report and request Phase 4 approval.

## Phase 4 — complete workflow and verification

- Connect the dashboard to real inference and progress/error states.
- Complete approved result history, image retention/deletion, and account features if included in Phase 1.
- Check accessibility, responsive behavior, input handling, privacy controls, and the full upload-to-result workflow.
- Record automated and manual verification results and remaining research limitations.

Exit: a functional, tested research prototype. Report and request Phase 5 approval.

## Phase 5 — deployment and handover

- Prepare the approved Python hosting configuration, model loading, secrets setup, storage, and backup/restore procedure.
- Deploy within the approved scope and verify the running application.
- Deliver runbooks, API documentation, training/evaluation records, and a final phase report.

Exit: a working deployment and reproducible local setup, subject to hosting access and compute availability.

## Deferred

Flutter/Android or any other smartphone application requires a new explicit user command and its own approved plan.

## Report format for every phase

Document scope, files/features changed, decisions, checks run and their outcomes, outstanding limitations, and the proposed next phase in `docs/phase-reports/`. Update the checkpoint before requesting the next phase's approval.
