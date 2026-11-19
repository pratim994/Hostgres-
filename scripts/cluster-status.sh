#!/usr/bin/env bash
set -euo pipefail
docker compose exec pg1 patronictl -c /etc/patroni/patroni.yml list
