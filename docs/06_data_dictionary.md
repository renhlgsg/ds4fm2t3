# Data dictionary - FDL_DATA (generated from `sql/fdl/create_fdl_tables.sql`)

Legend: **PK** primary key, **UK** unique natural key, **FK** logical foreign key (not physically declared - see design document), **derived** = computed by the ELT. Unknown member: key `-1` exists in every dimension.


## ETL_RUN_LOG

| Column | Type | Key | Nullable | Description / derivation |
|---|---|---|---|---|
| `run_id` | VARCHAR | PK | No |  |
| `target_table` | VARCHAR(40) | PK | No |  |
| `run_type` | VARCHAR(12) |  | No | INITIAL / INCREMENTAL |
| `rows_inserted` | BIGINT |  | No |  |
| `rows_updated` | BIGINT |  | No |  |
| `rows_total` | BIGINT |  | No |  |
| `started_at` | TIMESTAMP |  | No |  |
| `finished_at` | TIMESTAMP |  | No |  |

Composite primary key: (run_id, target_table)

## DQ_RESULT_LOG

| Column | Type | Key | Nullable | Description / derivation |
|---|---|---|---|---|
| `run_id` | VARCHAR | PK | No |  |
| `check_id` | VARCHAR(10) | PK | No |  |
| `category` | VARCHAR(20) |  | No | GRAIN / NULL / DUPLICATE / REFERENTIAL / BUSINESS |
| `severity` | VARCHAR(5) |  | No | ERROR / WARN |
| `description` | VARCHAR(250) |  | No |  |
| `violations` | BIGINT |  | No |  |
| `status` | VARCHAR(4) |  | No | PASS / FAIL / WARN |
| `executed_at` | TIMESTAMP |  | No |  |

Composite primary key: (run_id, check_id)

## D_DATE

**Grain:** one row per calendar day.

| Column | Type | Key | Nullable | Description / derivation |
|---|---|---|---|---|
| `date_key` | INTEGER | PK | No | YYYYMMDD; -1 = Unknown |
| `full_date` | DATE |  | Yes |  |
| `day_of_month` | SMALLINT |  | Yes |  |
| `day_of_week` | SMALLINT |  | Yes | 1 = Monday .. 7 = Sunday (ISO) |
| `day_name` | VARCHAR(9) |  | Yes |  |
| `week_of_year` | SMALLINT |  | Yes | ISO week |
| `month_number` | SMALLINT |  | Yes |  |
| `month_name` | VARCHAR(9) |  | Yes |  |
| `year_month` | VARCHAR(7) |  | Yes | 'YYYY-MM' |
| `quarter` | SMALLINT |  | Yes |  |
| `year` | SMALLINT |  | Yes |  |
| `is_weekend` | BOOLEAN |  | Yes |  |
| `row_hash` | VARCHAR(32) |  | No |  |

## D_GEOGRAPHY

**Grain:** one row per 5-digit zip-code prefix.

| Column | Type | Key | Nullable | Description / derivation |
|---|---|---|---|---|
| `geography_key` | BIGINT | PK | No |  |
| `zip_code_prefix` | INTEGER | UK | No | natural key |
| `city` | VARCHAR(60) |  | Yes |  |
| `state` | VARCHAR(2) |  | Yes |  |
| `region` | VARCHAR(12) | derived | Yes | derived: North/Northeast/Central-West/Southeast/South |
| `latitude` | DOUBLE |  | Yes | centroid (mean of all points for the prefix); NULL if unknown |
| `longitude` | DOUBLE |  | Yes |  |
| `has_coordinates` | BOOLEAN | derived | Yes | derived |
| `row_hash` | VARCHAR(32) |  | No |  |
| `dw_loaded_at` | TIMESTAMP |  | No |  |
| `dw_updated_at` | TIMESTAMP |  | No |  |

## D_CUSTOMER

**Grain:** one row per real-world customer (customer_unique_id). Olist's customer_id is per-order.

| Column | Type | Key | Nullable | Description / derivation |
|---|---|---|---|---|
| `customer_key` | BIGINT | PK | No |  |
| `customer_unique_id` | VARCHAR(32) | UK | No | natural key |
| `zip_code_prefix` | INTEGER |  | Yes | from the customer's most recent order |
| `city` | VARCHAR(60) |  | Yes |  |
| `state` | VARCHAR(2) |  | Yes |  |
| `first_purchase_date` | DATE | derived | Yes | derived |
| `last_purchase_date` | DATE | derived | Yes | derived |
| `total_orders` | INTEGER | derived | Yes | derived: non-cancelled orders |
| `total_items` | INTEGER | derived | Yes | derived |
| `customer_lifetime_value` | DECIMAL(14,2) | derived | Yes | derived: SUM(price+freight) over non-cancelled orders |
| `average_order_value` | DECIMAL(14,2) | derived | Yes | derived: CLV / total_orders |
| `is_repeat_customer` | BOOLEAN | derived | Yes | derived: total_orders > 1 |
| `row_hash` | VARCHAR(32) |  | No |  |
| `dw_loaded_at` | TIMESTAMP |  | No |  |
| `dw_updated_at` | TIMESTAMP |  | No |  |

