SELECT p.product_id,
       p.product_category_name AS category_name_pt,
       COALESCE(t.product_category_name_english,
                CASE WHEN p.product_category_name = 'Unspecified' THEN 'unspecified'
                     ELSE p.product_category_name END) AS category_name_en,   -- fallback: PT name when no translation exists
       p.product_name_lenght        AS name_length,
       p.product_description_lenght AS description_length,
       p.product_photos_qty         AS photos_qty,
       p.product_weight_g           AS weight_g,
       p.product_length_cm          AS length_cm,
       p.product_height_cm          AS height_cm,
       p.product_width_cm           AS width_cm,
       CASE WHEN p.product_length_cm > 0 AND p.product_height_cm > 0 AND p.product_width_cm > 0
            THEN CAST(p.product_length_cm AS BIGINT) * p.product_height_cm * p.product_width_cm END AS volume_cm3,
       CASE WHEN p.product_weight_g <= 0    THEN 'Unknown'
            WHEN p.product_weight_g < 500   THEN 'Light'
            WHEN p.product_weight_g < 2000  THEN 'Medium'
            WHEN p.product_weight_g < 10000 THEN 'Heavy'
            ELSE 'Very Heavy' END AS weight_class
FROM {sdl}.PRODUCTS p
LEFT JOIN {sdl}.PRODUCT_CATEGORY_TRANSLATION t ON t.product_category_name = p.product_category_name
