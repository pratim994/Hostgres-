# Endpoints

All host-published ports bind to `127.0.0.1`. The listed endpoints are based on Compose and the checked-in service configuration.

| Service | Protocol / port | Path | Purpose and access |
|---|---:|---|---|
| PgBouncer | PostgreSQL / 6432 | Database protocol | Normal application connection; app role password required; host loopback. |
| HAProxy | PostgreSQL / 5000 | Database protocol | Primary-only raw write route; PostgreSQL credentials required; host loopback. |
| HAProxy stats | HTTP / 8404 | `/`, `/metrics` | Statistics page and Prometheus metrics; no authentication configured; host loopback for published port, also internal. |
| Patroni pg1 | HTTP / 8008 | `/primary`, `/health`, `/metrics` | Role/health/metrics API; no authentication or TLS configured; host loopback. |
| Patroni pg2 | HTTP / 8009 | Same | Role/health/metrics API; host loopback. |
| Patroni pg3 | HTTP / 8010 | Same | Role/health/metrics API; host loopback. |
| PostgreSQL pg1 | PostgreSQL / 5433 | Database protocol | Direct diagnostic access; authenticated; host loopback. |
| PostgreSQL pg2 | PostgreSQL / 5434 | Database protocol | Direct diagnostic access; authenticated; host loopback. |
| PostgreSQL pg3 | PostgreSQL / 5435 | Database protocol | Direct diagnostic access; authenticated; host loopback. |
| Prometheus | HTTP / 9090 | `/` | Query and target UI; no authentication configured; host loopback. |
| Grafana | HTTP / 3000 | `/` | Dashboards; admin password from environment; host loopback. |
| etcd | HTTP / 2379, peer / 2380, metrics / 2381 | etcd v3 API / `/metrics` | Internal Compose network only; no authentication or TLS configured. |
| PostgreSQL exporters | HTTP / 9187 | `/metrics` | Internal only, one exporter per database node. |
| Node exporter | HTTP / 9100 | `/metrics` | Internal only; host filesystem and proc/sys are mounted read-only. |

PgBouncer admin console is not enabled in the current image configuration. No public endpoint is intended. Validate actual image behavior before relying on individual REST methods in automation.
