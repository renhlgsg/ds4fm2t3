-- FDL_DATA : star schema. Placeholder {schema} = FDL_DATA.
-- Conventions: D_ = dimension, F_ = fact. Surrogate keys (*_key) via sequences; key -1 = 'Unknown' member.
-- PRIMARY KEYs are enforced. FOREIGN KEYs are intentionally NOT declared physically (DuckDB restricts
-- UPDATE/DELETE on FK-referenced tables, which would break incremental loads); referential integrity
-- is verified by pipeline/dq_tests.py instead (common DW practice).
-- row_hash = md5 of all business columns -> change detection for incremental loads.

-- ============================ ETL CONTROL ============================
CREATE TABLE IF NOT EXISTS {schema}.ETL_RUN_LOG (
    run_id         VARCHAR      NOT NULL,
    target_table   VARCHAR(40)  NOT NULL,
    run_type       VARCHAR(12)  NOT NULL,      -- INITIAL | INCREMENTAL
    rows_inserted  BIGINT       NOT NULL,
    rows_updated   BIGINT       NOT NULL,
    rows_total     BIGINT       NOT NULL,
    started_at     TIMESTAMP    NOT NULL,
    finished_at    TIMESTAMP    NOT NULL,
    PRIMARY KEY (run_id, target_table)
);

CREATE TABLE IF NOT EXISTS {schema}.DQ_RESULT_LOG (
    run_id       VARCHAR      NOT NULL,
    check_id     VARCHAR(10)  NOT NULL,
    category     VARCHAR(20)  NOT NULL,        -- GRAIN | NULL | DUPLICATE | REFERENTIAL | BUSINESS
    severity     VARCHAR(5)   NOT NULL,        -- ERROR | WARN
    description  VARCHAR(250) NOT NULL,
    violations   BIGINT       NOT NULL,
    status       VARCHAR(4)   NOT NULL,        -- PASS | FAIL | WARN
    executed_at  TIMESTAMP    NOT NULL,
    PRIMARY KEY (run_id, check_id)
);

-- ============================ DIMENSIONS ============================
CREATE SEQUENCE IF NOT EXISTS {schema}.seq_geography_key;
CREATE SEQUENCE IF NOT EXISTS {schema}.seq_customer_key;
CREATE SEQUENCE IF NOT EXISTS {schema}.seq_product_key;
CREATE SEQUENCE IF NOT EXISTS {schema}.seq_seller_key;
CREATE SEQUENCE IF NOT EXISTS {schema}.seq_payment_type_key;

-- Grain: one row per calendar day.
CREATE TABLE IF NOT EXISTS {schema}.D_DATE (
    date_key       INTEGER      NOT NULL,       -- YYYYMMDD; -1 = Unknown
    full_date      DATE,
    day_of_month   SMALLINT,
    day_of_week    SMALLINT,                    -- 1 = Monday .. 7 = Sunday (ISO)
    day_name       VARCHAR(9),
    week_of_year   SMALLINT,                    -- ISO week
    month_number   SMALLINT,
    month_name     VARCHAR(9),
    year_month     VARCHAR(7),                  -- 'YYYY-MM'
    quarter        SMALLINT,
    year           SMALLINT,
    is_weekend     BOOLEAN,
    row_hash       VARCHAR(32)  NOT NULL,
    PRIMARY KEY (date_key)
);

-- Grain: one row per 5-digit zip-code prefix.
CREATE TABLE IF NOT EXISTS {schema}.D_GEOGRAPHY (
    geography_key    BIGINT       NOT NULL DEFAULT nextval('{schema}.seq_geography_key'),
    zip_code_prefix  INTEGER      NOT NULL,     -- natural key
    city             VARCHAR(60),
    state            VARCHAR(2),
    region           VARCHAR(12),               -- derived: North/Northeast/Central-West/Southeast/South
    latitude         DOUBLE,                    -- centroid (mean of all points for the prefix); NULL if unknown
    longitude        DOUBLE,
    has_coordinates  BOOLEAN,                   -- derived
    row_hash         VARCHAR(32)  NOT NULL,
    dw_loaded_at     TIMESTAMP    NOT NULL DEFAULT current_timestamp,
    dw_updated_at    TIMESTAMP    NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (geography_key),
    UNIQUE (zip_code_prefix)
);

