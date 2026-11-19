from __future__ import annotations

import csv
import json
import logging
import statistics
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger("ha_experiment_reports")


def summarize(runs: list[dict[str, Any]]) -> dict[str, Any]:
    values = [run["end_to_end_rto_seconds"] for run in runs if isinstance(run.get("end_to_end_rto_seconds"), (int, float))]
    lost_counts = [run["lost_acknowledged_transactions"] for run in runs if isinstance(run.get("lost_acknowledged_transactions"), int)]
    failed_attempts = [run["failed_write_attempts"] for run in runs if isinstance(run.get("failed_write_attempts"), int)]
    return {
        "scenario": runs[0]["scenario"] if runs else None,
        "sample_count": len(runs),
        "failed_experiment_count": sum(run.get("status") != "passed" for run in runs),
        "rto_seconds": {
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "median": statistics.median(values) if values else None,
            "mean": statistics.mean(values) if values else None,
            "standard_deviation": statistics.stdev(values) if len(values) > 1 else (0.0 if values else None),
        },
        "lost_acknowledged_transactions": {
            "total": sum(lost_counts),
            "maximum_per_run": max(lost_counts) if lost_counts else None,
        },
        "failed_write_attempts": sum(failed_attempts),
        "runs": runs,
    }


def write_reports(runs: list[dict[str, Any]], results_directory: Path) -> None:
    summary = summarize(runs)
    results_directory.mkdir(parents=True, exist_ok=True)
    (results_directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    fields = ["run_id", "scenario", "status", "end_to_end_rto_seconds", "successful_transactions", "failed_write_attempts", "lost_acknowledged_transactions"]
    with (results_directory / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: run.get(field) for field in fields} for run in runs)
    stats = summary["rto_seconds"]
    report = [
        "# Experiment report", "", f"Scenario: {summary['scenario']}",
        f"Sample count: {summary['sample_count']}",
        f"Failed experiments: {summary['failed_experiment_count']}", "",
        f"Acknowledged transactions lost (total): {summary['lost_acknowledged_transactions']['total']}",
        f"Failed write attempts (total): {summary['failed_write_attempts']}", "",
        "## End-to-end RTO (seconds)", "", f"Minimum: {stats['min']}",
        f"Maximum: {stats['max']}", f"Median: {stats['median']}",
        f"Mean: {stats['mean']}", f"Standard deviation: {stats['standard_deviation']}", "",
        "Values are generated only from recorded runs. Patroni transitions are sampled; they are not exact internal event timestamps.", "",
    ]
    (results_directory / "report.md").write_text("\n".join(report), encoding="utf-8")


def main() -> None:
    results_directory = Path(__file__).resolve().parent / "results"
    measured_runs = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(results_directory.glob("run-*.json"))
        if path.name not in {"summary.json"}
    ]
    write_reports(measured_runs, results_directory)
    LOGGER.info("Wrote report from %d recorded run files", len(measured_runs))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()
