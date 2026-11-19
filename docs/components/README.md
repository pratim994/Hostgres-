# Component notes

## PostgreSQL

PostgreSQL 16 stores transaction state in WAL and streams WAL to replicas. The Compose nodes use persistent named volumes, checksums, `wal_level=replica`, replication slots, and `wal_log_hints` to support Patroni-managed rewind. Streaming replication is not an independent backup. PostgreSQL 16 was retained from V1; newer majors would add upgrade and compatibility work without helping this lab's immediate goals.

## Patroni

Patroni controls PostgreSQL lifecycle, bootstrap, leader state, replica creation, and failover. The container entrypoint renders the read-only node YAML into `/run/patroni.yml` using password, synchronous-mode, and connection-limit environment values before dropping privileges. The REST API supplies role health to HAProxy and metrics to Prometheus. Alternatives include repmgr and operator-managed Kubernetes clusters; Patroni is selected because this lab explicitly studies DCS-backed leader management.

## etcd

Three etcd members form a 2-of-3 quorum. Patroni uses the client endpoints for the leader lock. Two simultaneous member failures remove quorum and must stop safe leader changes. etcd endpoints currently use unauthenticated plaintext inside a local Docker bridge; a remote deployment needs TLS, authentication, restricted peer/client ACLs, and independent failure domains.

## HAProxy

HAProxy accepts TCP client sessions and checks Patroni `/primary` over HTTP on port 8008. A healthy PostgreSQL TCP listener may be a replica, so raw TCP liveness is not enough for write routing. Stats and Prometheus metrics are exposed on the internal stats listener; the host stats page is loopback-only.

## PgBouncer

The pooler uses transaction pooling with 40 default backend connections and up to 500 clients. It connects through HAProxy, so new backend connections follow promotion. Transaction pooling trades away session affinity and can return transient errors during failover; application retry and idempotency remain application responsibilities. The upstream image supports configuration from environment variables and PostgreSQL 16 SCRAM mode; validate the pinned image at startup before relying on it operationally. [Upstream image configuration](https://github.com/edoburu/docker-pgbouncer)

## Prometheus and Grafana

Prometheus scrapes Patroni, per-node PostgreSQL exporters, etcd, HAProxy, and Node Exporter. Grafana provisions a Prometheus datasource and overview dashboard. The starter alert thresholds are fixed in `monitoring/alerts.yml` and must be tuned to workload/SLO requirements; Alertmanager delivery is not configured.

## Backup subsystem

No backup component is currently configured. pgBackRest is a candidate because repository-based full/differential backup and WAL archive management fit the desired workflow; a remote repository, secret handling, retention, and isolated tested restore must precede adoption.

## Experiment engine

The Python runner provides a Docker Compose execution adapter for one guarded primary-stop scenario. It records UTC event correlation timestamps and monotonic durations, stores one client ledger per run, compares acknowledged UUIDs with PostgreSQL, and writes JSON, CSV, and Markdown summaries. Additional failure adapters and measures are not implemented yet.