-- Grain: one row per real-world customer (customer_unique_id). Olist's customer_id is per-order.
CREATE TABLE IF NOT EXISTS {schema}.D_CUSTOMER (
    customer_key              BIGINT        NOT NULL DEFAULT nextval('{schema}.seq_customer_key'),
    customer_unique_id        VARCHAR(32)   NOT NULL,   -- natural key
    zip_code_prefix           INTEGER,                  -- from the customer's most recent order
    city                      VARCHAR(60),
    state                     VARCHAR(2),
    first_purchase_date       DATE,                     -- derived
    last_purchase_date        DATE,                     -- derived
    total_orders              INTEGER,                  -- derived: non-cancelled orders
    total_items               INTEGER,                  -- derived
    customer_lifetime_value   DECIMAL(14,2),            -- derived: SUM(price+freight) over non-cancelled orders
    average_order_value       DECIMAL(14,2),            -- derived: CLV / total_orders
    is_repeat_customer        BOOLEAN,                  -- derived: total_orders > 1
    row_hash                  VARCHAR(32)   NOT NULL,
    dw_loaded_at              TIMESTAMP     NOT NULL DEFAULT current_timestamp,
    dw_updated_at             TIMESTAMP     NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (customer_key),
    UNIQUE (customer_unique_id)
);

-- Grain: one row per product.
CREATE TABLE IF NOT EXISTS {schema}.D_PRODUCT (
    product_key          BIGINT        NOT NULL DEFAULT nextval('{schema}.seq_product_key'),
    product_id           VARCHAR(32)   NOT NULL,        -- natural key
    category_name_pt     VARCHAR(60),
    category_name_en     VARCHAR(60),                   -- translation; falls back to PT name, 'unspecified' if none
    name_length          INTEGER,                       -- source typo 'lenght' corrected
    description_length   INTEGER,
    photos_qty           INTEGER,
    weight_g             INTEGER,
    length_cm            INTEGER,
    height_cm            INTEGER,
    width_cm             INTEGER,
    volume_cm3           BIGINT,                        -- derived: L x H x W
    weight_class         VARCHAR(12),                   -- derived: Unknown/Light/Medium/Heavy/Very Heavy
    row_hash             VARCHAR(32)   NOT NULL,
    dw_loaded_at         TIMESTAMP     NOT NULL DEFAULT current_timestamp,
    dw_updated_at        TIMESTAMP     NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (product_key),
    UNIQUE (product_id)
);

-- Grain: one row per seller.
CREATE TABLE IF NOT EXISTS {schema}.D_SELLER (
    seller_key       BIGINT       NOT NULL DEFAULT nextval('{schema}.seq_seller_key'),
    seller_id        VARCHAR(32)  NOT NULL,             -- natural key
    zip_code_prefix  INTEGER,
    city             VARCHAR(60),
    state            VARCHAR(2),
    row_hash         VARCHAR(32)  NOT NULL,
    dw_loaded_at     TIMESTAMP    NOT NULL DEFAULT current_timestamp,
    dw_updated_at    TIMESTAMP    NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (seller_key),
    UNIQUE (seller_id)
);

-- Grain: one row per payment type.
CREATE TABLE IF NOT EXISTS {schema}.D_PAYMENT_TYPE (
    payment_type_key    BIGINT       NOT NULL DEFAULT nextval('{schema}.seq_payment_type_key'),
    payment_type_code   VARCHAR(20)  NOT NULL,          -- natural key (credit_card, boleto, ...)
    payment_type_name   VARCHAR(30),
    payment_method_group VARCHAR(10),                   -- derived: Card / Boleto / Voucher / Other
    row_hash            VARCHAR(32)  NOT NULL,
    dw_loaded_at        TIMESTAMP    NOT NULL DEFAULT current_timestamp,
    dw_updated_at       TIMESTAMP    NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (payment_type_key),
    UNIQUE (payment_type_code)
);

-- ============================== FACTS ==============================
-- Grain: one row per order item (order_id, order_item_id).  Process: sales.
CREATE TABLE IF NOT EXISTS {schema}.F_ORDER_ITEMS (
    order_id                 VARCHAR(32)   NOT NULL,    -- degenerate dimension
    order_item_id            SMALLINT      NOT NULL,    -- degenerate dimension (1..n within order)
    purchase_date_key        INTEGER       NOT NULL,
    shipping_limit_date_key  INTEGER       NOT NULL,
    customer_key             BIGINT        NOT NULL,
    product_key              BIGINT        NOT NULL,
    seller_key               BIGINT        NOT NULL,
    customer_geography_key   BIGINT        NOT NULL,
    seller_geography_key     BIGINT        NOT NULL,
    order_status             VARCHAR(20),               -- degenerate dimension
    item_quantity            SMALLINT,                  -- derived: always 1 (one row = one unit)
    price                    DECIMAL(10,2),
    freight_value            DECIMAL(10,2),
    total_sale_amount        DECIMAL(10,2),             -- derived: price + freight_value
    freight_ratio            DECIMAL(8,4),              -- derived: freight / price
    row_hash                 VARCHAR(32)   NOT NULL,
    dw_loaded_at             TIMESTAMP     NOT NULL DEFAULT current_timestamp,
    dw_updated_at            TIMESTAMP     NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (order_id, order_item_id)
);

