# Failure test plan

Run only against the disposable V1 environment. Capture timestamps, logs, Patroni role changes, HAProxy stats and client-side transaction IDs for each run.

| Test | Action | Expected observation |
|---|---|---|
| Primary process/container loss | `docker compose stop <leader>` | Eligible replica is promoted; HAProxy routes new connections to it |
| Replica loss | Stop a standby | Primary continues accepting writes; one standby unavailable |
| One etcd member loss | Stop one etcd container | Remaining 2/3 quorum continues |
| Two etcd member loss | Stop two etcd containers | No quorum; Patroni must not elect a new leader |
| Former primary restart | Start stopped node | It should rejoin as a replica after timeline reconciliation |
| Replication lag | Generate write load | Observe replay lag and candidate eligibility |

Never test two etcd failures while simultaneously relying on this lab for data you care about. A quorum loss prevents safe leader coordination.
