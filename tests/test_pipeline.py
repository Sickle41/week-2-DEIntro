"""Tests for pipeline.py's CLI argument parsing.

No S3/DuckDB I/O here — just checking that parse_args() wires flags to the
right stage defaults and that overrides come through as the right types.
"""

from __future__ import annotations

from pathlib import Path

from de_pipeline import export, fetch, load, pipeline


def test_parse_args_defaults_match_stage_defaults() -> None:
    args = pipeline.parse_args([])

    assert args.min_orders == 1
    assert args.raw_dir == fetch.RAW_DIR
    assert args.db_path == load.DB_PATH
    assert args.output_dir == export.OUTPUT_DIR


def test_parse_args_overrides() -> None:
    args = pipeline.parse_args(
        [
            "--min-orders",
            "2",
            "--raw-dir",
            "custom/raw",
            "--db-path",
            "custom/warehouse.duckdb",
            "--output-dir",
            "custom/output",
        ]
    )

    assert args.min_orders == 2
    assert args.raw_dir == Path("custom/raw")
    assert args.db_path == Path("custom/warehouse.duckdb")
    assert args.output_dir == Path("custom/output")
