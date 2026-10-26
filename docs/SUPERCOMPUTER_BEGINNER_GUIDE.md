# Run SkinDiseaseAI yourself on the college supercomputer

The college has said it will provide your own login. This walkthrough covers the complete package for E1 EfficientNetV2-S, E2 Swin-T, E3 concatenation fusion and E4 attention fusion. Training has not yet run on the college system.

The existing ZIP is `artifacts/training-package/SkinDiseaseAI-all-models-training.zip` (about 3 GB). It already contains the dataset, frozen splits and official initialization files. You do not need to upload the whole workspace or the Windows virtual environment. This beginner guide is a separate companion to the ZIP; `START_HERE.md` inside the ZIP contains its technical instructions.

## Choose the route that matches your college access

| What you have | Follow this route | Where training runs |
| --- | --- | --- |
| A pen drive and a college computer | Route A below: carry the ZIP, then upload using the college computer/login | The allocated college GPU |
| Your own laptop and an SSH login | Steps 2-3 (Route B), then Steps 4-9 | The allocated college GPU |
| A website with a login window | Route C: browser portal/Jupyter, later in this guide | The portal's allocated GPU job/session |
| A Linux desktop or terminal login supplied at college | Route D: college Linux login, later in this guide | The allocated college GPU |

A pen drive is a way to carry files. You still use your college login to reach the training system. The GPU allocation and the training/checkpoint commands are shared across these routes. Follow Step 1 first; the college's actual server, paths and scheduler settings replace the placeholders.

## 1. Get the connection and job details

Ask the college administrator for these details with your login:

| Detail | What to ask |
| --- | --- |
| Connection | SSH host/IP and port, or browser portal URL; VPN/MFA instructions if required |
| Account | Your username and the college's own authentication instructions |
| GPU access | GPU type/memory, scheduler name and job-submission instructions |
| Job settings | Assigned GPU partition/queue, project/account name if required, and resource/time limits |
| Storage | Private persistent project directory with enough quota; request at least 20 GiB free after unpacking |
| Python | How to activate Python 3.11 or a compatible CUDA PyTorch environment, and where package installation is allowed |

You can send: "I will train four PyTorch skin-lesion models using one NVIDIA GPU. Please provide my login/connection instructions, GPU job-submission example, persistent storage directory and Python environment instructions. The package is about 3 GB and saves resumable checkpoints."

All `YOUR_...` values below are placeholders. Replace them with the college's assigned values. Use passwords, MFA and private keys only in the college's authentication flow; do not paste them into this project or chat.

## Route A. Carry the files on a pen drive

### A1. Copy onto the pen drive using your laptop

Connect the pen drive and check its drive letter in File Explorer. The commands below use **`E:` as an example**; replace it with your actual pen-drive letter. Check there is enough free space for the approximately 3 GB ZIP, this guide and later training results; result size depends on the run. These commands copy files and do not format the drive.

In **PowerShell on your laptop**:

```powershell
Set-Location -LiteralPath (Join-Path $env:USERPROFILE 'OneDrive\Desktop\Major Project\SkinDiseaseAI')
New-Item -ItemType Directory -Path 'E:\SkinDiseaseAI-transfer' -Force
Copy-Item -LiteralPath '.\artifacts\training-package\SkinDiseaseAI-all-models-training.zip' -Destination 'E:\SkinDiseaseAI-transfer\'
Copy-Item -LiteralPath '.\docs\SUPERCOMPUTER_BEGINNER_GUIDE.md' -Destination 'E:\SkinDiseaseAI-transfer\'
Get-FileHash -LiteralPath 'E:\SkinDiseaseAI-transfer\SkinDiseaseAI-all-models-training.zip' -Algorithm SHA256
```

Compare the ZIP hash with Step 4, then use Windows **Eject** before unplugging the pen drive. You can also copy these two files using File Explorer.

### A2. Upload from a college Windows computer

Insert the pen drive into the college computer where USB use is permitted. Check its drive letter again; it may differ from the letter on your laptop. In **PowerShell on that college computer**, upload directly from the pen drive:

