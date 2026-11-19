# Operations runbook

## Local startup

1. Copy `.env.example` to `.env` and replace every placeholder with distinct random secrets.
2. Run `docker compose up -d --build`.
3. Wait for `./scripts/wait-for-primary.sh`, then inspect `./scripts/cluster-status.sh` and `docker compose ps`.
4. Run `./scripts/init-app.sh` once to create the least-privilege application role and schema.
5. Connect through PgBouncer using `127.0.0.1:6432`.

The existing `.env` file is ignored by Git and must be updated locally with the additional variables required by Compose. Do not run `down --volumes` to fix startup problems.

## Checks

```sh
./scripts/cluster-status.sh
docker compose exec pg1 patronictl -c /etc/patroni/patroni.yml list
PGPASSWORD="$POSTGRES_SUPERUSER_PASSWORD" psql -h 127.0.0.1 -p 5000 -U postgres -d postgres -f scripts/check-replication.sql
docker compose exec etcd1 etcdctl --endpoints=http://etcd1:2379,http://etcd2:2379,http://etcd3:2379 endpoint status --cluster -w table
curl -fsS http://127.0.0.1:8404/
curl -fsS http://127.0.0.1:9090/-/healthy
```

## Failover and recovery

`make failover` requests explicit confirmation and runs one primary-container-stop scenario. `make benchmark` requests confirmation and attempts five repetitions. The experiment runner stops and restarts the current leader, writes results under the ignored `experiments/results/` directory, and fails the run if assertions do not pass. Do not run these commands against data you depend on.

If recovery fails, inspect `docker compose logs --tail=200 pg1 pg2 pg3 etcd1 etcd2 etcd3 haproxy pgbouncer`. Confirm etcd has 2/3 members before attempting a Patroni switchover. Former-primary rejoin via rewind is configured but not validated in an automated integration test yet.

## Data lifecycle

`make down` stops containers and preserves named volumes. `make clean` does the same. `make clean-volumes` requires `CONFIRM_DATA_DELETION=postgres-ha-lab` and deletes all project volumes. No backup or PITR runbook is available because backup tooling is not implemented.

## Common startup failures

- Missing Compose variables: populate `.env` with all names in `.env.example`.
- Permission failures: inspect ownership in the affected named volume and Patroni entrypoint logs. Startup performs a one-time recursive ownership correction only when the data-directory root is not owned by `postgres`.
- No leader: check etcd member health and logs; do not reset volumes.
- Exporter authentication: ensure `make init-app` ran after schema creation and that the app role has `pg_monitor`.
- PgBouncer login errors: verify `APP_PASSWORD` matches the role password. Re-run `scripts/init-app.sh` to rotate it in place.
