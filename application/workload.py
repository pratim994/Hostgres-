from __future__ import annotations

import argparse
import json
import logging
import os
import random
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extensions import make_dsn


LOGGER = logging.getLogger("ha_workload")


class LedgerPersistenceError(RuntimeError):
    pass


def database_dsn() -> str:
    configured = os.environ.get("DATABASE_URL")
    if configured:
        return configured
    password = os.environ.get("APP_PASSWORD")
    if not password:
        raise RuntimeError("APP_PASSWORD must be set in the environment")
    return make_dsn(host="127.0.0.1", port=6432, dbname="postgres", user="appuser", password=password, connect_timeout=3)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DurableLedger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

    def record(self, transaction_id: str, acknowledged_utc: str) -> None:
        with self.lock:
            created = not self.path.exists()
            try:
                with self.path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps({"transaction_id": transaction_id, "acknowledged_utc": acknowledged_utc}) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                if created:
                    descriptor = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(descriptor)
                    finally:
                        os.close(descriptor)
            except OSError as error:
                raise LedgerPersistenceError("Unable to persist acknowledged transaction ledger") from error


def run_worker(
    worker_id: int,
    deadline: float,
    interval: float,
    write_ratio: float,
    transaction_timeout: float,
    retry_delay: float,
    ledger: DurableLedger,
    counters: dict[str, int],
    counter_lock: threading.Lock,
) -> None:
    next_transaction = time.monotonic()
    while next_transaction < deadline:
        now = time.monotonic()
        if now < next_transaction:
            time.sleep(min(next_transaction - now, max(0.0, deadline - now)))
        next_transaction += interval
        transaction_id = str(uuid.uuid4())
        is_write = random.random() < write_ratio
        database = None
        try:
            database = psycopg2.connect(database_dsn(), connect_timeout=max(1, int(transaction_timeout)))
            database.autocommit = False
            with database.cursor() as cursor:
                cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(int(transaction_timeout * 1000)),))
                if is_write:
                    cursor.execute(
                        "INSERT INTO acknowledged_transactions(transaction_id) VALUES (%s)",
                        (transaction_id,),
                    )
                    cursor.execute("INSERT INTO heartbeat(client_id) VALUES (%s)", (f"workload-{worker_id}",))
                else:
                    cursor.execute("SELECT count(*) FROM acknowledged_transactions")
                    cursor.fetchone()
            database.commit()
            acknowledged_utc = utc_now()
            if is_write:
                ledger.record(transaction_id, acknowledged_utc)
            with counter_lock:
                counters["successful"] += 1
        except (psycopg2.Error, OSError):
            with counter_lock:
                counters["failed"] += 1
            LOGGER.exception("workload operation failed", extra={"worker_id": worker_id, "transaction_id": transaction_id})
            time.sleep(retry_delay)
        finally:
            if database is not None:
                database.close()
        with counter_lock:
            counters["attempted"] += 1


def run_workload(arguments: argparse.Namespace) -> dict[str, Any]:
    ledger = DurableLedger(Path(arguments.ledger))
    counters = {"attempted": 0, "successful": 0, "failed": 0}
    counter_lock = threading.Lock()
    started_monotonic = time.monotonic()
    started_utc = utc_now()
    deadline = started_monotonic + arguments.duration
    interval = arguments.clients / arguments.transactions_per_second
    with ThreadPoolExecutor(max_workers=arguments.clients) as executor:
        futures = [
            executor.submit(
                run_worker,
                worker_id,
                deadline,
                interval,
                arguments.write_ratio,
                arguments.transaction_timeout,
                arguments.retry_delay,
                ledger,
                counters,
                counter_lock,
            )
            for worker_id in range(arguments.clients)
        ]
        for future in as_completed(futures):
            future.result()
    elapsed = time.monotonic() - started_monotonic
    return {
        "started_utc": started_utc,
        "completed_utc": utc_now(),
        "duration_seconds": elapsed,
        "clients": arguments.clients,
        "target_transactions_per_second": arguments.transactions_per_second,
        "write_ratio": arguments.write_ratio,
        "attempted_transactions": counters["attempted"],
        "successful_transactions": counters["successful"],
        "failed_transactions": counters["failed"],
        "transactions_per_second": counters["successful"] / elapsed if elapsed else 0,
        "ledger_path": arguments.ledger,
        "delivery_note": "Each retry receives a new UUID. An ambiguous COMMIT can have committed without a local ledger record; application-level exactly-once delivery is not guaranteed.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clients", type=int, default=8)
    parser.add_argument("--transactions-per-second", type=float, default=20.0)
    parser.add_argument("--write-ratio", type=float, default=1.0)
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--transaction-timeout", type=float, default=5.0)
    parser.add_argument("--retry-delay", type=float, default=0.5)
    parser.add_argument("--ledger", default="experiments/results/workload-ledger.jsonl")
    parser.add_argument("--output", default="experiments/results/workload.json")
    arguments = parser.parse_args()
    if arguments.clients < 1 or arguments.clients > 500 or arguments.transactions_per_second <= 0:
        raise SystemExit("clients must be 1..500 and transactions-per-second must be positive")
    if not 0 <= arguments.write_ratio <= 1 or arguments.duration < 1 or arguments.transaction_timeout <= 0 or arguments.retry_delay < 0:
        raise SystemExit("write-ratio must be 0..1; duration and timeout positive; retry-delay nonnegative")
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
    measured = run_workload(arguments)
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(measured, indent=2) + "\n", encoding="utf-8")
    LOGGER.info("Workload complete", extra={"successful_transactions": measured["successful_transactions"], "failed_transactions": measured["failed_transactions"]})


if __name__ == "__main__":
    main()