## D_PRODUCT

**Grain:** one row per product.

| Column | Type | Key | Nullable | Description / derivation |
|---|---|---|---|---|
| `product_key` | BIGINT | PK | No |  |
| `product_id` | VARCHAR(32) | UK | No | natural key |
| `category_name_pt` | VARCHAR(60) |  | Yes |  |
| `category_name_en` | VARCHAR(60) |  | Yes | translation; falls back to PT name, 'unspecified' if none |
| `name_length` | INTEGER |  | Yes | source typo 'lenght' corrected |
| `description_length` | INTEGER |  | Yes |  |
| `photos_qty` | INTEGER |  | Yes |  |
| `weight_g` | INTEGER |  | Yes |  |
| `length_cm` | INTEGER |  | Yes |  |
| `height_cm` | INTEGER |  | Yes |  |
| `width_cm` | INTEGER |  | Yes |  |
| `volume_cm3` | BIGINT | derived | Yes | derived: L x H x W |
| `weight_class` | VARCHAR(12) | derived | Yes | derived: Unknown/Light/Medium/Heavy/Very Heavy |
| `row_hash` | VARCHAR(32) |  | No |  |
| `dw_loaded_at` | TIMESTAMP |  | No |  |
| `dw_updated_at` | TIMESTAMP |  | No |  |

## D_SELLER

**Grain:** one row per seller.

| Column | Type | Key | Nullable | Description / derivation |
|---|---|---|---|---|
| `seller_key` | BIGINT | PK | No |  |
| `seller_id` | VARCHAR(32) | UK | No | natural key |
| `zip_code_prefix` | INTEGER |  | Yes |  |
| `city` | VARCHAR(60) |  | Yes |  |
| `state` | VARCHAR(2) |  | Yes |  |
| `row_hash` | VARCHAR(32) |  | No |  |
| `dw_loaded_at` | TIMESTAMP |  | No |  |
| `dw_updated_at` | TIMESTAMP |  | No |  |

## D_PAYMENT_TYPE

**Grain:** one row per payment type.

| Column | Type | Key | Nullable | Description / derivation |
|---|---|---|---|---|
| `payment_type_key` | BIGINT | PK | No |  |
| `payment_type_code` | VARCHAR(20) | UK | No | natural key (credit_card, boleto, ...) |
| `payment_type_name` | VARCHAR(30) |  | Yes |  |
| `payment_method_group` | VARCHAR(10) | derived | Yes | derived: Card / Boleto / Voucher / Other |
| `row_hash` | VARCHAR(32) |  | No |  |
| `dw_loaded_at` | TIMESTAMP |  | No |  |
| `dw_updated_at` | TIMESTAMP |  | No |  |

## F_ORDER_ITEMS

**Grain:** one row per order item (order_id, order_item_id).  Process: sales.

| Column | Type | Key | Nullable | Description / derivation |
|---|---|---|---|---|
| `order_id` | VARCHAR(32) | PK | No | degenerate dimension |
| `order_item_id` | SMALLINT | PK | No | degenerate dimension (1..n within order) |
| `purchase_date_key` | INTEGER | FK | No |  |
| `shipping_limit_date_key` | INTEGER | FK | No |  |
| `customer_key` | BIGINT | FK | No |  |
| `product_key` | BIGINT | FK | No |  |
| `seller_key` | BIGINT | FK | No |  |
| `customer_geography_key` | BIGINT | FK | No |  |
| `seller_geography_key` | BIGINT | FK | No |  |
| `order_status` | VARCHAR(20) |  | Yes | degenerate dimension |
| `item_quantity` | SMALLINT | derived | Yes | derived: always 1 (one row = one unit) |
| `price` | DECIMAL(10,2) |  | Yes |  |
| `freight_value` | DECIMAL(10,2) |  | Yes |  |
| `total_sale_amount` | DECIMAL(10,2) | derived | Yes | derived: price + freight_value |
| `freight_ratio` | DECIMAL(8,4) | derived | Yes | derived: freight / price |
| `row_hash` | VARCHAR(32) |  | No |  |
| `dw_loaded_at` | TIMESTAMP |  | No |  |
| `dw_updated_at` | TIMESTAMP |  | No |  |

Composite primary key: (order_id, order_item_id)

## F_ORDERS

**Grain:** one row per order. Accumulating snapshot (milestone dates fill in as the order progresses).

