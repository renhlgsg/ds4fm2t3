SELECT r.review_id,
       r.order_id,
       COALESCE(dc.customer_key, -1) AS customer_key,
       COALESCE(CAST(strftime(r.review_creation_date,   '%Y%m%d') AS INTEGER), -1) AS review_creation_date_key,
       COALESCE(CAST(strftime(r.review_answer_timestamp,'%Y%m%d') AS INTEGER), -1) AS review_answer_date_key,
       CAST(r.review_score AS SMALLINT)                       AS review_score,
       r.review_comment_title   <> 'Unspecified'              AS has_comment_title,
       r.review_comment_message <> 'Unspecified'              AS has_comment_message,
       CAST(CASE WHEN r.review_comment_message = 'Unspecified' THEN 0
                 ELSE length(r.review_comment_message) END AS INTEGER) AS comment_message_length,
       CAST(round((epoch(r.review_answer_timestamp) - epoch(r.review_creation_date)) / 3600.0, 2) AS DECIMAL(10,2)) AS response_time_hours,
       r.review_score >= 4                                    AS is_positive,
       r.review_score <= 2                                    AS is_negative
FROM {sdl}.ORDER_REVIEWS r
LEFT JOIN {sdl}.ORDERS o    ON o.order_id = r.order_id
LEFT JOIN {sdl}.CUSTOMERS c ON c.customer_id = o.customer_id
LEFT JOIN {fdl}.D_CUSTOMER dc ON dc.customer_unique_id = c.customer_unique_id
