# Windows setup and Phase 1 verification

The files are already created. Open PowerShell and enter the repository:

```powershell
Set-Location -LiteralPath 'C:\Users\ATUL KUMAR AGRAHARI\OneDrive\Desktop\Major Project\SkinDiseaseAI'
python --version
git --version
```

Target Python is 3.11. Phase 1 needs no package download. A local `.venv` is created during setup; if it is absent on a new checkout, create it:

```powershell
python -m venv .venv
```

Use the environment's executable directly. Activation and PowerShell execution-policy changes are unnecessary:

```powershell
.\.venv\Scripts\python.exe scripts\doctor.py --output reports/local/environment.json
.\.venv\Scripts\python.exe -m compileall -q scripts
git status --short --branch
```

Success means the verifier reports `"passed": true`, exits with code 0, and produces the JSON report. Compilation should exit 0 with no errors. Git must report branch `main`. No web server or model is started by these commands.

Optional future dependency-presence gate:

```powershell
.\.venv\Scripts\python.exe scripts\doctor.py --require-ml
```

This intentionally exits 1 now because ML packages are absent. Diagnose the listed missing packages in the ML setup phase; do not interpret it as failed Phase 1 readiness or claim training is possible yet.

Save progress after meaningful work:

```powershell
.\.venv\Scripts\python.exe scripts\checkpoint.py --summary 'Describe saved work and actual checks' --next 'Describe the next approved action'
```

## Git

The local repository is initialized on `main`. No GitHub repository, remote, or public upload is created. Do not add datasets, images, secrets, or large weights. Project history files are tracked; environments and machine-specific reports are ignored. Review `git status` and staged changes before committing.

If Git has no author identity when you choose to commit, set your own identity locally; no invented identity should be substituted. Remote publication and credentials are separate from local setup.

## Colab preparation

User access is confirmed. In the later approved training phase, choose a GPU runtime and check the actual allocation. These inspection cells are standard Python/shell instructions, not an implemented training notebook:

```python
import sys
print(sys.version)
```

```python
import torch
import torchvision
print(torch.__version__, torchvision.__version__)
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0))
```

Do not assume these imports work until executed in Colab. If they fail or no GPU is available, diagnose before training. Future phase files will provide exact installation/training commands once implemented and verified. Checkpoints must be written to approved durable storage, not only Colab's temporary runtime disk.
