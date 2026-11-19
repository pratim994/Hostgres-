#!/usr/bin/env bash
set -euo pipefail

read -rp 'This runs five primary-stop failover experiments and changes cluster roles. Type postgres-ha-lab to continue: ' confirmation
if [[ "$confirmation" != postgres-ha-lab ]]; then
  printf '%s\n' 'Benchmark cancelled.'
  exit 2
fi
export LAB_CONFIRMATION=postgres-ha-lab
python3 experiments/engine/run.py primary-container-stop --runs 5 --approve
