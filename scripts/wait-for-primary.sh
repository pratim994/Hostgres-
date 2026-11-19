#!/usr/bin/env bash
set -euo pipefail
for i in $(seq 1 60); do
  for node in pg1 pg2 pg3; do
    if curl -fsS "http://localhost:$(
      case "$node" in pg1) echo 8008;; pg2) echo 8009;; pg3) echo 8010;; esac
    )/primary" >/dev/null; then
      echo "Primary is $node"
      exit 0
    fi
  done
  sleep 2
done
echo "No primary became available within 120 seconds" >&2
exit 1
