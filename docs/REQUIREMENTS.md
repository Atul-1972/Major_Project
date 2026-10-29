# Requirements

Recorded from the user's instructions on 2026-10-25 (Asia/Calcutta).

## Purpose and users

**SkinDiseaseAI – Explainable AI-Based Skin Disease Screening Using CNN–Transformer Fusion** is a research prototype for preliminary screening of supported skin conditions. Intended users are general users, healthcare students, researchers, and potentially healthcare professionals evaluating AI-assisted screening.

The system supports awareness and consultation with qualified dermatologists. It does not replace professional diagnosis.

## Requested capabilities

1. Upload a skin image for analysis.
2. Classify supported skin-lesion categories with a trained hybrid EfficientNetV2-S and Transformer model using feature fusion. Swin-T is the proposed Transformer branch, subject to the documented feasibility checks. Fusion is a required project component; standalone models serve as comparison baselines.
3. Display predicted classes and model confidence with appropriate limitations.
4. Show Grad-CAM visualizations of image regions influencing model output, with an accurate description of what the visualization explains.
5. Validate supported formats and basic technical image quality.
6. Provide a responsive dashboard, upload area, real analysis progress, and organized results.
7. Include guidance to consult qualified dermatologists.
8. Permit a future Flutter Android client through an API; mobile implementation is deferred until explicitly requested.

## Technology and appearance

On 2026-10-29 the user approved Phase 7 with training deferred: "yes start wit hthe phase 7". Implement the local responsive dashboard, upload/preview/consent, genuine request progress, API results and honest unavailable/error states now. Real prediction and explanation acceptance remain pending returned evaluated weights and validated explanation support. Phase 8, mobile and deployment require separate approval.

On 2026-10-28 the user approved starting Phase 6 with training deferred to the college supercomputer. Implement and verify the backend independently of model availability. A running API must distinguish liveness from model readiness and return 503 when no verified evaluated hybrid export is configured. Training, metrics and explanation validation remain required later; the Phase 7 ordering override above permits dashboard preparation now.

- Python, PyTorch, FastAPI, EfficientNetV2, and a Vision Transformer branch.
- HTML, CSS, and browser JavaScript without Node.js or a Node build step.
- Original modern healthcare dashboard with white and light-blue styling and simple navigation.
- Persistent development progress and explicit approval before every new phase.

## Supplied research reference

User-supplied title: *Enhanced Skin Disease Classification via Dataset Refinement and Attention-Based Vision Approach* (2025).

https://pmc.ncbi.nlm.nih.gov/articles/PMC11939559/

Phase 1 checked the title and methods using the primary source's indexed full-text excerpts. Live PMC and publisher requests were challenged/rate-limited. See `../reports/literature_review.md` for the limited review and its access constraints. The citation does not establish trained weights or clinical validity for this project.

The user reaffirmed this paper as the primary research reference and explicitly required model fusion on 2026-10-25. Our extension combines CNN and Transformer features, comparing concatenation (E3) and attention-based fusion (E4). Describe it as a project extension inspired by the reference, not the paper's reproduced architecture. Baselines remain necessary for measuring whether fusion helps; a weaker fusion result must be reported honestly and does not authorize silently replacing the required hybrid with a standalone model.

## Decisions needed in Phase 1

- Dataset source, license, access, supported classes, and whether uploaded images match the training-image domain.
- Existing trained weights versus new training; available GPU, compute time, storage, and reproducibility requirements.
- Exact CNN/Transformer variants, fusion design, preprocessing, training strategy, and evaluation protocol.
- Split strategy to prevent patient/image leakage; class imbalance and relevant subgroup evaluation where supported by data.
- Confidence presentation, calibration, uncertain/out-of-distribution input behavior, and scope of Grad-CAM for the fused model.
- Upload size/format limits, quality-check thresholds, storage duration, deletion, and access to results.
- Whether users need accounts and saved screening history. Persistent development records are already required; patient-result history needs a separate product decision.
- Deployment environment and intended research-demo audience.

No dataset files, trained skin-lesion weights, or deployment credentials have been provided. The planned seven-class HAM10000 specification is documented in `DATASET_PLAN.md` and must be checked against the downloaded metadata.

## Master prompt additions and current decisions

The attached master prompt is preserved in `MASTER_PROJECT_PROMPT.md`. It explicitly authorizes Phase 1 only and supersedes the initial implementation order with research before application development.

- Compare E1 EfficientNetV2-S, E2 Transformer (proposed Swin-T), E3 concatenation fusion, and E4 attention fusion. Segmentation is optional and requires suitable verified masks.
- Audit HAM10000 before training. Group related images to prevent leakage, save manifests and mappings, and augment only the training partition.
- Use the same splits/evaluation protocol across experiments. Report per-class precision, sensitivity, specificity, macro-F1, confusion matrices, and applicable ROC-AUC. Record time, parameters, and latency when practical.
- Save real, resumable model checkpoints. Never invent data, results, trained artifacts, or compatibility checks.
- Provide `GET /health`, `GET /model-info`, `POST /predict`, and development `/docs`. Load the selected evaluated model at startup and match its exported preprocessing/mapping.
- The user confirmed Colab access and that HAM10000 is not downloaded. Dataset audit and training are future approved phases.
- Use separate dependency manifests as implementations are added. Phase 1 requires only the Python standard library.
- Organize work under the named `SkinDiseaseAI` repository, with `ai_model/`, `backend/`, deferred `mobile_app/`, `docs/`, and `reports/`; retain `frontend/` for the active web deliverable.
- Prepare reproducibility records, API docs, UML/architecture diagrams, testing reports, user documentation, and academic report/presentation materials incrementally.

Proposed version 1 processes images in memory without accounts or retained screening history. The requirement to preserve development progress remains independent of patient-image retention. Hosting credentials and final deployment audience are not needed for Phase 1 and remain unresolved.
