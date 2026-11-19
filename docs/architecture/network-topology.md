# Network topology

Compose creates a private `ha-net` bridge for all components. Client traffic is published only on loopback: PgBouncer `6432`, HAProxy PostgreSQL `5000`, HAProxy stats `8404`, Grafana `3000`, Prometheus `9090`, direct PostgreSQL `5433`-`5435`, and Patroni REST `8008`-`8010`. etcd client/peer and exporter endpoints are internal only.

HAProxy connects to PostgreSQL service ports and probes each Patroni REST API on port 8008 using `/primary`; a node is eligible for the write backend only when that role endpoint returns success. PostgreSQL direct ports bypass pooling/routing and are for local diagnostics only.

This profile uses plaintext HTTP and PostgreSQL connections on the isolated local bridge. TLS, service certificates, authenticated etcd, host firewall rules, and secret-manager integration are required for a multi-host deployment.
