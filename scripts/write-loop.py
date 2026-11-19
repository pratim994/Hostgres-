import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2 import Error


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ha_workload")
password = os.environ["APP_PASSWORD"]
dsn = os.getenv("DATABASE_URL", f"host=127.0.0.1 port=6432 dbname=postgres user=appuser password={password} connect_timeout=3")
ledger = Path(os.getenv("COMMIT_LEDGER", "experiments/results/workload-ledger.jsonl"))
interval = float(os.getenv("TRANSACTION_INTERVAL_SECONDS", "0.25"))

while True:
    database = None
    transaction_id = str(uuid.uuid4())
    try:
        database = psycopg2.connect(dsn)
        with database.cursor() as cursor:
            cursor.execute("INSERT INTO acknowledged_transactions(transaction_id) VALUES (%s)", (transaction_id,))
            cursor.execute("INSERT INTO heartbeat(client_id) VALUES (%s)", (os.getenv("CLIENT_ID", "writer-1"),))
        database.commit()
        record = {"transaction_id": transaction_id, "acknowledged_utc": datetime.now(timezone.utc).isoformat()}
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        logger.info("transaction committed", extra={"transaction_id": transaction_id})
        time.sleep(interval)
    except (Error, OSError, KeyError, ValueError):
        logger.exception("workload transaction failed", extra={"transaction_id": transaction_id})
        time.sleep(1)
    finally:
        if database is not None:
            database.close()
