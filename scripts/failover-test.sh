#!/usr/bin/env bash
set -euo pipefail
read -rp 'This stops the current primary container. Type postgres-ha-lab to continue: ' confirmation
if [[ "$confirmation" != postgres-ha-lab ]]; then
  printf '%s\n' 'Experiment cancelled.'
  exit 2
fi
export LAB_CONFIRMATION=postgres-ha-lab
python3 experiments/engine/run.py primary-container-stop --runs 1 --approve
