# Initial literature and source review

Reviewed on 2026-10-25 (Asia/Calcutta). This is a Phase 1 planning review, not a systematic review or independent reproduction.

## User-supplied reference

[Enhanced Skin Disease Classification via Dataset Refinement and Attention-Based Vision Approach](https://pmc.ncbi.nlm.nih.gov/articles/PMC11939559/) (2025), publisher [Bioengineering 12(3), 275](https://www.mdpi.com/2306-5354/12/3/275).

The title matches the user's reference. The indexed methods describe contrast-related preprocessing followed by a Vision Transformer, using HAM10000 and a separate broader skin-disease dataset. Reported experiments vary train/test ratios. This supports investigating preprocessing/attention; it does not establish the proposed EfficientNetV2-S/Swin fusion design or its performance. We will use saved grouped train/validation/test splits and independent baselines instead of treating the reported results as our target or reproduction.

Access limitation: live PMC returned a browser challenge and the publisher returned HTTP 429. The review used primary-source indexed text exposed by search, not an inspected code repository, raw dataset, or complete reproducibility audit. Do not claim the paper's implementation or split integrity was independently verified. A fuller critical review can be added when source access permits.

## Dataset sources

- [HAM10000 original data descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC6091241/) and [dataset DOI](https://doi.org/10.7910/DVN/DBW86T): source for the initial dermoscopy task, documented counts, grouping needs, and reported noncommercial dataset license. The live Dataverse terms page was challenged; verify download-version terms before use. Our audit is still pending.
- [PAD-UFES-20 original dataset record](https://data.mendeley.com/datasets/zr7vgbcyr2/1): candidate clinical smartphone-image domain with patient/lesion metadata and a different class taxonomy. This record was accessible and lists CC BY 4.0. No claim of compatibility with our eventual trained model is made.

## Model and dependency sources

- [EfficientNetV2-S, Torchvision](https://docs.pytorch.org/vision/0.24/models/generated/torchvision.models.efficientnet_v2_s.html): confirms architecture/weight API and published preprocessing recipe. Our common-resolution experiment will explicitly record its departure from that recipe.
- [Swin-T, Torchvision](https://docs.pytorch.org/vision/0.24/models/generated/torchvision.models.swin_t.html): confirms supported Transformer architecture and weight API. Resource suitability remains an experiment.
- [PyTorch previous versions](https://pytorch.org/get-started/previous-versions/) and [Torchvision compatibility table](https://github.com/pytorch/vision): a documented matched-version reference for future dependency setup, not a claim of installed/tested packages.

## Research contribution to test

The project's contribution is a reproducible comparison of CNN, Transformer, and two fusion strategies under a common leakage-aware protocol, with scoped explanations and an honest research web interface. Neither higher accuracy from fusion nor clinical/general-smartphone suitability is assumed.
