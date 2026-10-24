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
