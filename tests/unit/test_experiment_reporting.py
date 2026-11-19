from experiments.reporting import summarize


def test_summary_uses_recorded_values_only() -> None:
    summary = summarize(
        [
            {"scenario": "primary_container_stop", "status": "passed", "end_to_end_rto_seconds": 0.2},
            {"scenario": "primary_container_stop", "status": "failed", "end_to_end_rto_seconds": 0.4},
            {"scenario": "primary_container_stop", "status": "passed", "end_to_end_rto_seconds": None},
        ]
    )

    assert summary["sample_count"] == 3
    assert summary["failed_experiment_count"] == 1
    assert summary["rto_seconds"]["min"] == 0.2
    assert summary["rto_seconds"]["max"] == 0.4
    assert abs(summary["rto_seconds"]["median"] - 0.3) < 1e-12
    assert abs(summary["rto_seconds"]["mean"] - 0.3) < 1e-12


def test_empty_summary_has_no_fabricated_measurements() -> None:
    summary = summarize([])

    assert summary["sample_count"] == 0
    assert summary["failed_experiment_count"] == 0
    assert summary["rto_seconds"] == {
        "min": None,
        "max": None,
        "median": None,
        "mean": None,
        "standard_deviation": None,
    }
