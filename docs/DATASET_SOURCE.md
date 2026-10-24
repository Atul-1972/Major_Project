# Phase 2 source and attribution

Verified on 2026-10-25 (Asia/Calcutta).

The Harvard Dataverse API returned HTTP 403, and the human page returned a browser challenge. No attempt was made to bypass that access control. The alternate source is the publisher-supported [official ISIC Challenge data distribution](https://challenge.isic-archive.com/data/#2018).

For 2018 Task 3, that page provides the HAM10000 training images, diagnosis ground truth, and supplemental image-to-lesion grouping metadata. The grouping schema is explained by the [ISIC supplemental-data announcement](https://forum.isic-archive.com/t/task-3-supplemental-information/430). Only this training cohort is used to construct our own grouped train/validation/test partition; challenge validation/test files are not mixed in.

| Original file | Official URL |
| --- | --- |
| Images | https://isic-archive.s3.amazonaws.com/challenges/2018/ISIC2018_Task3_Training_Input.zip |
| One-hot diagnoses | https://isic-archive.s3.amazonaws.com/challenges/2018/ISIC2018_Task3_Training_GroundTruth.zip |
| Lesion groups | https://isic-archive.s3.amazonaws.com/challenges/2018/ISIC2018_Task3_Training_LesionGroupings.csv |

## Terms and credit

The source page links [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Preserve credit, license links, and descriptions of modifications; the intended use here is noncommercial academic research. The repository's MIT license covers original code, not these data or pretrained weights. No image redistribution or commercial deployment is performed in Phase 2.

Credit the HAM10000 contributors: ViDIR Group, Department of Dermatology, Medical University of Vienna; Tschandl, Rosendahl, and Kittler's [HAM10000 data descriptor](https://doi.org/10.1038/sdata.2018.161). Also cite the [ISIC 2018 challenge report](https://arxiv.org/abs/1902.03368) when using its distribution. Original archive contents, including embedded notices, remain in ignored `raw/` storage.

## Provenance and modifications

`data/ham10000/provenance.json` records the exact download URLs, entity tags, source content lengths, locally computed SHA-256 values, and acquisition times. Entity tags are recorded as source version identifiers, not assumed to be MD5 checksums. Locally computed SHA-256 checks integrity of our saved files; it is not a separately published provider checksum.

`metadata.csv` is our derived canonical table. It is a checked one-to-one join of the original image/one-hot diagnosis table and lesion-group CSV, with diagnosis codes lowercased to the planned mapping. It is not the original Harvard `HAM10000_metadata.csv`. No labels or patient attributes are inferred. Demographics are absent from this alternate metadata distribution and are explicitly reported as unavailable.

Images remain unchanged on disk. Audit features and perceptual thumbnails are computed in memory; only hashes/statistics and group identifiers are recorded. Runtime preprocessing normalizes orientation, converts to RGB, letterboxes to 224 pixels, and normalizes channels. Flips and modest color jitter apply to training samples only. This is our experimental preprocessing, not an exact reproduction of the reference paper.
