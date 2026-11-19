# Architecture decisions

## ADR 001: Patroni with etcd

Use Patroni to manage PostgreSQL lifecycle and etcd as a three-member leader-lock DCS. A majority quorum provides deterministic coordination. Alternatives such as repmgr or a managed database service were not selected because this repository is intended to expose leader-election behavior. Single-host etcd members do not provide host fault tolerance.

## ADR 002: asynchronous default, synchronous opt-in

Async is the default to preserve commit availability when a standby is unavailable. Patroni synchronous mode is configurable via `POSTGRES_SYNC_MODE=true`; this can block or reject writes depending on strictness and commit settings. Synchronous replication narrows some loss windows but cannot guarantee zero RPO across all failures.

## ADR 003: HAProxy and PgBouncer

HAProxy checks Patroni's `/primary` role endpoint; a raw TCP check would accept replicas and cannot guarantee write safety. PgBouncer transaction pooling reduces backend connection pressure. Session-level features are incompatible with this pooling mode unless explicitly pinned or avoided.

## ADR 004: local Compose boundary

Compose gives reproducible process/container experiments, not independent failure domains. A multi-host reference profile is a documented follow-up, not an implemented deployment.

## ADR 005: transaction measurement

Duration uses a local monotonic clock; UTC timestamps are for correlation. A UUID is committed in PostgreSQL, then recorded in an fsynced client-side ledger after COMMIT acknowledgment. A narrow crash interval between acknowledgment and ledger fsync can undercount acknowledgments; therefore the measurement is conservative, not a mathematically exact external commit witness.

## ADR 006: backup tool pending

No backup product was selected or implemented. pgBackRest is a reasonable next choice for repository retention and verification, but wiring a production-like remote repository and tested isolated restore is required before claiming PITR.
