"""Day 3 — wire the stages into one end-to-end run.

This is the entry point for ``uv run de-pipeline``. By the end of the week it
should run the whole pipeline — fetch from S3 -> load into DuckDB -> run the
transforms -> export the results — printing a short summary so a human can see
what happened.
"""

from __future__ import annotations

import argparse
from pathlib import Path

# The stages you'll orchestrate. Each exposes the functions you wrote this week.
from de_pipeline import export, fetch, load, transform


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI args for ``de-pipeline``. ``argv=None`` reads from ``sys.argv``
    (the normal case); tests pass an explicit list instead."""
    parser = argparse.ArgumentParser(
        prog="de-pipeline",
        description="Fetch -> load -> transform -> export the orders/customers pipeline.",
    )
    parser.add_argument(
        "--min-orders",
        type=int,
        default=1,
        help="only keep customers with at least this many orders (default: 1)",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=fetch.RAW_DIR,
        help=f"where fetched source files land (default: {fetch.RAW_DIR})",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=load.DB_PATH,
        help=f"DuckDB database file (default: {load.DB_PATH})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=export.OUTPUT_DIR,
        help=f"where exported CSVs land (default: {export.OUTPUT_DIR})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Run the full pipeline end to end: fetch the source files, open a DuckDB
    connection, load the raw tables, run the transforms, export the results, and
    print a summary."""
    args = parse_args(argv)

    print("Fetching source files...")
    fetched = fetch.fetch_all(dest_dir=args.raw_dir)
    for name, path in fetched.items():
        print(f"  {name}: {path}")

    con = load.connect(db_path=args.db_path)
    try:
        print("Loading raw tables...")
        load_counts = load.load_all(con, raw_dir=args.raw_dir)
        for table, count in load_counts.items():
            print(f"  {table}: {count} rows")

        print("Running transforms...")
        transform_counts = transform.run_transforms(con, min_orders=args.min_orders)
        for table, count in transform_counts.items():
            print(f"  {table}: {count} rows")

        print("Exporting results...")
        exported = export.export_all(con, dest_dir=args.output_dir)
        for table, path in exported.items():
            print(f"  {table} -> {path}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
