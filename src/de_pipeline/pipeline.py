"""Day 3 — wire the stages into one end-to-end run.

This is the entry point for ``uv run de-pipeline``. By the end of the week it
should run the whole pipeline — fetch from S3 -> load into DuckDB -> run the
transforms — printing a short summary so a human can see what happened.
"""

from __future__ import annotations

# The stages you'll orchestrate. Each exposes the functions you wrote this week.
from de_pipeline import fetch, load, transform


def main() -> None:
    """Run the full pipeline end to end: fetch the source files, open a DuckDB
    connection, load the raw tables, run the transforms, and print a summary."""
    print("Fetching source files...")
    fetched = fetch.fetch_all()
    for name, path in fetched.items():
        print(f"  {name}: {path}")

    con = load.connect()
    try:
        print("Loading raw tables...")
        load_counts = load.load_all(con)
        for table, count in load_counts.items():
            print(f"  {table}: {count} rows")

        print("Running transforms...")
        transform_counts = transform.run_transforms(con)
        for table, count in transform_counts.items():
            print(f"  {table}: {count} rows")
    finally:
        con.close()


if __name__ == "__main__":
    main()
