from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extensions import connection, make_dsn
from experiments.reporting import write_reports


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "results"
LOGGER = logging.getLogger("ha_experiments")
NODES = {"pg1": 8008, "pg2": 8009, "pg3": 8010}


class LedgerPersistenceError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dsn() -> str:
    password = os.environ.get("APP_PASSWORD")
    if not password:
        raise RuntimeError("APP_PASSWORD must be set in the environment")
    configured_dsn = os.environ.get("DATABASE_URL")
    if configured_dsn:
        return configured_dsn
    return make_dsn(
        host="127.0.0.1",
        port=6432,
        dbname="postgres",
        user="appuser",
        password=password,
        connect_timeout=2,
    )


def primary_node() -> str | None:
    for node, port in NODES.items():
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/primary", timeout=0.4) as response:
                if response.status == 200:
                    return node
        except (urllib.error.URLError, TimeoutError):
            continue
    return None


def persist_commit(db: connection, ledger: Path) -> tuple[str, float, str]:
    transaction_id = str(uuid.uuid4())
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO acknowledged_transactions(transaction_id) VALUES (%s)",
            (transaction_id,),
        )
    db.commit()
    acknowledged_at = time.monotonic()
    acknowledged_utc = utc_now()
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger_created = not ledger.exists()
    try:
        with ledger.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"transaction_id": transaction_id, "acknowledged_utc": acknowledged_utc}) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        if ledger_created:
            directory_descriptor = os.open(ledger.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
    except OSError as error:
        raise LedgerPersistenceError("Unable to persist acknowledged transaction to the independent ledger") from error
    return transaction_id, acknowledged_at, acknowledged_utc


def missing_acknowledgements(ledger: Path, db: connection) -> int:
    acknowledged = set()
    if ledger.exists():
        with ledger.open(encoding="utf-8") as stream:
            for line in stream:
                record = json.loads(line)
                acknowledged.add(record["transaction_id"])
    if not acknowledged:
        return 0
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT transaction_id::text FROM acknowledged_transactions WHERE transaction_id = ANY(%s::uuid[])",
            (list(acknowledged),),
        )
        present = {row[0] for row in cursor.fetchall()}
    return len(acknowledged - present)


def docker(*arguments: str, timeout: int = 30) -> str:
    result = subprocess.run(
        ["docker", "compose", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout.strip()


def wait_for_write(timeout_seconds: float, ledger: Path) -> tuple[str | None, float | None, str | None, int]:
    deadline = time.monotonic() + timeout_seconds
    failures = 0
    while time.monotonic() < deadline:
        db = None
        try:
            db = psycopg2.connect(dsn())
            transaction_id, acknowledged_monotonic, acknowledged_utc = persist_commit(db, ledger)
            return transaction_id, acknowledged_monotonic, acknowledged_utc, failures
        except (psycopg2.Error, OSError):
            failures += 1
            time.sleep(0.1)
        finally:
            if db is not None:
                db.close()
    return None, None, None, failures


def run_primary_stop(run_number: int, approve: bool, timeout_seconds: int) -> dict[str, Any]:
    if not approve or os.environ.get("LAB_CONFIRMATION") != "postgres-ha-lab":
        raise RuntimeError("Destructive scenario requires --approve and LAB_CONFIRMATION=postgres-ha-lab")
    services = [json.loads(line) for line in docker("ps", "--format", "json").splitlines() if line.strip()]
    required_services = set(NODES) | {"etcd1", "etcd2", "etcd3", "haproxy", "pgbouncer"}
    if (
        not services
        or any(service.get("Project") != "postgres-ha-lab" for service in services)
        or not required_services.issubset({service.get("Service") for service in services})
    ):
        raise RuntimeError("Compose project identity did not match the expected PostgreSQL HA lab")
    leader = primary_node()
    if leader is None:
        raise RuntimeError("No primary is currently reported by Patroni")
    ledger_token = uuid.uuid4().hex
    ledger = RESULTS / "ledgers" / f"run-{run_number:03d}-{ledger_token}.jsonl"
    db = psycopg2.connect(dsn())
    try:
        initial_id, _, _ = persist_commit(db, ledger)
    finally:
        db.close()
    failure_monotonic = time.monotonic()
    failure_utc = utc_now()
    detection_monotonic = None
    role_change_utc = None
    first_write_monotonic = None
    first_write_utc = None
    failed_transactions = 0
    recovered = False
    try:
        docker("stop", "--timeout", "5", leader)
        detect_deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < detect_deadline:
            if primary_node() not in (None, leader):
                detection_monotonic = time.monotonic()
                role_change_utc = utc_now()
                break
            time.sleep(0.1)
        transaction_id, first_write_monotonic, first_write_utc, failed_transactions = wait_for_write(timeout_seconds, ledger)
        recovered = transaction_id is not None
        if not recovered:
            raise RuntimeError("HAProxy/PgBouncer write endpoint did not recover before timeout")
    finally:
        docker("start", leader)
    recovery_deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < recovery_deadline and primary_node() is None:
        time.sleep(0.1)
    db = psycopg2.connect(dsn())
    try:
        lost = missing_acknowledgements(ledger, db)
    finally:
        db.close()
    result: dict[str, Any] = {
        "run_id": f"run-{run_number:03d}",
        "scenario": "primary_container_stop",
        "status": "passed" if recovered and lost == 0 and detection_monotonic is not None else "failed",
        "started_utc": failure_utc,
        "completed_utc": utc_now(),
        "failed_node": leader,
        "first_pre_failure_transaction_id": initial_id,
        "failure_to_new_primary_observed_seconds": detection_monotonic - failure_monotonic if detection_monotonic else None,
        "new_primary_observed_utc": role_change_utc,
        "end_to_end_rto_seconds": first_write_monotonic - failure_monotonic if first_write_monotonic else None,
        "first_successful_write_utc": first_write_utc,
        "successful_transactions": 2 if recovered else 1,
        "failed_write_attempts": failed_transactions,
        "lost_acknowledged_transactions": lost,
        "ledger_path": str(ledger.relative_to(ROOT)),
        "measurement_note": "The role change is sampled at 100 ms and is not an exact Patroni detection or promotion event. Recovery is the first committed transaction through PgBouncer and HAProxy.",
    }
    output = RESULTS / f"run-{run_number:03d}.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", choices=["primary-container-stop"])
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--approve", action="store_true")
    arguments = parser.parse_args()
    if arguments.runs < 1 or arguments.runs > 20 or arguments.timeout < 10:
        raise SystemExit("runs must be 1..20 and timeout must be at least 10 seconds")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    RESULTS.mkdir(parents=True, exist_ok=True)
    measured: list[dict[str, Any]] = []
    for number in range(1, arguments.runs + 1):
        started_utc = utc_now()
        try:
            measured.append(run_primary_stop(number, arguments.approve, arguments.timeout))
        except (RuntimeError, OSError, ValueError, subprocess.SubprocessError, psycopg2.Error) as error:
            LOGGER.exception("Experiment run %s failed", number)
            measured.append({"run_id": f"run-{number:03d}", "scenario": arguments.scenario.replace("-", "_"), "status": "failed", "started_utc": started_utc, "completed_utc": utc_now(), "error_type": type(error).__name__, "error": str(error)})
            (RESULTS / f"run-{number:03d}.json").write_text(json.dumps(measured[-1], indent=2) + "\n", encoding="utf-8")
    write_reports(measured, RESULTS)
    if any(run.get("status") != "passed" for run in measured):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