-- Grain: one row per order. Accumulating snapshot (milestone dates fill in as the order progresses).
CREATE TABLE IF NOT EXISTS {schema}.F_ORDERS (
    order_id                    VARCHAR(32)  NOT NULL,
    customer_key                BIGINT       NOT NULL,
    customer_geography_key      BIGINT       NOT NULL,
    purchase_date_key           INTEGER      NOT NULL,
    approved_date_key           INTEGER      NOT NULL,
    carrier_date_key            INTEGER      NOT NULL,
    delivered_date_key          INTEGER      NOT NULL,
    estimated_delivery_date_key INTEGER      NOT NULL,
    order_status                VARCHAR(20),
    purchase_ts                 TIMESTAMP,
    approved_ts                 TIMESTAMP,
    delivered_carrier_ts        TIMESTAMP,
    delivered_customer_ts       TIMESTAMP,
    estimated_delivery_ts       TIMESTAMP,
    item_count                  INTEGER,                -- derived
    seller_count                INTEGER,                -- derived
    total_price                 DECIMAL(12,2),          -- derived: SUM(item price)
    total_freight               DECIMAL(12,2),          -- derived: SUM(item freight)
    total_order_amount          DECIMAL(12,2),          -- derived: total_price + total_freight
    total_payment_value         DECIMAL(12,2),          -- derived: SUM(payment_value)
    approval_hours              DECIMAL(10,2),          -- derived: approved - purchase       (NULL until known)
    carrier_handover_days       DECIMAL(10,2),          -- derived: carrier - approved
    delivery_days               DECIMAL(10,2),          -- derived: customer - purchase
    estimated_delivery_days     DECIMAL(10,2),          -- derived: estimated - purchase
    delivery_delay_days         DECIMAL(10,2),          -- derived: customer - estimated (>0 = late)
    is_delivered                BOOLEAN,                -- derived
    is_late                     BOOLEAN,                -- derived (NULL if not delivered)
    row_hash                    VARCHAR(32)  NOT NULL,
    dw_loaded_at                TIMESTAMP    NOT NULL DEFAULT current_timestamp,
    dw_updated_at               TIMESTAMP    NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (order_id)
);

-- Grain: one row per payment instalment record (order_id, payment_sequential).
CREATE TABLE IF NOT EXISTS {schema}.F_ORDER_PAYMENTS (
    order_id               VARCHAR(32)   NOT NULL,
    payment_sequential     SMALLINT      NOT NULL,
    purchase_date_key      INTEGER       NOT NULL,
    customer_key           BIGINT        NOT NULL,
    payment_type_key       BIGINT        NOT NULL,
    payment_installments   SMALLINT,
    payment_value          DECIMAL(12,2),
    installment_value      DECIMAL(12,2),               -- derived: payment_value / GREATEST(installments,1)
    row_hash               VARCHAR(32)   NOT NULL,
    dw_loaded_at           TIMESTAMP     NOT NULL DEFAULT current_timestamp,
    dw_updated_at          TIMESTAMP     NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (order_id, payment_sequential)
);

-- Grain: one row per review of an order (review_id, order_id).
CREATE TABLE IF NOT EXISTS {schema}.F_ORDER_REVIEWS (
    review_id                  VARCHAR(32)  NOT NULL,
    order_id                   VARCHAR(32)  NOT NULL,
    customer_key               BIGINT       NOT NULL,
    review_creation_date_key   INTEGER      NOT NULL,
    review_answer_date_key     INTEGER      NOT NULL,
    review_score               SMALLINT,
    has_comment_title          BOOLEAN,                 -- derived
    has_comment_message        BOOLEAN,                 -- derived
    comment_message_length     INTEGER,                 -- derived (0 when 'Unspecified')
    response_time_hours        DECIMAL(10,2),           -- derived: answer_ts - creation_ts
    is_positive                BOOLEAN,                 -- derived: score >= 4
    is_negative                BOOLEAN,                 -- derived: score <= 2
    row_hash                   VARCHAR(32)  NOT NULL,
    dw_loaded_at               TIMESTAMP    NOT NULL DEFAULT current_timestamp,
    dw_updated_at              TIMESTAMP    NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (review_id, order_id)
);
