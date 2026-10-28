# Decision record

## 2026-10-28: resume with training deferred; prepare Phase 6

The user requested continuing beyond training while it will run on the college supercomputer, then explicitly approved: "Yes, start Phase 6 with training deferred". Backend preparation is now authorized before research execution finishes. Keep Phases 3-5 evidence open rather than marking training skipped/completed. Implement the FastAPI service with genuine unavailable inference by default, a trusted returned-export adapter, bounded in-memory uploads, no retained images/history, CPU inference and serialized model execution. Grad-CAM remains unavailable pending implementation/validation. Phase 6 real-model acceptance remains open; Phase 7, mobile and deployment are unapproved. Standing source-only GitHub backup resumes; authenticated sync of the saved setup and initial backend was verified in this session.

## 2026-10-25 — confirmed constraints

- Application name: SkinDiseaseAI.
- Initial location: the Desktop `Major Project` workspace. During Phase 1, consolidated into its `SkinDiseaseAI` subdirectory to match the requested repository name.
- Target: a research web application; mobile work is deferred until the user commands it.
- Backend: Python, with FastAPI preferred; machine learning uses PyTorch.
- Node.js is excluded. Proposed frontend is HTML/CSS/browser JavaScript, served by the Python application.
- Work proceeds in approved phases. The later attached master prompt explicitly authorizes Phase 1 only.
- Development history is kept in local checkpoint files and Markdown reports.

## Pending architecture decisions

On 2026-10-26 the user requested automatic GitHub pushes after changes and phase completion. Persist that authorization in `AGENTS.md`, enable `.project/github_sync.json`, and call the guarded standard-library sync helper after normal checkpoints. Save locally first; keep commits for retry on a network/authentication failure, refuse non-fast-forward history changes, and keep private assets excluded. Appropriate validation remains an agent responsibility before checkpoints. No continuous file-save watcher or startup service is installed.

Latest 2026-10-26 override: the user will run training and explicitly authorized Phases 4 and 5 for all four models. Prepare a single private source/data/official-initialization ZIP with Linux setup, one-GPU sequential E1-E4 fitting, checkpoint recovery, validation-first hybrid selection, fixed test reporting and clean-process export. Earlier staff-operated assumptions are superseded. Preserve the frozen splits and old artifacts; do not claim completed GPU experiments or expand to application/mobile work.

The user clarified that no facility details have been provided and the college team said it will train the model. Prepare a staff-operated handoff instead of requiring student credentials. `COLLEGE_TRAINING_HANDOFF.md` accompanies the unchanged ZIP, preserves the frozen E1 protocol, and requests smoke/one-epoch evidence followed by the complete private run artifacts. No communication, upload or college execution has been performed by the agent.

Latest compute choice, 2026-10-26: the user confirmed "my college will provide the supercomputer". Prepare Phase 3 for the college facility once its access, GPU, software, scheduler and persistent-storage details are supplied. Keep the existing E1 protocol and frozen splits; verify compatibility and one durable epoch checkpoint before full training. No remote access or training is verified, and this does not approve later model phases. Colab remains an alternative.

See `ARCHITECTURE.md`, `DATASET_PLAN.md`, and `EXPERIMENT_PLAN.md` for Phase 1 design choices and their validation gates. Hosting and access controls remain to be resolved before deployment.

## 2026-10-25 — master prompt and user reply

- Preserve the master prompt as received in `MASTER_PROJECT_PROMPT.md`.
- Research-first order supersedes the initial web-foundation-first plan.
- Investigate HAM10000 as the initial dermoscopic classification dataset. User confirmed it is not downloaded.
- User confirmed Google Colab access; train on a GPU runtime when one is actually allocated. Local environment is suitable for development and CPU checks; NVIDIA CUDA training is not available on the detected Intel GPU.
- Use EfficientNetV2-S for E1 and propose Swin-T for E2 to reduce the initial compute burden relative to ViT-B/16. E3/E4 compare concatenation and two-branch attention. These are experiment designs, not proven improvements.
- Proposed version 1 has no accounts or persistent user-image history. Process uploads in memory, exclude images from logs, and require explicit opt-in before any future retention feature.
- Use Python-served templates and browser JavaScript for the web client. No Node tooling.
- Create only a scope note in `mobile_app/`; no Flutter dependencies or implementation are authorized now.
- MIT covers original repository code; dataset, paper, pretrained weights, and third-party code retain their own terms. No dataset or model redistribution is implied.

## 2026-10-25 — reference and fusion clarification

