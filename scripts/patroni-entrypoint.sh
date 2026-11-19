#!/usr/bin/env bash
set -euo pipefail

data_directory=/var/lib/postgresql/data
install -d -o postgres -g postgres -m 700 "$data_directory"
if [[ "$(stat -c '%U' "$data_directory")" != postgres ]]; then
  chown -R postgres:postgres "$data_directory"
fi
chmod 700 "$data_directory"
python3 /usr/local/bin/render-patroni-config.py /etc/patroni/patroni.yml /run/patroni.yml
chown postgres:postgres /run/patroni.yml
chmod 600 /run/patroni.yml
exec gosu postgres "$@"
