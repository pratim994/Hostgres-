#!/usr/bin/env bash
set -euo pipefail

if [[ "${CONFIRM_DATA_DELETION:-}" != "postgres-ha-lab" ]]; then
  printf '%s\n' 'This removes PostgreSQL and etcd persistent data for this Compose project.'
  printf '%s\n' 'Set CONFIRM_DATA_DELETION=postgres-ha-lab to proceed.' >&2
  exit 2
fi

docker compose down --volumes
