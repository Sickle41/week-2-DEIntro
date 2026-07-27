-- One row per customer: customer_id, name, order_count, total_revenue.
-- Dedups raw_customers (keep highest record_version) before joining, so
-- duplicate customer rows don't fan out the order counts. $min_orders is a
-- bound parameter.
CREATE OR REPLACE TABLE customer_order_summary AS
WITH deduped_customers AS (
    SELECT * EXCLUDE (row_num)
    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY customer_id
                ORDER BY record_version DESC
            ) AS row_num
        FROM raw_customers
    )
    WHERE row_num = 1
),
order_agg AS (
    SELECT
        customer_id,
        count(*) AS order_count,
        sum(line_total) AS total_revenue
    FROM clean_orders
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT
    c.customer_id,
    c.name,
    o.order_count,
    o.total_revenue
FROM order_agg o
JOIN deduped_customers c ON c.customer_id = o.customer_id
WHERE o.order_count >= $min_orders