```powershell
scp 'E:\SkinDiseaseAI-transfer\SkinDiseaseAI-all-models-training.zip' YOUR_USERNAME@YOUR_HOST:~/
ssh YOUR_USERNAME@YOUR_HOST
```

Follow the college's authentication instructions. The college computer must have SSH/SCP available and access to the assigned server; use its approved file-transfer application or portal if those commands are unavailable. After SSH connects, continue at **Step 4**, then setup/tests and GPU-job submission in Steps 5-8. The college computer's Windows drive `E:` is not a path on the remote supercomputer.

If the college computer runs **Linux**, use the pen drive's actual mounted path from its file manager, for example:

```bash
scp '/media/YOUR_USERNAME/YOUR_USB_LABEL/SkinDiseaseAI-transfer/SkinDiseaseAI-all-models-training.zip' YOUR_USERNAME@YOUR_HOST:~/
ssh YOUR_USERNAME@YOUR_HOST
```

The `/media/...` path is an example for the computer holding the pen drive; replace it with the real path. Continue at Step 4 after connecting. For a browser login, sign in through Route C and select the ZIP on the pen drive in the portal's upload dialog instead.

### A3. Bring results home on the pen drive

After the training job has stopped, run **Step 9 on the server** to collect logs and create `SkinDiseaseAI-training-results.tar.gz` plus its `.sha256` file. Then, in **PowerShell on the college Windows computer**, download both directly to the pen drive:

```powershell
scp YOUR_USERNAME@YOUR_HOST:~/SkinDiseaseAI-work/SkinDiseaseAI/SkinDiseaseAI-training-results.tar.gz 'E:\SkinDiseaseAI-transfer\'
scp YOUR_USERNAME@YOUR_HOST:~/SkinDiseaseAI-work/SkinDiseaseAI/SkinDiseaseAI-training-results.tar.gz.sha256 'E:\SkinDiseaseAI-transfer\'
Get-FileHash -LiteralPath 'E:\SkinDiseaseAI-transfer\SkinDiseaseAI-training-results.tar.gz' -Algorithm SHA256
Get-Content -LiteralPath 'E:\SkinDiseaseAI-transfer\SkinDiseaseAI-training-results.tar.gz.sha256'
```

Adjust the remote project path and pen-drive letter. Compare the hashes, eject the drive and take it home. If using a browser, use its file browser to download both generated files and save/copy them onto the pen drive.

Back on **your laptop**, from your local `SkinDiseaseAI/` repository:

```powershell
Copy-Item -LiteralPath 'E:\SkinDiseaseAI-transfer\SkinDiseaseAI-training-results.tar.gz' -Destination '.'
Copy-Item -LiteralPath 'E:\SkinDiseaseAI-transfer\SkinDiseaseAI-training-results.tar.gz.sha256' -Destination '.'
Get-FileHash -LiteralPath '.\SkinDiseaseAI-training-results.tar.gz' -Algorithm SHA256
Get-Content -LiteralPath '.\SkinDiseaseAI-training-results.tar.gz.sha256'
```

Verify the hashes again, then follow the **After training** section for local extraction and model verification. Keep the backup until the returned results are checked.

## 2. Route B: connect from your Windows laptop

If the college provides SSH access, open **PowerShell** on your laptop:

```powershell
ssh YOUR_USERNAME@YOUR_HOST
```

Follow the college's authentication steps. Password characters may not appear while typing. On the first connection, compare any displayed host fingerprint with the college's instructions before accepting it. If a nondefault port is provided, use `ssh -p YOUR_PORT YOUR_USERNAME@YOUR_HOST`.

