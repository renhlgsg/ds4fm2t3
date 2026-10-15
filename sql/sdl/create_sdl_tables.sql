-- SDL_DATA : cleaned tables. Same columns as RDL_DATA, plus PRIMARY KEY constraints.
-- Clean rules (see pipeline/clean_sdl.py): rows with missing PK deleted; numeric NULL -> 0;
-- string NULL/blank -> 'Unspecified'; duplicate rows removed. TIMESTAMP NULLs are kept (see docs).
-- Placeholder {schema} is replaced by pipeline/clean_sdl.py

CREATE TABLE IF NOT EXISTS {schema}.GEOLOCATION (
    geolocation_zip_code_prefix INTEGER NOT NULL,
    geolocation_lat             DOUBLE NOT NULL,
    geolocation_lng             DOUBLE NOT NULL,
    geolocation_city            VARCHAR NOT NULL,
    geolocation_state           VARCHAR NOT NULL,
    PRIMARY KEY (geolocation_zip_code_prefix, geolocation_lat, geolocation_lng, geolocation_city, geolocation_state)
);

CREATE TABLE IF NOT EXISTS {schema}.CUSTOMERS (
    customer_id              VARCHAR NOT NULL,
    customer_unique_id       VARCHAR,
    customer_zip_code_prefix INTEGER,
    customer_city            VARCHAR,
    customer_state           VARCHAR,
    PRIMARY KEY (customer_id)
);

CREATE TABLE IF NOT EXISTS {schema}.SELLERS (
    seller_id              VARCHAR NOT NULL,
    seller_zip_code_prefix INTEGER,
    seller_city            VARCHAR,
    seller_state           VARCHAR,
    PRIMARY KEY (seller_id)
);

CREATE TABLE IF NOT EXISTS {schema}.PRODUCTS (
    product_id                 VARCHAR NOT NULL,
    product_category_name      VARCHAR,
    product_name_lenght        INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty         INTEGER,
    product_weight_g           INTEGER,
    product_length_cm          INTEGER,
    product_height_cm          INTEGER,
    product_width_cm           INTEGER,
    PRIMARY KEY (product_id)
);

CREATE TABLE IF NOT EXISTS {schema}.PRODUCT_CATEGORY_TRANSLATION (
    product_category_name         VARCHAR NOT NULL,
    product_category_name_english VARCHAR,
    PRIMARY KEY (product_category_name)
);

CREATE TABLE IF NOT EXISTS {schema}.ORDERS (
    order_id                      VARCHAR NOT NULL,
    customer_id                   VARCHAR,
    order_status                  VARCHAR,
    order_purchase_timestamp      TIMESTAMP,
    order_approved_at             TIMESTAMP,
    order_delivered_carrier_date  TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    PRIMARY KEY (order_id)
);

CREATE TABLE IF NOT EXISTS {schema}.ORDER_PAYMENTS (
    order_id             VARCHAR NOT NULL,
    payment_sequential   INTEGER NOT NULL,
    payment_type         VARCHAR,
    payment_installments INTEGER,
    payment_value        DOUBLE,
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE TABLE IF NOT EXISTS {schema}.ORDER_REVIEWS (
    review_id               VARCHAR NOT NULL,
    order_id                VARCHAR NOT NULL,
    review_score            INTEGER,
    review_comment_title    VARCHAR,
    review_comment_message  VARCHAR,
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    PRIMARY KEY (review_id, order_id)
);

CREATE TABLE IF NOT EXISTS {schema}.ORDER_ITEMS (
    order_id            VARCHAR NOT NULL,
    order_item_id       INTEGER NOT NULL,
    product_id          VARCHAR,
    seller_id           VARCHAR,
    shipping_limit_date TIMESTAMP,
    price               DOUBLE,
    freight_value       DOUBLE,
    PRIMARY KEY (order_id, order_item_id)
);
