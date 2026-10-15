SELECT p.order_id,
       CAST(p.payment_sequential AS SMALLINT) AS payment_sequential,
       COALESCE(CAST(strftime(o.order_purchase_timestamp, '%Y%m%d') AS INTEGER), -1) AS purchase_date_key,
       COALESCE(dc.customer_key, -1)      AS customer_key,
       COALESCE(pt.payment_type_key, -1)  AS payment_type_key,
       CAST(p.payment_installments AS SMALLINT) AS payment_installments,
       CAST(p.payment_value AS DECIMAL(12,2))   AS payment_value,
       CAST(CAST(p.payment_value AS DECIMAL(12,2)) / GREATEST(p.payment_installments, 1) AS DECIMAL(12,2)) AS installment_value
FROM {sdl}.ORDER_PAYMENTS p
LEFT JOIN {sdl}.ORDERS o     ON o.order_id = p.order_id
LEFT JOIN {sdl}.CUSTOMERS c  ON c.customer_id = o.customer_id
LEFT JOIN {fdl}.D_CUSTOMER dc     ON dc.customer_unique_id = c.customer_unique_id
LEFT JOIN {fdl}.D_PAYMENT_TYPE pt ON pt.payment_type_code = p.payment_type
