"""Export the final tables to files.

The pipeline's last mile: write the customer-facing outputs
(``customer_order_summary``, ``tag_revenue``) out of DuckDB into plain CSV files
under ``data/output/`` so a downstream consumer (a BI tool, another team, a data
lake) can pick them up without needing a DuckDB connection.

Docs:
  - DuckDB COPY:  https://duckdb.org/docs/stable/sql/statements/copy
"""

from __future__ import annotations

from pathlib import Path

import duckdb

# Where exported files land. (data/ is git-ignored.)
OUTPUT_DIR = Path("data/output")

# The tables export_all() writes out, in order. Both are built by
# transform.run_transforms() before export runs.
EXPORT_TABLES = ("customer_order_summary", "tag_revenue")


def export_table(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    dest_dir: Path = OUTPUT_DIR,
) -> Path:
    """Write ``table_name`` out to ``dest_dir/<table_name>.csv`` and return the
    path. Uses DuckDB's COPY so the export runs where the data already lives,
    instead of pulling the table into Python first."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{table_name}.csv"
    con.execute(f"COPY {table_name} TO '{dest_path.as_posix()}' (HEADER, DELIMITER ',')")
    return dest_path


def export_all(
    con: duckdb.DuckDBPyConnection, dest_dir: Path = OUTPUT_DIR
) -> dict[str, Path]:
    """Export every table in ``EXPORT_TABLES`` and return a mapping of table
    name -> path written."""
    return {name: export_table(con, name, dest_dir) for name in EXPORT_TABLES}
