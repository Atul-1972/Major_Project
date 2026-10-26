# Phase 2 perceptual candidate review

Date: 2026-10-25 (Asia/Calcutta).

The first actual-cohort audit decoded all 10,015 source images: every image was RGB at 600 x 450 pixels, with the expected seven-class counts and 7,470 source lesion IDs. It found two exact pixel-duplicate groups and 58 perceptual candidate pairs. Eleven candidate pairs had differing source labels, so the audit stopped before generating any splits. No exact pixel or source-lesion label conflicts were reported.

The failed report and image records are preserved under ignored `data/ham10000/audit_initial/`. The private comparison sheet is `reports/local/near-duplicate-review.png`. These are data artifacts and must not be committed or published with the source code.

## Technical review and decision

Codex inspected all eleven cross-label pairs side by side at 390 x 292 pixels per image, derived from the 600 x 450 originals. Each showed visible differences in central outline/internal structure and/or surrounding hair, spots, and field borders. They were recorded as distinct image structures caught by the coarse perceptual heuristic. This is an agent's technical file-identity review, not a dermatologist's review, clinical confirmation of labels, or proof that lesions/patients differ.

Source images, metadata and diagnoses remain unchanged. The hash-distance and thumbnail-difference thresholds remain unchanged. All 58 candidate edges, including the eleven reviewed cross-label pairs, remain connected for splitting. This conservative grouping prevents those pairs from crossing partitions even if visual review missed a relationship. No images are removed to force the expected counts.

| Source label combination | Reviewed pairs |
| --- | ---: |
| bcc / nv | 1 |
| bkl / nv | 2 |
| bcc / df | 1 |
| mel / nv | 6 |
| mel / bkl | 1 |

## Reproducible evidence

`data/ham10000/near_duplicate_review.json` contains each pair's identifiers, original file SHA-256 hashes, a concrete visual rationale, the technical decision `distinct_images_keep_grouped`, and the full canonical metadata SHA-256. The data pipeline discovers this local file or accepts an explicit `--duplicate-review <path>`.

The audit rejects mismatching source hashes, invalid decisions, duplicate review entries and reviews that no longer match detected cross-label candidates. Without an applicable review, a cross-label perceptual candidate still fails. Exact-pixel and source-lesion label conflicts always fail, including when a review is supplied. New uncertain or conflicting duplicates require investigation; this file is not a blanket waiver.

The resulting audit records the review's hash/count. The immutable manifest bundle copies `duplicate_review.json`, checksums it, and includes its hash in the input fingerprint. Phase completion verifies the audited review hash against the frozen bundle. Editing the review requires a new manifest output directory rather than modifying an existing experiment's splits.

Keep the local review with the data backup. For Colab, copy it privately to `SkinDiseaseAI/data/ham10000/near_duplicate_review.json` on Drive before preparing this cohort. It contains per-image source records and is excluded from Git. A fresh clone alone does not contain this review and will correctly stop on the unreviewed candidates.

Forty-two automated tests passed after implementing this procedure and the frozen-review completion check. Synthetic review fixtures test software behavior only; the actual image audit and batches are separate evidence in the Phase 2 report. Perceptual matching can miss related images or group unrelated images. Patient disjointness remains unknown because source patient IDs are absent.
