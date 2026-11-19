# Application flow

```mermaid
sequenceDiagram
  participant App as Application
  participant Pool as PgBouncer
  participant Proxy as HAProxy
  participant Primary as PostgreSQL primary
  participant Standby as PostgreSQL standby
  participant DCS as etcd quorum
  App->>Pool: Connect as appuser
  Pool->>Proxy: Backend connection
  Proxy->>Primary: /primary role check selects writable node
  App->>Primary: Transaction with unique UUID
  Primary->>Primary: Commit WAL locally
  Primary-->>Standby: Stream WAL (async by default)
  Primary-->>App: COMMIT acknowledgment
  App->>App: fsync UUID to independent client ledger
  Primary--xDCS: Leader heartbeat stops on failure
  DCS-->>Standby: Patroni observes leader lock transition
  Standby->>Standby: Promote if eligible and quorum permits
  Proxy->>Standby: /primary now succeeds; route new connections
  App->>Pool: Retry via normal endpoint
  Pool-->>App: First recovered committed write defines end-to-end RTO
```

The independent ledger is written only after the server returns a successful `COMMIT`. A crash between server commit acknowledgment and local ledger fsync is an unavoidable measurement ambiguity in this simple client; results can undercount acknowledged commits in that narrow interval. Retrying a transaction after an ambiguous connection failure can duplicate application effects unless the application uses the UUID as a deduplication key. The lab ledger table uses a primary key to reject a repeated UUID. `application.workload` supports concurrent clients, target transaction rate, read/write ratio, duration, timeout, retry delay, and output paths. It assigns a fresh UUID to each attempt and does not promise exactly-once application delivery.

PgBouncer transaction pooling does not preserve session state across transactions. Keep application operations transaction-scoped and reconnect after failover. HAProxy shuts down sessions marked down so clients must reconnect.