| Column | Type | Key | Nullable | Description / derivation |
|---|---|---|---|---|
| `order_id` | VARCHAR(32) | PK | No |  |
| `customer_key` | BIGINT | FK | No |  |
| `customer_geography_key` | BIGINT | FK | No |  |
| `purchase_date_key` | INTEGER | FK | No |  |
| `approved_date_key` | INTEGER | FK | No |  |
| `carrier_date_key` | INTEGER | FK | No |  |
| `delivered_date_key` | INTEGER | FK | No |  |
| `estimated_delivery_date_key` | INTEGER | FK | No |  |
| `order_status` | VARCHAR(20) |  | Yes |  |
| `purchase_ts` | TIMESTAMP |  | Yes |  |
| `approved_ts` | TIMESTAMP |  | Yes |  |
| `delivered_carrier_ts` | TIMESTAMP |  | Yes |  |
| `delivered_customer_ts` | TIMESTAMP |  | Yes |  |
| `estimated_delivery_ts` | TIMESTAMP |  | Yes |  |
| `item_count` | INTEGER | derived | Yes | derived |
| `seller_count` | INTEGER | derived | Yes | derived |
| `total_price` | DECIMAL(12,2) | derived | Yes | derived: SUM(item price) |
| `total_freight` | DECIMAL(12,2) | derived | Yes | derived: SUM(item freight) |
| `total_order_amount` | DECIMAL(12,2) | derived | Yes | derived: total_price + total_freight |
| `total_payment_value` | DECIMAL(12,2) | derived | Yes | derived: SUM(payment_value) |
| `approval_hours` | DECIMAL(10,2) | derived | Yes | derived: approved - purchase       (NULL until known) |
| `carrier_handover_days` | DECIMAL(10,2) | derived | Yes | derived: carrier - approved |
| `delivery_days` | DECIMAL(10,2) | derived | Yes | derived: customer - purchase |
| `estimated_delivery_days` | DECIMAL(10,2) | derived | Yes | derived: estimated - purchase |
| `delivery_delay_days` | DECIMAL(10,2) | derived | Yes | derived: customer - estimated (>0 = late) |
| `is_delivered` | BOOLEAN | derived | Yes | derived |
| `is_late` | BOOLEAN | derived | Yes | derived (NULL if not delivered) |
| `row_hash` | VARCHAR(32) |  | No |  |
| `dw_loaded_at` | TIMESTAMP |  | No |  |
| `dw_updated_at` | TIMESTAMP |  | No |  |

## F_ORDER_PAYMENTS

**Grain:** one row per payment instalment record (order_id, payment_sequential).

| Column | Type | Key | Nullable | Description / derivation |
|---|---|---|---|---|
| `order_id` | VARCHAR(32) | PK | No |  |
| `payment_sequential` | SMALLINT | PK | No |  |
| `purchase_date_key` | INTEGER | FK | No |  |
| `customer_key` | BIGINT | FK | No |  |
| `payment_type_key` | BIGINT | FK | No |  |
| `payment_installments` | SMALLINT |  | Yes |  |
| `payment_value` | DECIMAL(12,2) |  | Yes |  |
| `installment_value` | DECIMAL(12,2) | derived | Yes | derived: payment_value / GREATEST(installments,1) |
| `row_hash` | VARCHAR(32) |  | No |  |
| `dw_loaded_at` | TIMESTAMP |  | No |  |
| `dw_updated_at` | TIMESTAMP |  | No |  |

Composite primary key: (order_id, payment_sequential)

## F_ORDER_REVIEWS

**Grain:** one row per review of an order (review_id, order_id).

| Column | Type | Key | Nullable | Description / derivation |
|---|---|---|---|---|
| `review_id` | VARCHAR(32) | PK | No |  |
| `order_id` | VARCHAR(32) | PK | No |  |
| `customer_key` | BIGINT | FK | No |  |
| `review_creation_date_key` | INTEGER | FK | No |  |
| `review_answer_date_key` | INTEGER | FK | No |  |
| `review_score` | SMALLINT |  | Yes |  |
| `has_comment_title` | BOOLEAN | derived | Yes | derived |
| `has_comment_message` | BOOLEAN | derived | Yes | derived |
| `comment_message_length` | INTEGER | derived | Yes | derived (0 when 'Unspecified') |
| `response_time_hours` | DECIMAL(10,2) | derived | Yes | derived: answer_ts - creation_ts |
| `is_positive` | BOOLEAN | derived | Yes | derived: score >= 4 |
| `is_negative` | BOOLEAN | derived | Yes | derived: score <= 2 |
| `row_hash` | VARCHAR(32) |  | No |  |
| `dw_loaded_at` | TIMESTAMP |  | No |  |
| `dw_updated_at` | TIMESTAMP |  | No |  |

Composite primary key: (review_id, order_id)
