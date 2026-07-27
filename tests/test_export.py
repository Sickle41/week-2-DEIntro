"""Tests for export.py — writing the final tables out to CSV files.

Uses the ``loaded_con`` fixture (see conftest.py) plus ``transform.run_transforms``
to build all four tables, then checks export.py writes them out correctly.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from de_pipeline import export, transform


def test_export_all_writes_a_csv_per_table(
    loaded_con: duckdb.DuckDBPyConnection, tmp_path: Path
) -> None:
    transform.run_transforms(loaded_con)

    paths = export.export_all(loaded_con, dest_dir=tmp_path)

    assert set(paths) == {"customer_order_summary", "tag_revenue"}
    for table_name, path in paths.items():
        assert path == tmp_path / f"{table_name}.csv"
        assert path.exists()


def test_exported_csv_round_trips_the_row_count(
    loaded_con: duckdb.DuckDBPyConnection, tmp_path: Path
) -> None:
    transform.run_transforms(loaded_con)

    paths = export.export_all(loaded_con, dest_dir=tmp_path)

    for table_name, path in paths.items():
        table_rows = loaded_con.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
        csv_rows = loaded_con.execute(
            "SELECT count(*) FROM read_csv_auto(?)", [str(path)]
        ).fetchone()[0]
        assert csv_rows == table_rows


def test_export_table_creates_missing_dest_dir(
    loaded_con: duckdb.DuckDBPyConnection, tmp_path: Path
) -> None:
    transform.run_transforms(loaded_con)
    nested = tmp_path / "nested" / "output"

    path = export.export_table(loaded_con, "tag_revenue", dest_dir=nested)

    assert path == nested / "tag_revenue.csv"
    assert path.exists()
