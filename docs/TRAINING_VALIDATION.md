# Training package validation

Recorded 2026-10-26. Local machine: Windows, Python 3.11, torch 2.9.1+cpu, torchvision 0.24.1+cpu. No NVIDIA GPU is available locally. This record is about implementation behavior, not classification performance.

## Checks performed

- Original 55-test regression suite passed after generalizing the training/model construction paths.
- Full suite with model/recovery/integrity checks passed 67 tests before the final export checks were added. The seven final package/orchestration/export tests passed, including the two additional checks below.
- Actual E2/E3/E4 architectures passed seven-logit/finite-output checks in their dedicated real-image diagnostics; synthetic unit tests additionally checked backbone freezing, head/backbone gradients and state reload. Frozen backbones retain buffers during warm-up.
- E1, E2, E3 and E4 each passed official-pretrained CPU diagnostics on real frozen train/validation images: input `[2, 3, 224, 224]`, output `[2, 7]`, finite forward/backward behavior, optimizer updates, and matching checkpoint reload. These disposable smoke batches are not trained research classifiers and produce no research metrics. Approximate diagnostic runtimes were 5.00, 5.60, 10.06 and 8.03 seconds respectively, not full-epoch estimates.
- Synthetic fixtures verify deterministic interrupted-epoch recovery and resumed model/optimizer selection behavior. All four configurations use the same engine; the extended configurations have their own epoch-recovery tests.
- The suite-selection tests ensure all four validation choices are fixed before any held-out evaluation, keep a better baseline visible, and select a required hybrid even when it does not outperform the baseline.
- A randomly initialized actual E4 architecture in a clearly synthetic test run was exported and reloaded in a fresh Python process. Probe outputs matched; altered exported configuration was rejected by checksum. This checks file compatibility, not trained-model quality.
- Package checks reject changed, missing and escaping file paths; CPU research execution is refused before acquisition; paused runs resume and do not open test evaluation.
- Both official initialization downloads matched their Torchvision filename hash prefixes and were loaded successfully. Full cached file SHA-256 values are below.
- `pip check` passed. Each Linux shell launcher passed Git Bash `bash -n` individually. Bash syntax validation does not establish Linux driver/scheduler compatibility.

| Initialization | SHA-256 |
| --- | --- |
| EfficientNetV2-S | `dd5fe13b1d60ec15317ccc8ca158186e134d3366c3dde9cb9a4e301f2dc66c74` |
| Swin-T | `704ceda373461b0a224fcdddd75cd2a5e9f8064512ed47adbddef7f343fd147b` |

The frozen split fingerprint is `59c4dc4192093bb29e33e7d1d79c8937819d7d4e0fd05a0e552009d76e3a43fd`. Original images are carried as the provider archive, with verified acquisition receipts and source/terms documentation. The complete transfer receipt records the final ZIP hash and size.

## Still requires actual college execution

CUDA/AMP compatibility, GPU memory use, scheduler configuration, shared-filesystem locking/persistence, Linux package installation and job recovery are unverified. No real E1-E4 fitting, final-test scores, fusion improvement or clinical validity is claimed. Setup needs a compatible GPU environment; no promise of zero errors on an unknown system is supportable. The package checks fail explicitly instead of substituting random weights or fake results.

Archive construction/extracted-package checks are recorded in the development checkpoint and local validation report after the ZIP is generated. Do not confuse software-test or CPU diagnostic success with completed research training. Run `START_HERE.md` instructions on an allocated GPU and return the complete run directory for review.
