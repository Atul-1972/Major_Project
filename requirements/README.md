# Dependency policy

Phase 1 has no third-party Python dependencies. The reusable environment checker and checkpoint utility run with the standard library.

Use a repository-local virtual environment instead of the globally installed packages. ML-training and backend manifests will be added with their implementations. Installation success, import checks, and `pip check` must be recorded before calling any dependency set tested.

Phase 2 installed and import-tested `torch==2.9.1` and `torchvision==0.24.1` on Windows Python 3.11. Their runtime versions report `2.9.1+cpu` / `0.24.1+cpu`; a CPU tensor calculation and `pip check` passed. The dedicated PyTorch CPU index supplied no compatible wheels in this session; the same matched versions from PyPI worked. `torch-cpu.txt` therefore delegates to the verified Windows manifest. This is a reproducible local choice, not a claim that it is the newest release. The pair appears in the [official previous-version instructions](https://pytorch.org/get-started/previous-versions/).

| File | Purpose |
| --- | --- |
| `phase1.txt` | Standard-library-only preparation |
| `data.txt` | Pinned NumPy, Pillow, and pytest for Phase 2 |
| `torch-windows.txt` | Matched Windows CPU PyTorch/Torchvision from PyPI |
| `phase2-windows.txt` | Combined Phase 2 installation entry point |
| `locks/phase2-windows-py311.txt` | Actual local installed-package freeze, including transitive dependencies |
| `phase3-windows.txt` | Phase 2 plus locally verified scikit-learn 1.7.2 / Matplotlib 3.10.7 |
| `phase3-colab.txt` | Evaluation/plotting pins only; preserve Colab's CUDA torch/torchvision pair |
| `training-linux.txt` | Non-torch requirements for all-model college GPU training; `setup_training.sh` installs the matched CUDA torch/torchvision pair separately |
| `locks/phase3-windows-py311.txt` | Actual Phase 3 local dependency freeze |
| `backend.txt` | Phase 6 FastAPI/Uvicorn/multipart/Pydantic/Pillow dependencies; no GPU required for missing-model operation |
| `backend-test.txt` | Backend dependencies plus HTTP test client and pytest |
| `locks/backend-windows-py311.txt` | Actual combined Phase 6 local Windows Python 3.11 environment |

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/phase2-windows.txt
.\.venv\Scripts\python.exe -m pip check
```

Recheck maintained versions and the actual Colab Python/CUDA runtime before pinning/installing. Do not downgrade or replace Colab's installed PyTorch blindly, and do not mix unrelated torch/torchvision versions. Record package versions, runtime hardware, and a lock/freeze with each experiment. CPU inference and Colab GPU training may need different wheel indexes while retaining compatible library versions.