- User instruction: "use this reseach paper as refrence and here we use fusion of model", referring to https://pmc.ncbi.nlm.nih.gov/articles/PMC11939559/.
- Treat that paper as the primary research reference. Attribute the reference method and our CNN–Transformer feature-fusion extension separately.
- Fusion is required: EfficientNetV2-S plus proposed Swin-T, with E3 concatenation and E4 attention-based fusion. E1/E2 remain comparison baselines.
- Select between validated fusion candidates using the predeclared validation protocol. If fusion underperforms a baseline, report it honestly; do not silently change the project's required architecture. Resolve an inability to pass export/verification checks before integration.
- This is a Phase 1 requirements clarification. Phase 2 remains unapproved; no dataset processing, training, or mobile work begins.

## 2026-10-25 — preserve project chat history

- User instruction: "i want to save all the chat history of this project".
- Archive available user/assistant conversation messages directly from the local project session record, separately from progress summaries. Include progress updates, question/answer replies, and the preserved master prompt.
- Keep transcripts and source registration local and ignored by Git. Add a manual exporter, checkpoint-triggered refresh, and a watcher for the active session. A watcher must be restarted if its process or the computer stops.
- Exclude internal instructions, private reasoning, internal tool payloads, and environment-only UI snapshots. Do not reconstruct missing messages or claim arbitrary images/attachments were copied.
- This maintenance request is authorized independently of the pending dataset phase; Phase 2 remains unapproved.

## 2026-10-25 — Phase 2 authorization and implementation

- User approved Phase 2 with "start phase 2". Dataset processing is authorized; training remains a separately approved Phase 3.
- Harvard's API returned HTTP 403. Use the documented official ISIC 2018 Task 3 training distribution with its CC BY-NC 4.0 notice, original labels, and supplemental lesion identifiers. Never substitute an undocumented pre-split/augmented mirror.
- The canonical metadata is a one-to-one join named `metadata.csv`, retaining original lesion IDs and diagnosis-confirmation text. Patient/demographic values are not invented.
- Prefer actual patient IDs when supplied; otherwise union lesion relations, exact duplicates, and conservative perceptual matches. The ISIC source used here has no patient IDs.
- Shared preprocessing is RGB/orientation normalization and aspect-preserving 224-pixel letterboxing with ImageNet normalization. Training-only flips/color jitter are configured; rotation is initially omitted to avoid an additional crop/geometry change before review.
- Freeze class mappings, manifests, and preprocessing together, with hashes and a seed-42 class-aware group assignment. Reject changed existing bundles rather than silently regenerating splits.
- Windows torch/torchvision 2.9.1/0.24.1 from PyPI import as CPU builds; NumPy 2.3.5 and Pillow 12.0.0 are installed. CPU operation and `pip check` passed; Colab execution remains unverified.

## 2026-10-25 — Phase 2 resumption and actual duplicate review

- User requested "resume Phase 2" after the earlier pause. Resume the data phase only; training remains unapproved.
- Added bounded atomic-status retries after an observed Windows file-lock failure; partial downloads are preserved.
- The first complete image audit stopped on eleven cross-label perceptual candidates. Technical visual inspection found distinct image structures; preserve the failed audit and per-pair rationale/hash evidence locally. This does not clinically validate source labels or establish independent patients/lesions.
- Keep all candidate pairs connected, retain every source image/label, and keep the original matching thresholds. Permit only explicit hash-bound false-match reviews; exact-pixel/source-lesion conflicts always fail. Freeze review evidence with the manifest bundle. See `DUPLICATE_REVIEW.md`.

## 2026-10-25 approval; 2026-10-26 handoff — Phase 3

- User approved "so start phase 3" and requested pause/resume, then asked for beginner Colab instructions. After a browser fetch error, the user reported Colab works and its GPU probe returns True. That report is separate from actual GPU model execution evidence.
- Implement the planned E1 protocol in `ai_model/config/e1.json`: three warm-up plus up to twenty fine-tuning epochs, batch eight, train-only inverse-frequency weights, AdamW/cosine scheduling, patience five and validation macro-F1 selection. Preserve 224-pixel Phase 2 letterboxing, rather than adopting the pretrained enum's 384-pixel crop transform.
- Save initial and completed-epoch state to durable Drive storage; repeat unfinished epochs. `last.pt` also contains best weights so an interrupted best-file write can be repaired. Reject changed source/config/packages/splits on resume. Handle AMP overflow through scaler skip/backoff; count only applied optimizer updates.
- Keep training restricted to train/validation. Final-test evaluation requires a finished run and immutable validation selection, and saved reports cannot switch to another selection.
- Prepare a small private allowlisted transfer bundle. Download original images and pretrained initialization inside Colab to avoid the user's slow laptop upload. No external upload or Colab execution was performed by the agent.
- All 55 local tests and the real-image, actual-network CPU diagnostic passed. Local official-weight requests were reset; the diagnostic explicitly used random initialization and is not research training. Phase 3 remains in progress until GPU smoke, resumable training and evaluated results are reviewed. Phase 4 remains unapproved.
