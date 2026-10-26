# Phase 5: fusion training/export implementation ready; evidence pending

The user explicitly authorized Phase 5 on 2026-10-26 while requesting all four models. E3/E4 implementation is available; no actual fusion research training has run.

- E3 concatenates the pooled 1,280-dimension CNN and 768-dimension Swin-T feature vectors before classification.
- E4 projects each vector to 256 dimensions, adds learned branch embeddings, performs four-head attention on two tokens, then residual normalization, mean pooling and classification. This is branch-feature attention, not a pixel explanation.
- Both branches initialize independently from their official ImageNet files. No trained-baseline transfer is presumed. Warm-up freezes both complete backbones while training the fusion/classification head; fine-tuning unfreezes both.
- The suite trains E1-E4 sequentially on identical immutable manifests, then fixes every candidate and selects the hybrid by validation macro-F1 before any held-out scores. A stronger baseline is recorded honestly and does not silently replace the hybrid.
- Separate fixed-checkpoint evaluation, comparison records, inference-only weights/metadata, integrity hashes and clean-process probe verification are implemented. Export uses the validation-selected hybrid. The package includes the dataset/provider receipts and both pretrained caches; it excludes any claim of already trained skin-lesion weights.

Both actual pretrained fusion architectures passed real-image CPU forward/backward/checkpoint diagnostics. Synthetic unit tests verify both-branch gradients, frozen buffers, exact epoch recovery, validation-before-test selection, and clean-process E4 export/reload with tamper rejection. See `../TRAINING_VALIDATION.md`.

Actual GPU compatibility/AMP/memory use, checkpoint persistence, research training, final-test metrics, measured fusion gains, Grad-CAM/explanation validation and real trained export verification remain pending. Optional segmentation has not been implemented and has no supplied masks. No backend, dashboard, mobile or deployment work is authorized by this training-package request. Phase 5 remains in progress.

Final package evidence: 69 repository tests passed in 40.09 seconds; 58 tests passed from the extracted ZIP in 29.16 seconds. Receipt SHA-256 and ZIP CRC checks passed, as did 66 shipped-file hashes and extracted-source imports. The 2,973,268,386-byte archive contains the original dataset and both official ImageNet caches. Aggregate evidence is `../../reports/training-package-summary.json`; this still does not establish GPU execution or trained-model quality.
