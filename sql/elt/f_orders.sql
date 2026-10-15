WITH it AS (
    SELECT order_id, count(*) AS item_count, count(DISTINCT seller_id) AS seller_count,
           sum(CAST(price AS DECIMAL(12,2))) AS total_price,
           sum(CAST(freight_value AS DECIMAL(12,2))) AS total_freight
    FROM {sdl}.ORDER_ITEMS GROUP BY order_id
), pay AS (
    SELECT order_id, sum(CAST(payment_value AS DECIMAL(12,2))) AS total_payment_value
    FROM {sdl}.ORDER_PAYMENTS GROUP BY order_id
)
SELECT o.order_id,
       COALESCE(dc.customer_key, -1)  AS customer_key,
       COALESCE(g.geography_key, -1)  AS customer_geography_key,
       COALESCE(CAST(strftime(o.order_purchase_timestamp,      '%Y%m%d') AS INTEGER), -1) AS purchase_date_key,
       COALESCE(CAST(strftime(o.order_approved_at,             '%Y%m%d') AS INTEGER), -1) AS approved_date_key,
       COALESCE(CAST(strftime(o.order_delivered_carrier_date,  '%Y%m%d') AS INTEGER), -1) AS carrier_date_key,
       COALESCE(CAST(strftime(o.order_delivered_customer_date, '%Y%m%d') AS INTEGER), -1) AS delivered_date_key,
       COALESCE(CAST(strftime(o.order_estimated_delivery_date, '%Y%m%d') AS INTEGER), -1) AS estimated_delivery_date_key,
       o.order_status,
       o.order_purchase_timestamp       AS purchase_ts,
       o.order_approved_at              AS approved_ts,
       o.order_delivered_carrier_date   AS delivered_carrier_ts,
       o.order_delivered_customer_date  AS delivered_customer_ts,
       o.order_estimated_delivery_date  AS estimated_delivery_ts,
       CAST(COALESCE(it.item_count, 0) AS INTEGER)   AS item_count,
       CAST(COALESCE(it.seller_count, 0) AS INTEGER) AS seller_count,
       CAST(COALESCE(it.total_price, 0) AS DECIMAL(12,2))   AS total_price,
       CAST(COALESCE(it.total_freight, 0) AS DECIMAL(12,2)) AS total_freight,
       CAST(COALESCE(it.total_price, 0) + COALESCE(it.total_freight, 0) AS DECIMAL(12,2)) AS total_order_amount,
       CAST(COALESCE(pay.total_payment_value, 0) AS DECIMAL(12,2)) AS total_payment_value,
       CAST(round((epoch(o.order_approved_at) - epoch(o.order_purchase_timestamp)) / 3600.0, 2) AS DECIMAL(10,2)) AS approval_hours,
       CAST(round((epoch(o.order_delivered_carrier_date) - epoch(o.order_approved_at)) / 86400.0, 2) AS DECIMAL(10,2)) AS carrier_handover_days,
       CAST(round((epoch(o.order_delivered_customer_date) - epoch(o.order_purchase_timestamp)) / 86400.0, 2) AS DECIMAL(10,2)) AS delivery_days,
       CAST(round((epoch(o.order_estimated_delivery_date) - epoch(o.order_purchase_timestamp)) / 86400.0, 2) AS DECIMAL(10,2)) AS estimated_delivery_days,
       CAST(date_diff('day', CAST(o.order_estimated_delivery_date AS DATE), CAST(o.order_delivered_customer_date AS DATE)) AS DECIMAL(10,2)) AS delivery_delay_days,
       o.order_delivered_customer_date IS NOT NULL AS is_delivered,
       CASE WHEN o.order_delivered_customer_date IS NULL THEN NULL
            ELSE CAST(o.order_delivered_customer_date AS DATE) > CAST(o.order_estimated_delivery_date AS DATE) END AS is_late
FROM {sdl}.ORDERS o
LEFT JOIN {sdl}.CUSTOMERS c ON c.customer_id = o.customer_id
LEFT JOIN {fdl}.D_CUSTOMER dc ON dc.customer_unique_id = c.customer_unique_id
LEFT JOIN {fdl}.D_GEOGRAPHY g ON g.zip_code_prefix = c.customer_zip_code_prefix
LEFT JOIN it  ON it.order_id  = o.order_id
LEFT JOIN pay ON pay.order_id = o.order_id
