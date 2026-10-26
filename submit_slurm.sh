#!/usr/bin/env bash
#SBATCH --job-name=SkinDiseaseAI
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --output=skindiseaseai-%j.log
# Set the college account/partition/time limits with sbatch CLI options.
set -euo pipefail
cd -- "${SLURM_SUBMIT_DIR:?Submit using sbatch from the extracted SkinDiseaseAI directory}"
bash run_training.sh "$@"
