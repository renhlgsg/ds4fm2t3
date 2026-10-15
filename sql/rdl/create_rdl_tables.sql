-- RDL_DATA : raw tables, 1:1 with source CSV files.
-- No PRIMARY KEY constraints here on purpose: the raw layer must accept the file as delivered
-- (e.g. GEOLOCATION contains 261,831 fully duplicated rows). Keys are enforced from SDL_DATA onwards.
-- "Business key" comments document the unique key identified by profiling.
-- Placeholder {schema} is replaced by pipeline/provision_rdl.py

CREATE TABLE IF NOT EXISTS {schema}.GEOLOCATION (          -- business key: all 5 columns (after full-row dedup)
    geolocation_zip_code_prefix INTEGER,
    geolocation_lat             DOUBLE,
    geolocation_lng             DOUBLE,
    geolocation_city            VARCHAR,
    geolocation_state           VARCHAR
);

CREATE TABLE IF NOT EXISTS {schema}.CUSTOMERS (            -- business key: customer_id
    customer_id              VARCHAR,
    customer_unique_id       VARCHAR,
    customer_zip_code_prefix INTEGER,
    customer_city            VARCHAR,
    customer_state           VARCHAR
);

CREATE TABLE IF NOT EXISTS {schema}.SELLERS (              -- business key: seller_id
    seller_id              VARCHAR,
    seller_zip_code_prefix INTEGER,
    seller_city            VARCHAR,
    seller_state           VARCHAR
);

CREATE TABLE IF NOT EXISTS {schema}.PRODUCTS (             -- business key: product_id
    product_id                 VARCHAR,
    product_category_name      VARCHAR,
    product_name_lenght        INTEGER,    -- source spelling kept in raw layer
    product_description_lenght INTEGER,
    product_photos_qty         INTEGER,
    product_weight_g           INTEGER,
    product_length_cm          INTEGER,
    product_height_cm          INTEGER,
    product_width_cm           INTEGER
);

CREATE TABLE IF NOT EXISTS {schema}.PRODUCT_CATEGORY_TRANSLATION (   -- business key: product_category_name
    product_category_name         VARCHAR,
    product_category_name_english VARCHAR
);

CREATE TABLE IF NOT EXISTS {schema}.ORDERS (               -- business key: order_id
    order_id                      VARCHAR,
    customer_id                   VARCHAR,
    order_status                  VARCHAR,
    order_purchase_timestamp      TIMESTAMP,
    order_approved_at             TIMESTAMP,
    order_delivered_carrier_date  TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS {schema}.ORDER_PAYMENTS (       -- business key: (order_id, payment_sequential)
    order_id             VARCHAR,
    payment_sequential   INTEGER,
    payment_type         VARCHAR,
    payment_installments INTEGER,
    payment_value        DOUBLE
);

CREATE TABLE IF NOT EXISTS {schema}.ORDER_REVIEWS (        -- business key: (review_id, order_id); review_id alone repeats 814 times
    review_id               VARCHAR,
    order_id                VARCHAR,
    review_score            INTEGER,
    review_comment_title    VARCHAR,
    review_comment_message  VARCHAR,
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS {schema}.ORDER_ITEMS (          -- business key: (order_id, order_item_id)
    order_id            VARCHAR,
    order_item_id       INTEGER,
    product_id          VARCHAR,
    seller_id           VARCHAR,
    shipping_limit_date TIMESTAMP,
    price               DOUBLE,
    freight_value       DOUBLE
);