After connection, you are using a Linux shell on the college server. Keep a second local PowerShell window for uploading files. Your laptop has OpenSSH `ssh` and `scp` available. [Microsoft SSH instructions](https://learn.microsoft.com/en-us/windows/terminal/tutorials/ssh).

## 3. Upload the training ZIP

In the **second PowerShell window on your laptop**, run:

```powershell
Set-Location -LiteralPath (Join-Path $env:USERPROFILE 'OneDrive\Desktop\Major Project\SkinDiseaseAI')
scp '.\artifacts\training-package\SkinDiseaseAI-all-models-training.zip' YOUR_USERNAME@YOUR_HOST:~/
```

This example uploads to your remote home directory. Use the administrator's approved transfer host/directory instead if required, particularly when home quota is small. For a nondefault SSH port, `scp` uses uppercase `-P YOUR_PORT`.

Wait until the transfer finishes. Do not upload `.venv`, `.venv-hpc`, chat history or the whole Desktop folder.

## 4. Unpack into persistent storage

The following **remote Linux commands** assume the college allows your home directory for this workload and the ZIP is in your remote home. If the college assigns a project filesystem, use that directory in place of `~/SkinDiseaseAI-work` and adjust subsequent paths.

```bash
sha256sum ~/SkinDiseaseAI-all-models-training.zip
```

For the delivered ZIP, expect:

```text
217ff22cdd7641b36ef91e7603de5faf466ac1e731f5358ec6b6fc68f714f5bc
```

Then:

```bash
mkdir -p ~/SkinDiseaseAI-work
cd ~/SkinDiseaseAI-work
python3 -m zipfile -e ~/SkinDiseaseAI-all-models-training.zip .
cd SkinDiseaseAI
python3 train.py --check-package
```

Success ends with `Package verified: 66 files`. This is a file-integrity check and needs no GPU. If the administrator first needs you to activate a Python module/environment, do that before these Python commands. Keep this project directory and all outputs on persistent storage, not an automatically deleted temporary directory.

## 5. Set up Python once

From the extracted remote `SkinDiseaseAI/` directory, on a node where the college permits installation:

```bash
python3 --version
bash setup_training.sh
```

Python 3.11 is recommended. The setup script supports Python 3.11-3.13, creates `.venv-hpc`, installs the selected CUDA PyTorch build and required Python packages, checks dependencies and verifies the package. It ends with `Setup finished` if successful. Setup may take time and needs approved package-network access or the college's package mirror/wheelhouse; the dataset and pretrained weight downloads are already included.

The default CUDA wheel index is 12.6. Ask the administrator to confirm driver compatibility before setup; alternate officially supported wheel indexes are described in `START_HERE.md`. Use the college's actual module/environment commands instead of guessing names.

If the college supplies an existing compatible environment, use the approved Python executable through `PYTHON_BIN=/absolute/path/to/python bash run_training.sh ...`. The administrator should confirm the dependencies in `requirements/training-linux.txt`. Keep the same package versions for resumed runs.

## 6. Submit a small first GPU job

Before submitting training, run the included software tests from the extracted project directory, on a node where the college permits CPU test work:

```bash
.venv-hpc/bin/python -m pytest -q tests
```

These 58 tests previously passed from an extracted copy locally. They check implementation behavior using synthetic fixtures and do not establish college GPU compatibility or trained-model performance. With a college-provided environment, replace `.venv-hpc/bin/python` with that environment's approved Python executable.

Logging in generally reaches a shared login node. Training must execute inside your allocated GPU job. Follow the college's scheduler instructions.

**If the college uses Slurm**, the ZIP includes `submit_slurm.sh`. Its defaults request one GPU, four CPU cores, 32 GiB host RAM and 24 hours; the college may require different limits, GPU type, account, partition or QOS settings. Obtain valid values first. A starting request of 16 GiB GPU memory or more still needs the real smoke check; actual E3/E4 memory use has not been measured on the college GPU.

From the extracted project directory, submit a one-epoch trial using your assigned GPU partition:

```bash
sbatch --partition=YOUR_GPU_PARTITION submit_slurm.sh --epochs-this-session 1
```

If an account is required, use:

```bash
sbatch --partition=YOUR_GPU_PARTITION --account=YOUR_PROJECT_ACCOUNT submit_slurm.sh --epochs-this-session 1
```

Use one of those submissions, not both. Add the administrator's actual resource/time overrides as needed. If the default partition is already appropriate, they may tell you to omit `--partition`.

The command prints `Submitted batch job` followed by your job ID. Submission means queued, not completed training. The trial verifies/extracts the data, checks the loaders, runs the real pretrained E1 GPU smoke, trains one E1 epoch and saves a paused checkpoint. It intentionally stops before E2 so you can inspect recovery and timing first.

These job commands follow [Slurm's official user guide](https://slurm.schedmd.com/quickstart.html). If the college uses PBS or another scheduler, ask for its GPU wrapper around `bash run_training.sh`; `sbatch` is only for Slurm.

## 7. Watch the job and verify its first checkpoint

Replace `YOUR_JOB_ID` with the returned numeric ID:

```bash
squeue -j YOUR_JOB_ID
tail -f skindiseaseai-YOUR_JOB_ID.log
```

`PD` means waiting in the queue; `R` means running. Press **Ctrl+C** to stop watching `tail`; that does not cancel the submitted job. If the job has left the queue, inspect the log and output files; absence from the queue alone does not prove success.

After the one-epoch job exits successfully:

```bash
cat artifacts/training/E1-seed42/gpu_smoke.json
cat artifacts/training/E1-seed42/status.json
ls -lh artifacts/training/E1-seed42/last.pt artifacts/training/E1-seed42/best.pt
```

Expected smoke fields are `passed: true`, `device: cuda`, and `checkpoint_reload_matches: true`. The status should be `paused` with `next_epoch: 1`, and both checkpoint files must exist in persistent storage. Save the log and these JSON files for review. A `No usable CUDA GPU` error means the process has not received a usable GPU environment; ask the administrator to check the allocation/software before retrying.

## 8. Continue the complete E1-E4 workflow

After verifying the first checkpoint, submit again from the same directory with the same account/partition settings, omitting the one-epoch limit:

```bash
sbatch --partition=YOUR_GPU_PARTITION --account=YOUR_PROJECT_ACCOUNT submit_slurm.sh
```

Omit `--account` if the college does not use it. The launcher detects `last.pt`, resumes E1, then runs E2, E3 and E4. GPU smoke checks run before fitting/resume. It selects the hybrid using validation results, evaluates the fixed checkpoints, writes the comparison and exports the selected hybrid.

If the job reaches a time limit, rerun the same submission after it stops. Completed epochs are preserved; the unfinished epoch can repeat. Do not reinstall/upgrade packages, edit source/config/splits, change output location or submit concurrent training jobs against the same directory during a run. Re-extracting the original ZIP or clearing outputs is not a resume procedure.

## 9. Know when training is complete and retrieve results

The log shows progress and `Saved epoch` messages. Individual models can finish with `completed` or `early_stopped`; early stopping is part of the protocol. The entire workflow is complete only when this file exists and reports `completed`:

```bash
cat artifacts/training/suite_status.json
```

### What to bring back from the supercomputer

**Bring back the complete `artifacts/training/` directory**, together with the scheduler job logs. The safest handoff is one results archive containing everything below, plus its SHA-256 checksum file. These files let us verify the experiment, resume training if necessary and integrate the selected hybrid into the project.

After a successful full run, use this checklist:

- [ ] **All four run folders:** `E1-seed42/`, `E2-seed42/`, `E3-seed42/` and `E4-seed42/`. Preserve `last.pt` for recovery, `best.pt` for the validation-selected checkpoint, `history.json`, `status.json`, `run.json`, `gpu_smoke.json`, class weights, class mapping and preprocessing records. Keep the remaining generated files in these folders too.
- [ ] **Each run's whole `evaluation/` directory:** `report.json`, `report.md`, `test_selection.json`, `confusion_matrix.png`, `roc_curves.png`, `training_curves.png`, `predictions.csv` and `error_analysis.json`. These provide measured results, plots, the fixed-test selection record and technical error analysis.
- [ ] **The whole `selected-hybrid/` directory:** `weights.pt`, `config.json`, `class_mapping.json`, `preprocessing.json`, `evaluation.json`, `model_card.json`, `verification_probe.pt` and `export_verification.json`. Keep these together; they are required for loading and checking the selected hybrid locally.
- [ ] **Suite selection/comparison/completion:** `validation_selection.json`, `comparison.json` and `suite_status.json` from the root of `artifacts/training/`.
- [ ] **Hardware, software and loader evidence:** `gpu_environment.json`, `package-freeze.txt` and the generated loader-verification report. These record what actually ran.
- [ ] **All job logs:** the existing `artifacts/training/logs/` directory, every `skindiseaseai-*.log` scheduler log for this run, and software-test output if you saved it. Include failed/interrupted job logs as well as successful ones.
- [ ] **Any intentional changes made at college:** return the exact changed training source/configuration files and environment setup instructions, if changes were needed. Keep them clearly identified alongside the original package.

The suite writes `export_verification.json` after checking the exported model in a fresh process. Actual accuracy and fusion improvement must come from the returned reports. If training is paused or interrupted, bring back all files generated so far and the error logs; final evaluation/export/completion files may not exist yet. Report that state honestly rather than treating it as a finished run.

You already have the original dataset, frozen splits and source ZIP locally. Returning the unchanged dataset, `.venv-hpc`, temporary image caches or the original training ZIP is unnecessary for this results handoff. Preserve the complete results archive locally and verify the transfer before clearing any college copy.

### Collect logs, compress the results, and download them

On the **remote server**, from the extracted `SkinDiseaseAI/` directory:

```bash
mkdir -p artifacts/training/logs
for job_log in skindiseaseai-*.log; do
    if [ -f "$job_log" ]; then
        cp "$job_log" artifacts/training/logs/
    fi
done
if [ -f software-tests.log ]; then
    cp software-tests.log artifacts/training/logs/
fi
if [ -f data/ham10000/processed/loader_verification.json ]; then
    cp data/ham10000/processed/loader_verification.json artifacts/training/loader-verification.json
fi
tar -czf SkinDiseaseAI-training-results.tar.gz artifacts/training
sha256sum SkinDiseaseAI-training-results.tar.gz > SkinDiseaseAI-training-results.tar.gz.sha256
```

Run these after the training job has stopped, so checkpoint files are not changing while you copy them. If the college uses different log names or locations, copy those job logs into `artifacts/training/logs/` before creating the archive. The optional copy commands above collect existing files; they do not generate a missing test or loader report.

In **local PowerShell**, from your local `SkinDiseaseAI/` repository:

```powershell
scp YOUR_USERNAME@YOUR_HOST:~/SkinDiseaseAI-work/SkinDiseaseAI/SkinDiseaseAI-training-results.tar.gz .
scp YOUR_USERNAME@YOUR_HOST:~/SkinDiseaseAI-work/SkinDiseaseAI/SkinDiseaseAI-training-results.tar.gz.sha256 .
Get-FileHash -LiteralPath '.\SkinDiseaseAI-training-results.tar.gz' -Algorithm SHA256
Get-Content -LiteralPath '.\SkinDiseaseAI-training-results.tar.gz.sha256'
```

Compare the two 64-character hashes; they must match, ignoring uppercase/lowercase. Adjust the remote paths if the college assigned another storage directory. You can copy the downloaded archive and checksum onto a pen drive if needed. The complete archive preserves training progress; the smaller JSON reports/logs can be reviewed first. Keep image-level outputs and checkpoints private. The later "After training" section explains local extraction, model verification and integration.

## Route C. Use a website login window or Jupyter portal

This route applies when the college gives you a URL and a username/password or another sign-in method, rather than an SSH command.

1. Open the college-provided URL in a browser on your laptop or an approved college computer. Complete its sign-in, MFA and VPN steps as instructed.
2. Open the portal's file browser and go to your assigned persistent project directory. Upload `SkinDiseaseAI-all-models-training.zip` from the laptop or pen drive. Portal labels and file-size limits vary; for a large-file upload limit, use the college's approved transfer route.
3. Open the portal's terminal in that same directory. If it offers only a notebook editor, ask how to open a terminal or submit a shell job; the supplied shell commands do not go into Python notebook cells.
4. In that **remote Linux terminal**, check your location and files:

```bash
pwd
ls -lh
```

If the terminal starts elsewhere, use `cd YOUR_PERSISTENT_PROJECT_DIRECTORY` first, with the actual uploaded ZIP directory. Then extract and verify:

```bash
python3 -m zipfile -e SkinDiseaseAI-all-models-training.zip .
cd SkinDiseaseAI
python3 train.py --check-package
```

Continue with **Step 5 for setup** and the test command in Step 6. Use the college's approved Python/environment activation instructions when needed.

Choose the portal's **GPU-backed** compute session before training. Once inside the allocated GPU terminal, run:

```bash
bash run_training.sh --epochs-this-session 1
```

Verify the first checkpoint, then rerun `bash run_training.sh` in the same project/environment to complete all four models. If the portal terminal is only a login-node terminal, submit through its scheduler instead. Session disconnect/timeout behavior depends on the college portal; ask whether submitted jobs or interactive sessions survive logout. The checkpoint files are the recovery mechanism.

After the job stops, use **Step 9** to collect logs and create the results archive/checksum. In the portal's file browser, download both `SkinDiseaseAI-training-results.tar.gz` and `SkinDiseaseAI-training-results.tar.gz.sha256`. Save them on your laptop, or onto the pen drive when using a college computer, then verify the checksum locally. There is no universal portal button sequence; its actual interface and GPU-allocation rules come from the college.

## Route D. Use a college Linux desktop or terminal login

If the supplied login opens a **Windows desktop**, open PowerShell there and use the Windows SSH/SCP route after transferring the ZIP to that desktop through the college's approved method. A pen drive connected to your laptop is available in a remote desktop only if the college enables drive redirection; otherwise use file upload/SCP from the computer that holds the ZIP.

If the college gives you a Linux login screen or opens a terminal for your account, sign in using the college's instructions and open **Terminal**. First confirm whether this is the supercomputer's login environment or a separate lab computer.

If it is a separate lab computer, use Route A's upload command from the mounted pen drive, or transfer from your laptop with Steps 2-3, then SSH to the assigned supercomputer. A ZIP on your laptop is not automatically visible in the Linux account.

If the college has made your pen drive or transferred ZIP available directly in the Linux environment, copy the ZIP into your **assigned persistent directory**. For example, after replacing both paths with actual college paths:

```bash
cp '/media/YOUR_USERNAME/YOUR_USB_LABEL/SkinDiseaseAI-transfer/SkinDiseaseAI-all-models-training.zip' '/YOUR/PERSISTENT/PROJECT/DIRECTORY/'
cd /YOUR/PERSISTENT/PROJECT/DIRECTORY
python3 -m zipfile -e SkinDiseaseAI-all-models-training.zip .
cd SkinDiseaseAI
python3 train.py --check-package
```

Run setup/tests from Steps 5-6 where permitted, then submit a GPU job using the college's scheduler instructions. Logging into Linux does not itself establish a GPU allocation. If the administrator confirms that this terminal is already inside an allocated GPU session, use `bash run_training.sh --epochs-this-session 1`, verify its checkpoint, and then `bash run_training.sh` to finish. Run on persistent storage rather than the pen drive.

For the return journey, create the archive and checksum in Step 9. If the pen drive is actually mounted in this Linux environment and USB writes are permitted, copy both generated files to its actual mount path:

```bash
cp SkinDiseaseAI-training-results.tar.gz '/media/YOUR_USERNAME/YOUR_USB_LABEL/SkinDiseaseAI-transfer/'
cp SkinDiseaseAI-training-results.tar.gz.sha256 '/media/YOUR_USERNAME/YOUR_USB_LABEL/SkinDiseaseAI-transfer/'
```

Otherwise download through SSH/SCP or the browser portal. Use the desktop's eject/unmount control before unplugging a mounted pen drive, and verify the returned archive on your laptop as described above.

## If a step fails

Stop at that step and keep its output. Share the exact command and error plus the college's non-secret setup/job instructions. Useful details are GPU model, Python/PyTorch versions, scheduler type, assigned partition and the last part of the job log. Do not change initialization to random weights or edit the frozen split files to bypass an error. Local package tests passed, but actual college GPU compatibility and training remain unverified until you run these steps.

## After training: outcomes and bringing the model into the project

A successful complete run gives you trained parameter files, measured evaluation reports and a selected hybrid export. The Python architecture code already exists in the project; the newly learned parameters are saved separately. Results depend on the actual run. No accuracy or fusion improvement is guaranteed.

| Output inside `artifacts/training/` | What you use it for |
| --- | --- |
| `E1-seed42/` through `E4-seed42/` | Preserve each experiment's best/last weights, optimizer/recovery state and history |
| Each run's `evaluation/report.json` and `report.md` | Test accuracy, macro-F1, balanced accuracy, per-class precision/sensitivity/specificity/F1 and applicable ROC-AUC, with limitations |
| Each run's `evaluation/` plots and error records | Inspect confusion matrices, ROC/training curves and technical disagreements with source labels |
| `validation_selection.json` | See the chosen hybrid (E3 or E4) and best comparison model, fixed using validation scores before test reporting |
| `comparison.json` | Compare the four fixed candidates and their recorded training times; do not change selection using these held-out scores |
| `selected-hybrid/` | The deployable research inference files: `weights.pt`, `config.json`, `class_mapping.json`, `preprocessing.json`, evaluation/model card and export verification |
| `suite_status.json` and environment/log files | Confirm the whole workflow finished and preserve software/hardware/recovery evidence |

Bring back the whole results directory as described in step 9, rather than returning only `weights.pt`. Keep the original results archive as a backup. The checkpoints permit future recovery and the metadata explains how to use the weights correctly.

On your laptop, place the downloaded `SkinDiseaseAI-training-results.tar.gz` in the local repository. In **PowerShell from `SkinDiseaseAI/`**, choose a new unused import-folder name and extract without replacing an existing experiment:

```powershell
New-Item -ItemType Directory -Path '.\artifacts\imported-runs\college-run-001'
tar -xzf '.\SkinDiseaseAI-training-results.tar.gz' -C '.\artifacts\imported-runs\college-run-001'
```

The results are then under `artifacts/imported-runs/college-run-001/artifacts/training/`, because the archive retains its `artifacts/training` prefix. After confirming the archive came from your own run, use the existing local Python environment to verify the exported hybrid on CPU:

```powershell
.\.venv\Scripts\python.exe train.py --verify-export --output '.\artifacts\imported-runs\college-run-001\artifacts\training'
```

This checks the exported files' hashes, reconstructs the architecture, loads the trained inference weights and compares a saved validation probe with the expected output. A mismatch needs investigation of source/software/transfer details. It is not an instruction to retrain, alter the test selection or overwrite the backup. Only run this command after the actual export is returned; the current local package contains no trained project model.

Next, review `suite_status.json`, the four GPU smoke/run/history/evaluation records, selection/comparison and the export/model card. Verify that the protocol stayed fixed and report limitations honestly. Preserve a stronger baseline comparison even if the required hybrid underperforms. Local inference latency also needs measurement; training on a GPU does not guarantee fast CPU prediction.

Once reviewed, copy the complete approved `selected-hybrid/` directory to the project's ignored `ai_model/exports/selected-hybrid/` location. The application loader must use `config.json` to construct E3/E4 through the existing model registry, load `weights.pt`, apply the exact saved preprocessing, use `class_mapping.json` for output order and put the model in evaluation mode. Inference uses the trained weights; no model training runs inside an upload request.

The planned next implementation is FastAPI: load the verified model once at startup, provide health/model-information/prediction endpoints, then connect the no-Node web dashboard. The intended flow is image upload, shared preprocessing, selected hybrid inference, class scores and results. Scores remain uncalibrated model scores. Grad-CAM is additional work requiring validation against the final logit; for fusion its CNN spatial map describes the CNN contribution conditional on the other branch, not a spatial explanation of the entire Transformer.

Backend and dashboard implementation remain future approved phases; copying weights alone does not create the application. Training completion also does not complete clinical validation or the explanation checks. Bring back the actual result files first so the project can proceed on verified evidence.
