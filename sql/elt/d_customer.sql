-- D_CUSTOMER: one row per customer_unique_id. "Valid" orders exclude canceled/unavailable.
WITH co AS (
    SELECT c.customer_unique_id, c.customer_id, c.customer_zip_code_prefix AS zip,
           c.customer_city AS city, c.customer_state AS state,
           o.order_id, o.order_status, o.order_purchase_timestamp AS ts
    FROM {sdl}.CUSTOMERS c LEFT JOIN {sdl}.ORDERS o USING (customer_id)
), item_tot AS (
    SELECT order_id, count(*) AS n_items,
           sum(CAST(price AS DECIMAL(12,2)) + CAST(freight_value AS DECIMAL(12,2))) AS amt
    FROM {sdl}.ORDER_ITEMS GROUP BY order_id
), latest AS (
    SELECT customer_unique_id, zip, city, state FROM co
    QUALIFY row_number() OVER (PARTITION BY customer_unique_id ORDER BY ts DESC NULLS LAST, customer_id DESC) = 1
), agg AS (
    SELECT co.customer_unique_id,
           CAST(min(co.ts) FILTER (WHERE co.order_status NOT IN ('canceled','unavailable')) AS DATE) AS first_purchase_date,
           CAST(max(co.ts) FILTER (WHERE co.order_status NOT IN ('canceled','unavailable')) AS DATE) AS last_purchase_date,
           count(DISTINCT co.order_id) FILTER (WHERE co.order_status NOT IN ('canceled','unavailable')) AS total_orders,
           COALESCE(sum(it.n_items) FILTER (WHERE co.order_status NOT IN ('canceled','unavailable')), 0) AS total_items,
           COALESCE(sum(it.amt)     FILTER (WHERE co.order_status NOT IN ('canceled','unavailable')), 0) AS clv
    FROM co LEFT JOIN item_tot it ON it.order_id = co.order_id
    GROUP BY co.customer_unique_id
)
SELECT l.customer_unique_id,
       l.zip  AS zip_code_prefix,
       l.city, l.state,
       a.first_purchase_date, a.last_purchase_date,
       CAST(a.total_orders AS INTEGER) AS total_orders,
       CAST(a.total_items  AS INTEGER) AS total_items,
       CAST(a.clv AS DECIMAL(14,2))    AS customer_lifetime_value,
       CAST(CASE WHEN a.total_orders > 0 THEN a.clv / a.total_orders ELSE 0 END AS DECIMAL(14,2)) AS average_order_value,
       a.total_orders > 1              AS is_repeat_customer
FROM latest l JOIN agg a USING (customer_unique_id)
