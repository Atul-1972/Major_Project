# Phase 2: acquisition, audit, frozen splits, and data loading

Run every command from `Desktop/Major Project/SkinDiseaseAI`. These commands prepare research data; they do not train a model or start a server.

## Complete the phase as a resumable local job

```powershell
.\.venv\Scripts\python.exe -u scripts\run_phase2.py
```

This performs acquisition/extraction, dependency checks, tests, and actual-data preparation in order. It stops on any failed stage and retains downloaded bytes. After successful real-cohort checks it generates the final phase report and `reports/phase2-data-summary.json`, updates the checkpoint and checklist, and stops before training. It uses a process lock to prevent duplicate jobs. At the saved pause checkpoint, no Phase 2 runner was left running. Before any later restart, inspect the status file to avoid starting duplicate jobs.

Review its status and recent log output:

```powershell
Get-Content .project\phase2_run.local.json
Get-Content reports\local\phase2-run.log -Tail 20
```

This process can continue without agent tokens while the computer and process stay running. It is not a Windows startup service. If it stops or the computer restarts, run the same command to resume. `status: complete` means the data phase passed and is waiting for Phase 3 approval; `needs_attention` means inspect the log and resolve the reported issue before continuing.

## 1. Install the tested Windows environment

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/phase2-windows.txt
.\.venv\Scripts\python.exe -m pip check
```

The actual local dependency freeze is `requirements/locks/phase2-windows-py311.txt`. Colab uses its own checked runtime; do not install the Windows CPU entry point into Colab.

## 2. Acquire original source files

Read `DATASET_SOURCE.md` for the official distribution, attribution, noncommercial terms, and metadata derivation.

```powershell
.\.venv\Scripts\python.exe -u -m ai_model.data.acquire --extract --workers 4
```

The image archive is 2,771,732,744 bytes in this distribution. Allow room for archives, extraction, and a working reserve. Four validated byte-range connections are used for the image archive. `--workers 1` uses a single connection. Interrupted downloads retain verified chunk files and a contiguous `.part` prefix for resumption. Rerun the same command; source entity-tag or checksum mismatches fail instead of silently mixing releases. Existing extracted images must match archive CRC/size before reuse.

Small-file-only inspection is available without downloading images:

```powershell
.\.venv\Scripts\python.exe -m ai_model.data.acquire --metadata-only
```

This alone does not satisfy Phase 2. It downloads labels/groups and derives `metadata.csv`; it does not certify that image files exist or pass audit.

## 3. Audit and freeze manifests

```powershell
.\.venv\Scripts\python.exe -u -m ai_model.data.pipeline prepare
```

The command stops on failed audit, invalid group coverage, changed existing manifests, or invalid loader output. It checks source metadata, actual image files, supported format/dimensions, original modes, class counts, duplicate pixels, label conflicts, and near-duplicate candidates. Near-duplicates are conservatively connected when 64-bit dHash distance is at most 2 and mean 8 × 8 RGB-thumbnail difference is at most 0.03 on a 0–1 scale. This heuristic can miss related images and can overgroup; it is not proof of exhaustive visual duplicate detection.

Lesion, available patient, exact-duplicate, and detected near-duplicate relations are joined into indivisible components. A deterministic class-aware greedy procedure with seed 42 seeks approximately 70/15/15 image ratios while reserving class coverage. Actual counts depend on group boundaries. Labels from the locked test partition never control model tuning.

The actual cohort initially stopped on eleven cross-label perceptual candidates. Their technical visual review is documented in `DUPLICATE_REVIEW.md`. Keep the private, hash-bound `data/ham10000/near_duplicate_review.json` with the dataset. The pipeline discovers it automatically; use `--duplicate-review <path>` for another location. Reviewed candidates remain grouped and retain source labels. Exact-pixel/source-lesion conflicts and unreviewed cross-label candidates still fail. The review is frozen and checksum-protected alongside the manifests.

## 4. Inspect outputs

```text
data/ham10000/
  raw/                          Unmodified originals and acquisition receipts
  images/                       Original JPEGs
  metadata.csv                  Canonical join of official labels/groups
  provenance.json               Exact source URLs, versions and file hashes
  processed/
    audit.json                  Actual checks, counts, errors and limitations
    audited_images.csv          File/pixel hashes, dimensions, labels and groups
    splits/
      train.csv, val.csv, test.csv
      class_mapping.json        Audited class order used by every experiment
      preprocessing.json        Exact shared transform configuration
      split_summary.json        Class/group counts and leakage-check results
      manifest_set.json         Fingerprint and checksums protecting the bundle
    loader_verification.json    Real CPU tensor-batch checks; no training results
```

All runtime data and per-image records remain ignored by Git. Reviewable aggregate findings go in `reports/` and the phase report. Saved splits are immutable: identical inputs reuse the verified bundle, changed inputs/config require a new `--output` directory. A failed or manually edited manifest bundle must be diagnosed, not overwritten in place.

For audit only, or to repeat the loader check without regenerating splits:

```powershell
.\.venv\Scripts\python.exe -m ai_model.data.pipeline audit
.\.venv\Scripts\python.exe -m ai_model.data.pipeline verify
```

For a manually acquired original HAM10000 CSV, supply `--metadata <path>`; images still belong under `<data-dir>/images`. Do not rename unrelated data to force it through the release checks. The production specification expects all documented HAM10000 images and classes.

## 5. Verify code behavior

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use explicitly synthetic fixtures solely to check behavior. They do not demonstrate accuracy, clinical utility, or real-data audit success. A successful actual-data run must separately record zero prohibited cross-split overlaps, all seven classes in each split, and a finite `[B, 3, 224, 224]` float32 image batch with int64 labels. Validation/test transformations must repeat exactly and may not use augmentation.

## Colab

Open `ai_model/notebooks/phase2_data_preparation.ipynb` in Colab after copying the repository source to a private Drive folder named `SkinDiseaseAI`. The notebook checks imports and transforms before acquisition, calls the same real modules, and saves reports/manifests to Drive. The temporary Colab image cache can disappear after runtime termination; reacquire it before reusing saved manifests. Training remains the next separately approved phase.

Also copy the private technical review described above to `SkinDiseaseAI/data/ham10000/near_duplicate_review.json` on Drive. It is not in Git. The notebook requires the file before cohort preparation and verifies its source binding through the audit.
