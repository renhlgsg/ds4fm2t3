-- Unknown (-1) members so facts never carry NULL foreign keys. Idempotent.
INSERT INTO {schema}.D_DATE (date_key, full_date, day_name, month_name, year_month, row_hash)
SELECT -1, NULL, 'Unknown', 'Unknown', 'Unknown', md5('unknown')
WHERE NOT EXISTS (SELECT 1 FROM {schema}.D_DATE WHERE date_key = -1);

INSERT INTO {schema}.D_GEOGRAPHY (geography_key, zip_code_prefix, city, state, region, has_coordinates, row_hash)
SELECT -1, -1, 'Unknown', 'NA', 'Unknown', FALSE, md5('unknown')
WHERE NOT EXISTS (SELECT 1 FROM {schema}.D_GEOGRAPHY WHERE geography_key = -1);

INSERT INTO {schema}.D_CUSTOMER (customer_key, customer_unique_id, city, state, row_hash)
SELECT -1, 'UNKNOWN', 'Unknown', 'NA', md5('unknown')
WHERE NOT EXISTS (SELECT 1 FROM {schema}.D_CUSTOMER WHERE customer_key = -1);

INSERT INTO {schema}.D_PRODUCT (product_key, product_id, category_name_pt, category_name_en, weight_class, row_hash)
SELECT -1, 'UNKNOWN', 'Unspecified', 'unspecified', 'Unknown', md5('unknown')
WHERE NOT EXISTS (SELECT 1 FROM {schema}.D_PRODUCT WHERE product_key = -1);

INSERT INTO {schema}.D_SELLER (seller_key, seller_id, city, state, row_hash)
SELECT -1, 'UNKNOWN', 'Unknown', 'NA', md5('unknown')
WHERE NOT EXISTS (SELECT 1 FROM {schema}.D_SELLER WHERE seller_key = -1);

INSERT INTO {schema}.D_PAYMENT_TYPE (payment_type_key, payment_type_code, payment_type_name, payment_method_group, row_hash)
SELECT -1, 'UNKNOWN', 'Unknown', 'Other', md5('unknown')
WHERE NOT EXISTS (SELECT 1 FROM {schema}.D_PAYMENT_TYPE WHERE payment_type_key = -1);
