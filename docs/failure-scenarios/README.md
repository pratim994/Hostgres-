# Failure scenarios

Only `primary-container-stop` is implemented in the experiment CLI. It requires `--approve` and `LAB_CONFIRMATION=postgres-ha-lab`; shell entry points prompt for the lab identity. It samples Patroni role endpoints every 100 ms, attempts committed UUID writes through PgBouncer and HAProxy, records server-acknowledged transaction IDs to a local fsynced ledger, restarts the failed node, and checks acknowledged UUID survival.

| Scenario | Status | Notes |
|---|---|---|
| Primary container stop | Implemented, not yet runtime-verified | Bounded wait and restart cleanup; one node failure only. |
| Primary process termination | Not implemented | No kill-signal scenario. |
| Replica termination | Not implemented | |
| One/two etcd member termination | Not implemented | Expected quorum behavior is 2/3 progress; 1/3 cannot elect a leader. |
| Network partition between database nodes | Not implemented | Requires controlled network shaping and cleanup. |
| Network partition between Patroni and etcd | Not implemented | Requires controlled network shaping and cleanup. |
| Replication lag injection | Not implemented | |
| Heavy write workload | Not implemented | |
| Connection saturation | Not implemented | |
| Disk pressure | Not implemented | |
| HAProxy termination | Not implemented | |
| PgBouncer termination | Not implemented | |
| Former-primary recovery | Partially configured | `pg_rewind` is enabled, but automated assertion is missing. |
| Recovery after temporary quorum loss | Not implemented | |
| PITR recovery | Not implemented | No backup subsystem exists yet. |

An absent scenario must not be interpreted as a successful test. Run only against the local lab. Network and disk experiments need additional containment and are not safe to simulate with the current shared-host profile.
