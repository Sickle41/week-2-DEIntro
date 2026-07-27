"""Tests for validate.py — basic data-quality checks run after the transforms.

Each check gets a minimal, purpose-built table so we're testing the check
itself, not re-deriving the sample fixture. run_checks() is also exercised
against the real transformed pipeline to confirm known-good data always
passes all of them.
"""

from __future__ import annotations

import duckdb
import pytest

from de_pipeline import transform
from de_pipeline.validate import (
    CHECKS,
    DataQualityError,
    check_no_duplicate_customer_ids,
    check_no_duplicate_order_ids,
    check_no_negative_line_totals,
    check_no_null_order_dates,
    check_revenue_reconciles,
    run_checks,
)


def test_run_checks_passes_on_a_clean_pipeline(loaded_con: duckdb.DuckDBPyConnection) -> None:
    transform.run_transforms(loaded_con)

    passed = run_checks(loaded_con)

    assert passed == [check.__name__ for check in CHECKS]


def test_check_no_duplicate_order_ids_catches_a_dupe(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("CREATE TABLE orders_deduped AS SELECT * FROM (VALUES (1), (1), (2)) t(order_id)")

    with pytest.raises(DataQualityError, match="order_id"):
        check_no_duplicate_order_ids(con)


def test_check_no_duplicate_customer_ids_catches_a_dupe(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        "CREATE TABLE customer_order_summary AS "
        "SELECT * FROM (VALUES (1), (1), (2)) t(customer_id)"
    )

    with pytest.raises(DataQualityError, match="customer_id"):
        check_no_duplicate_customer_ids(con)


def test_check_no_null_order_dates_catches_a_null(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        "CREATE TABLE clean_orders AS "
        "SELECT * FROM (VALUES (DATE '2024-01-01'), (NULL::DATE)) t(order_date)"
    )

    with pytest.raises(DataQualityError, match="order_date"):
        check_no_null_order_dates(con)


def test_check_no_negative_line_totals_catches_a_negative(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("CREATE TABLE clean_orders AS SELECT * FROM (VALUES (10.0), (-5.0)) t(line_total)")

    with pytest.raises(DataQualityError, match="line_total"):
        check_no_negative_line_totals(con)


def test_check_revenue_reconciles_catches_a_mismatch(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        "CREATE TABLE clean_orders AS "
        "SELECT * FROM (VALUES (1, 100.0)) t(customer_id, line_total)"
    )
    # Attributed revenue (50) doesn't match the 100 sitting in clean_orders for
    # a customer who IS in the summary — nothing here explains the gap.
    con.execute(
        "CREATE TABLE customer_order_summary AS "
        "SELECT * FROM (VALUES (1, 50.0)) t(customer_id, total_revenue)"
    )

    with pytest.raises(DataQualityError, match="reconcile"):
        check_revenue_reconciles(con)


def test_run_checks_collects_every_failure(loaded_con: duckdb.DuckDBPyConnection) -> None:
    transform.run_transforms(loaded_con)
    # Corrupt an otherwise-valid pipeline in two independent ways at once:
    # a duplicated order_id, and a line_total that's gone negative.
    loaded_con.execute("INSERT INTO orders_deduped SELECT * FROM orders_deduped LIMIT 1")
    loaded_con.execute("UPDATE clean_orders SET line_total = -1 WHERE order_id = 1")

    with pytest.raises(DataQualityError) as exc_info:
        run_checks(loaded_con)

    message = str(exc_info.value)
    assert "order_id" in message
    assert "line_total" in message
