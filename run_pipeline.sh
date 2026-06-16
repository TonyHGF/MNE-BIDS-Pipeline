#!/usr/bin/env bash
set -euo pipefail

mode="local"  # "local" or "server"; command-line argument overrides this.
stage="${1:-inspect}"  # inspect/qc, convert, pipeline, motor_report, all
if [[ "${2:-}" == "local" || "${2:-}" == "server" ]]; then
  mode="$2"
elif [[ "$stage" == "local" || "$stage" == "server" ]]; then
  mode="$stage"
  stage="inspect"
fi

env_name="eeg-preprocessing"
source_root="/public/home/hugf2022/motor/in-house/20260616_hgf"
bids_root="/public/home/hugf2022/motor/in-house/20260616_hgf_bids"
config_path="config/pipeline_config.py"
slurm_script="slurm/run_pipeline_cpu.slurm"

inspect_cmd="python scripts/inspect_source.py --source-root ${source_root}"
convert_cmd="python scripts/convert_to_bids.py --source-root ${source_root} --bids-root ${bids_root}"
pipeline_cmd="mne_bids_pipeline --config=${config_path}"
motor_report_cmd="python scripts/motor_report.py"

case "$stage" in
  inspect|qc)
    command="$inspect_cmd"
    ;;
  convert)
    command="$convert_cmd"
    ;;
  pipeline)
    command="$pipeline_cmd"
    ;;
  motor_report)
    command="$motor_report_cmd"
    ;;
  all)
    command="${inspect_cmd} && ${convert_cmd} && ${pipeline_cmd} && ${motor_report_cmd}"
    ;;
  *)
    echo "Unknown stage: $stage" >&2
    echo "Usage: bash run_pipeline.sh [inspect|qc|convert|pipeline|motor_report|all] [local|server]" >&2
    exit 2
    ;;
esac

if [[ "$mode" == "local" ]]; then
  source ~/anaconda3/bin/activate "$env_name"
  eval "$command"
elif [[ "$mode" == "server" ]]; then
  mkdir -p logs
  export PIPELINE_ENV_NAME="$env_name"
  export PIPELINE_COMMAND="$command"
  sbatch "$slurm_script"
else
  echo "Unknown mode: $mode" >&2
  echo "Usage: bash run_pipeline.sh [inspect|qc|convert|pipeline|motor_report|all] [local|server]" >&2
  exit 2
fi
