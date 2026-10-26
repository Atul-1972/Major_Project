# Environment inspection

Inspected 2026-10-25 (Asia/Calcutta).

| Item | Observed value | Implication |
| --- | --- | --- |
| OS | Windows, build 26200, 64-bit | PowerShell instructions; local development |
| Python | CPython 3.11.0, 64-bit | Phase 1 standard-library scripts are supported |
| Git | 2.52.0.windows.1 | Local version control available |
| CPU | Intel Core Ultra 5 125H; 14 cores / 18 logical processors | CPU development and smoke checks |
| Physical RAM | 16,866,729,984 bytes, about 15.7 GiB | Avoid assuming full hybrid GPU training locally |
| Graphics | Intel Arc Graphics | No NVIDIA GPU was reported |
| NVIDIA utility | `nvidia-smi` not found | No NVIDIA CUDA training path verified |
| Disk free before setup | 50,867,523,584 bytes, about 47.4 GiB | Check dataset archive/extraction requirements before download |
| Colab | User confirmed access | Training target; actual GPU allocation still needs verification |
| HAM10000 | User confirmed not downloaded | Dataset audit and training have not started |

The global Python environment had NumPy, Pandas, scikit-learn, Pillow, and Uvicorn metadata, but no torch, torchvision, FastAPI, or pytest metadata. Those global packages were not imported or certified as compatible. The project-local virtual environment is separate and intentionally has no application dependencies in Phase 1.

Hardware inspection initially failed with sandbox WMI access denied. A read-only elevated rerun succeeded. Intel `AdapterRAM` from WMI is not treated as a measurement of usable training VRAM. GPU runtime and memory will be checked directly in the training phase.

Run `python scripts/doctor.py` from the repository to repeat the portable checks. `--require-ml` additionally checks ML package presence and is expected to fail in the empty Phase 1 environment. Neither mode imports PyTorch, tests CUDA, or validates a model. Machine-specific JSON output belongs under ignored `reports/local/`.

## Updates after Phase 1

Current 2026-10-26 update: the user will run the full E1-E4 suite themselves on college compute and explicitly approved Phases 4 and 5 training packaging. The complete ZIP includes both official ImageNet weight caches; their earlier local download failures have been resolved. All four actual pretrained architectures passed real-image CPU diagnostics locally. CUDA/AMP, Linux installation and scheduler/storage compatibility still require actual college execution. Follow `TRAINING_PACKAGE.md`; the staff-operated and Colab notes below are historical.

### College supercomputer handoff, 2026-10-26

The user confirmed: "my college will provide the supercomputer", then clarified that the college has supplied no access details and said its team will train the model. Treat this as college-operated training, not student login access. See `COLLEGE_TRAINING_HANDOFF.md`. Use the college facility as the intended Phase 3 training target; retain Colab as a prepared alternative. Access credentials, GPU allocation and compatibility have not been verified. Before preparing facility-specific commands, obtain the system name/setup guide, GPU model and VRAM, connection method (SSH, Jupyter or web portal), scheduler/queue instructions, persistent storage location and job time limit. Check whether dataset and official pretrained-weight downloads are permitted from the allocated environment.

The current E1 trainer uses one CUDA GPU. Run GPU smoke and one checkpointed epoch on the actual allocation before full training. Multiple-GPU/distributed training is not implemented. Do not assume Google Drive paths or Colab setup cells apply to the college system.

Phase 2 acquired and audited HAM10000 and installed torch 2.9.1+cpu / torchvision 0.24.1+cpu, NumPy 2.3.5 and Pillow 12.0.0 in the project venv. Local CUDA remains unavailable.

Phase 3 added and import-tested scikit-learn 1.7.2 and Matplotlib 3.10.7; `pip check` passed. The actual freeze is `requirements/locks/phase3-windows-py311.txt`. All 55 local tests passed, including deterministic CPU checkpoint recovery using synthetic fixtures. A separate real-image EfficientNetV2-S CPU diagnostic passed forward/backward and checkpoint reload, using explicitly random initialization because local requests for official ImageNet weights were reset. This is not model-performance evidence or a trained classifier.

The user subsequently reported Colab is working and the GPU probe returns True. No GPU model smoke/training/evaluation evidence has yet been received or executed by the local agent. The notebook records the actual allocated GPU, software versions and initialization hash before training; the original environment table above is a historical Phase 1 inspection.
