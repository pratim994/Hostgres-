CREATE TABLE IF NOT EXISTS heartbeat (
    id BIGSERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS heartbeat_created_at_idx
    ON heartbeat (created_at);

CREATE TABLE IF NOT EXISTS failover_events (
    id BIGSERIAL PRIMARY KEY,
    event_name TEXT NOT NULL,
    details TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS acknowledged_transactions (
    transaction_id UUID PRIMARY KEY,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
