SELECT i.order_id,
       CAST(i.order_item_id AS SMALLINT) AS order_item_id,
       COALESCE(CAST(strftime(o.order_purchase_timestamp, '%Y%m%d') AS INTEGER), -1) AS purchase_date_key,
       COALESCE(CAST(strftime(i.shipping_limit_date,      '%Y%m%d') AS INTEGER), -1) AS shipping_limit_date_key,
       COALESCE(dc.customer_key, -1)   AS customer_key,
       COALESCE(dp.product_key, -1)    AS product_key,
       COALESCE(ds.seller_key, -1)     AS seller_key,
       COALESCE(gc.geography_key, -1)  AS customer_geography_key,
       COALESCE(gs.geography_key, -1)  AS seller_geography_key,
       o.order_status,
       CAST(1 AS SMALLINT)             AS item_quantity,
       CAST(i.price AS DECIMAL(10,2))         AS price,
       CAST(i.freight_value AS DECIMAL(10,2)) AS freight_value,
       CAST(CAST(i.price AS DECIMAL(10,2)) + CAST(i.freight_value AS DECIMAL(10,2)) AS DECIMAL(10,2)) AS total_sale_amount,
       CAST(CASE WHEN i.price > 0 THEN round(i.freight_value / i.price, 4) END AS DECIMAL(8,4)) AS freight_ratio
FROM {sdl}.ORDER_ITEMS i
LEFT JOIN {sdl}.ORDERS    o  ON o.order_id = i.order_id
LEFT JOIN {sdl}.CUSTOMERS c  ON c.customer_id = o.customer_id
LEFT JOIN {fdl}.D_CUSTOMER  dc ON dc.customer_unique_id = c.customer_unique_id
LEFT JOIN {fdl}.D_PRODUCT   dp ON dp.product_id = i.product_id
LEFT JOIN {fdl}.D_SELLER    ds ON ds.seller_id  = i.seller_id
LEFT JOIN {sdl}.SELLERS     s  ON s.seller_id   = i.seller_id
LEFT JOIN {fdl}.D_GEOGRAPHY gc ON gc.zip_code_prefix = c.customer_zip_code_prefix
LEFT JOIN {fdl}.D_GEOGRAPHY gs ON gs.zip_code_prefix = s.seller_zip_code_prefix
