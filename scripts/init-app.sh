
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
set -a
source .env
set +a

export PGPASSWORD="$POSTGRES_SUPERUSER_PASSWORD"

psql -h 127.0.0.1 -p 5000 \
  -U postgres -d postgres \
  -v ON_ERROR_STOP=1 \
  -f sql/create-app-user.sql

psql -h 127.0.0.1 -p 5000 \
  -U postgres -d postgres \
  -v ON_ERROR_STOP=1 \
  -f sql/schema.sql

export PGPASSWORD="$APP_PASSWORD"
psql -h 127.0.0.1 -p 6432 -U appuser -d postgres -v ON_ERROR_STOP=1 \
  -c 'SELECT count(*) AS initialized_tables FROM information_schema.tables WHERE table_schema = '\''public'\'';'
echo "Application database initialized through PgBouncer."
