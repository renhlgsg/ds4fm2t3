-- D_DATE: calendar covering whole years from the earliest to the latest date seen anywhere in SDL.
WITH all_dates AS (
    SELECT order_purchase_timestamp AS d FROM {sdl}.ORDERS
    UNION ALL SELECT order_approved_at FROM {sdl}.ORDERS
    UNION ALL SELECT order_delivered_carrier_date FROM {sdl}.ORDERS
    UNION ALL SELECT order_delivered_customer_date FROM {sdl}.ORDERS
    UNION ALL SELECT order_estimated_delivery_date FROM {sdl}.ORDERS
    UNION ALL SELECT shipping_limit_date FROM {sdl}.ORDER_ITEMS
    UNION ALL SELECT review_creation_date FROM {sdl}.ORDER_REVIEWS
    UNION ALL SELECT review_answer_timestamp FROM {sdl}.ORDER_REVIEWS
), bounds AS (
    SELECT CAST(date_trunc('year', min(d)) AS DATE) AS lo,
           CAST(date_trunc('year', max(d)) + INTERVAL 1 YEAR - INTERVAL 1 DAY AS DATE) AS hi
    FROM all_dates
)
SELECT CAST(strftime(g.d, '%Y%m%d') AS INTEGER)            AS date_key,
       CAST(g.d AS DATE)                                    AS full_date,
       CAST(day(g.d) AS SMALLINT)                           AS day_of_month,
       CAST(isodow(g.d) AS SMALLINT)                        AS day_of_week,
       dayname(g.d)                                         AS day_name,
       CAST(weekofyear(g.d) AS SMALLINT)                    AS week_of_year,
       CAST(month(g.d) AS SMALLINT)                         AS month_number,
       monthname(g.d)                                       AS month_name,
       strftime(g.d, '%Y-%m')                               AS year_month,
       CAST(quarter(g.d) AS SMALLINT)                       AS quarter,
       CAST(year(g.d) AS SMALLINT)                          AS year,
       isodow(g.d) >= 6                                     AS is_weekend
FROM bounds b, generate_series(CAST(b.lo AS TIMESTAMP), CAST(b.hi AS TIMESTAMP), INTERVAL 1 DAY) AS g(d)
