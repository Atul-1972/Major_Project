# Decision record

## 2026-10-25 — confirmed constraints

- Application name: SkinDiseaseAI.
- Initial location: the Desktop `Major Project` workspace. During Phase 1, consolidated into its `SkinDiseaseAI` subdirectory to match the requested repository name.
- Target: a research web application; mobile work is deferred until the user commands it.
- Backend: Python, with FastAPI preferred; machine learning uses PyTorch.
- Node.js is excluded. Proposed frontend is HTML/CSS/browser JavaScript, served by the Python application.
- Work proceeds in approved phases. The later attached master prompt explicitly authorizes Phase 1 only.
- Development history is kept in local checkpoint files and Markdown reports.

## Pending architecture decisions

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
