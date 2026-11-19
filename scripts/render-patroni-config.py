from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml


def render(source: Path, destination: Path) -> None:
    configuration = yaml.safe_load(source.read_text(encoding="utf-8"))
    synchronous_mode = os.environ.get("POSTGRES_SYNC_MODE", "false").strip().lower()
    if synchronous_mode not in {"true", "false"}:
        raise ValueError("POSTGRES_SYNC_MODE must be true or false")
    max_connections = int(os.environ.get("POSTGRES_MAX_CONNECTIONS", "200"))
    if max_connections < 20:
        raise ValueError("POSTGRES_MAX_CONNECTIONS must be at least 20")
    configuration["bootstrap"]["dcs"]["synchronous_mode"] = synchronous_mode == "true"
    configuration["bootstrap"]["dcs"]["postgresql"]["parameters"]["max_connections"] = max_connections
    configuration["postgresql"]["parameters"]["max_connections"] = max_connections
    configuration["postgresql"]["authentication"]["superuser"]["password"] = os.environ["POSTGRES_SUPERUSER_PASSWORD"]
    configuration["postgresql"]["authentication"]["replication"]["password"] = os.environ["REPLICATION_PASSWORD"]
    destination.write_text(yaml.safe_dump(configuration, sort_keys=False), encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: render-patroni-config.py SOURCE DESTINATION")
    render(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()
