#!/usr/bin/env bash
#SBATCH --job-name=mne_bids_pipeline
#SBATCH --partition=bme_cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=12G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

cd "$SLURM_SUBMIT_DIR"
mkdir -p logs

env_name="${PIPELINE_ENV_NAME:-eeg-preprocessing}"
command="${PIPELINE_COMMAND:-mne_bids_pipeline --config=config/pipeline_config.py}"

echo "Job ID: ${SLURM_JOB_ID:-unknown}"
echo "Job name: ${SLURM_JOB_NAME:-unknown}"
echo "Node: ${SLURMD_NODENAME:-unknown}"
echo "Submit dir: $SLURM_SUBMIT_DIR"
echo "Environment: $env_name"
echo "Command: $command"
echo "Start: $(date)"

source ~/anaconda3/bin/activate "$env_name"

python - <<'PY'
import mne
import mne_bids
import mne_bids_pipeline

print("mne", mne.__version__)
print("mne_bids", mne_bids.__version__)
print("mne_bids_pipeline", getattr(mne_bids_pipeline, "__version__", "unknown"))
PY

eval "$command"

echo "HTML reports:"
find /public/home/hugf2022/motor/in-house/20260616_hgf_bids -type f -name '*.html' -print

echo "End: $(date)"
