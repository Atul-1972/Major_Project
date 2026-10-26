# Dataset plan

## Current state

Phase 2 completed on 2026-10-25. Official ISIC data contains 10,015 audited images and 7,470 lesion IDs; actual image/class counts match the table below. The frozen grouped splits contain 7,011 training, 1,502 validation and 1,502 test images, with every class represented and zero prohibited overlaps. See `phase-reports/phase-2.md`, `DUPLICATE_REVIEW.md` and `../reports/phase2-data-summary.json` for actual findings and limits. No training has run; Phase 3 requires approval.

## Initial source and scope

Use the original [HAM10000 dataset record](https://doi.org/10.7910/DVN/DBW86T) and [data descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC6091241/). It describes 10,015 dermoscopic images in seven imbalanced classes, including multiple images of some lesions. The descriptor reports CC BY-NC 4.0 for the dataset. Its article license is distinct from the dataset license. Live Dataverse terms were behind a browser check during Phase 1; verify the exact downloaded version's current terms and record them before use or redistribution.

| Proposed index | Source label | Display name | Published image count |
| --- | --- | --- | ---: |
| 0 | akiec | Actinic keratoses / intraepithelial carcinoma | 327 |
| 1 | bcc | Basal cell carcinoma | 514 |
| 2 | bkl | Benign keratosis-like lesions | 1099 |
| 3 | df | Dermatofibroma | 115 |
| 4 | mel | Melanoma | 1113 |
| 5 | nv | Melanocytic nevi | 6705 |
| 6 | vasc | Vascular lesions | 142 |

This is the planned class order. Phase 2 must generate and validate the saved mapping from the audited labels; every experiment and backend must use that mapping. Do not add eczema, psoriasis, or general skin-disease classes to this dataset's classifier.

## Acquisition in the next approved phase

1. Open the original record, verify permissions/attribution requirements, and record the dataset version and access date.
2. Download the metadata and original image archives through the provider's supported access path. Do not use a pre-augmented or pre-split mirror without a documented reason and provenance review.
3. Keep originals unchanged under ignored `data/ham10000/raw/`; place extracted originals under ignored `data/ham10000/images/` and the metadata CSV at `data/ham10000/HAM10000_metadata.csv`.
4. Record original filenames, provider checksums where available, and locally computed SHA-256 hashes. Read actual archive sizes before downloading/extracting; the local free-space measurement does not guarantee future capacity.
5. On Colab, use a private durable storage location. Do not publish images, private paths, or credentials in notebooks.

No automated download occurred in Phase 1. Phase 2 uses the official ISIC distribution after Harvard's API returned HTTP 403. See `DATASET_SOURCE.md` for verified source links, CC BY-NC 4.0 attribution, and metadata derivation. The derived table is named `metadata.csv`; it does not pretend to be Harvard's original CSV or supply missing demographics. Commands are in `PHASE_2.md`.

## Audit acceptance criteria

- Required columns include `image_id`, `lesion_id`, and `dx`; inspect the actual release before assuming any other fields exist.
- Check missing/duplicate identifiers, unknown labels, missing and extra image files, file readability, dimensions, channels, and metadata inconsistencies.
- Count classes and unique lesion groups and compare against the documented source release, explaining any differences.
- Hash decoded pixel data to detect identical images with different filenames. Keep identical/near-duplicate or related images together; quarantine contradictory labels rather than guessing a correction.
- Verify whether genuine patient IDs exist. Never infer patient identity from age/sex/site or claim patient-disjoint splits when only lesion IDs are available.
- Record missing demographic fields and representation limits. Do not infer skin tone from pixels or claim subgroup validation without suitable labels and sample sizes.

## Split plan

Propose approximately 70% training, 15% validation, 15% locked test, with seed 42. Partition groups, not individual image rows. Prefer real patient IDs when available; otherwise use lesion IDs and explicitly disclose residual patient overlap risk. Connect duplicate-image groups before splitting. Seek class balance while honoring group boundaries; actual ratios may differ.

Save image-level manifests containing split, image ID, group ID, label, relative file path, and checksum. Assert zero cross-split group or exact-duplicate overlap and verify class coverage. Missing groups or labels fail the checkpoint. If a class cannot appear in every split under valid grouping, diagnose and revise the protocol before training; do not fall back silently to image-level random splits.

Augmentation, resampling, and class-weight calculation use training data only. Freeze the manifests before E1; all comparisons reuse them. Validation controls tuning and checkpoint selection; the test set does not select architecture or thresholds.

## Smartphone-image investigation

[PAD-UFES-20's original record](https://data.mendeley.com/datasets/zr7vgbcyr2/1) describes smartphone clinical images, patient/lesion identifiers, six categories, and CC BY 4.0. It is a candidate for a separate domain-validation study, not an automatic extension of HAM10000. Its labels do not match HAM10000 one-to-one; any subset mapping and patient-group protocol require explicit design. No PAD-UFES-20 data has been downloaded.

Technical image readability/quality checks cannot establish that an image is dermoscopic or in distribution. Initial web results must disclose the dermoscopic research domain. Optional segmentation requires verified image-mask pairs and their permissions; no masks have been supplied.
