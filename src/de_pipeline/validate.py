"""Basic data-quality checks — run after the transforms, before you trust them.

Day 3 taught two specific ways this pipeline can go quietly wrong: a dedup that
lets a duplicate slip through, and a NULL join key that makes revenue vanish
instead of reconciling. Both were caught by hand, once, in a test. This module
turns those (and a couple of similarly cheap sanity checks) into standing
assertions any pipeline run can make against itself.

Each ``check_*`` function takes the DuckDB connection the transforms just ran
against and raises ``DataQualityError`` if something's wrong; it returns
nothing on success. ``run_checks()`` runs all of them and raises once with
every failure collected, rather than stopping at the first one.
"""

from __future__ import annotations

from collections.abc import Callable

import duckdb


class DataQualityError(Exception):
    """Raised when one or more data-quality checks fail."""


def check_no_duplicate_order_ids(con: duckdb.DuckDBPyConnection) -> None:
    """``orders_deduped`` must have exactly one row per ``order_id`` — that's
    the whole point of dedupe_orders()."""
    dupes = con.execute(
        "SELECT count(*) FROM "
        "(SELECT order_id FROM orders_deduped GROUP BY order_id HAVING count(*) > 1)"
    ).fetchone()[0]
    if dupes:
        raise DataQualityError(f"orders_deduped has {dupes} order_id(s) appearing more than once")


def check_no_duplicate_customer_ids(con: duckdb.DuckDBPyConnection) -> None:
    """``customer_order_summary`` must have exactly one row per ``customer_id``
    — a duplicate here means the customer dedup or join fanned out."""
    dupes = con.execute(
        "SELECT count(*) FROM ("
        "SELECT customer_id FROM customer_order_summary GROUP BY customer_id HAVING count(*) > 1"
        ")"
    ).fetchone()[0]
    if dupes:
        raise DataQualityError(
            f"customer_order_summary has {dupes} customer_id(s) appearing more than once"
        )


def check_no_null_order_dates(con: duckdb.DuckDBPyConnection) -> None:
    """``clean_orders.order_date`` must never be NULL — a NULL here means one of
    the three date formats silently failed to parse."""
    nulls = con.execute("SELECT count(*) FROM clean_orders WHERE order_date IS NULL").fetchone()[
        0
    ]
    if nulls:
        raise DataQualityError(f"clean_orders has {nulls} row(s) with a NULL order_date")


def check_no_negative_line_totals(con: duckdb.DuckDBPyConnection) -> None:
    """``clean_orders.line_total`` must never be negative — quantity and price
    are both meant to be non-negative, so a negative total means bad input got
    through the cast instead of being dropped."""
    negatives = con.execute("SELECT count(*) FROM clean_orders WHERE line_total < 0").fetchone()[
        0
    ]
    if negatives:
        raise DataQualityError(f"clean_orders has {negatives} row(s) with a negative line_total")


def check_revenue_reconciles(con: duckdb.DuckDBPyConnection) -> None:
    """Every dollar in ``clean_orders`` must be accounted for: either attributed
    to a customer in ``customer_order_summary``, or explainable — a NULL
    ``customer_id``, or a customer who didn't meet the ``min_orders`` threshold.
    This generalizes the Day-3 NULL-join-trap identity into a standing check
    that holds no matter what ``min_orders`` was passed."""
    total_clean, attributed, unaccounted = con.execute(
        """
        SELECT
            (SELECT COALESCE(sum(line_total), 0) FROM clean_orders),
            (SELECT COALESCE(sum(total_revenue), 0) FROM customer_order_summary),
            (
                SELECT COALESCE(sum(line_total), 0)
                FROM clean_orders
                WHERE customer_id IS NULL
                   OR customer_id NOT IN (SELECT customer_id FROM customer_order_summary)
            )
        """
    ).fetchone()
    if round(attributed + unaccounted, 2) != round(total_clean, 2):
        raise DataQualityError(
            "revenue does not reconcile: attributed "
            f"({attributed:.2f}) + unaccounted ({unaccounted:.2f}) != "
            f"clean_orders total ({total_clean:.2f})"
        )


# Every check run_checks() runs, in order.
CHECKS: tuple[Callable[[duckdb.DuckDBPyConnection], None], ...] = (
    check_no_duplicate_order_ids,
    check_no_duplicate_customer_ids,
    check_no_null_order_dates,
    check_no_negative_line_totals,
    check_revenue_reconciles,
)


def run_checks(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Run every check in ``CHECKS``. Returns the names of the checks that
    passed. If any check fails, raises ``DataQualityError`` once, with every
    failure's message collected — not just the first one."""
    passed: list[str] = []
    failures: list[str] = []
    for check in CHECKS:
        try:
            check(con)
        except DataQualityError as exc:
            failures.append(str(exc))
        else:
            passed.append(check.__name__)
    if failures:
        raise DataQualityError("; ".join(failures))
    return passed
