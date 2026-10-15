# Data lineage (table format)

## A. Layer-to-layer, table level
| Source file | RDL_DATA table | SDL_DATA table | FDL_DATA target(s) | Transformation SQL |
|---|---|---|---|---|
| olist_geolocation_dataset.csv | GEOLOCATION | GEOLOCATION | D_GEOGRAPHY | `sql/elt/d_geography.sql` |
| olist_customers_dataset.csv | CUSTOMERS | CUSTOMERS | D_CUSTOMER, D_GEOGRAPHY (zip fallback); customer key lookup in all facts | `d_customer.sql`, `d_geography.sql` |
| olist_sellers_dataset.csv | SELLERS | SELLERS | D_SELLER, D_GEOGRAPHY (zip fallback) | `d_seller.sql` |
| olist_products_dataset.csv | PRODUCTS | PRODUCTS | D_PRODUCT | `d_product.sql` |
| product_category_name_translation.csv | PRODUCT_CATEGORY_TRANSLATION | PRODUCT_CATEGORY_TRANSLATION | D_PRODUCT.category_name_en | `d_product.sql` |
| olist_orders_dataset.csv | ORDERS | ORDERS | F_ORDERS, F_ORDER_ITEMS/PAYMENTS/REVIEWS (dates, customer), D_DATE, D_CUSTOMER (aggregates) | `f_orders.sql`, `d_customer.sql`, `d_date.sql` |
| olist_order_items_dataset.csv | ORDER_ITEMS | ORDER_ITEMS | F_ORDER_ITEMS, F_ORDERS (aggregates), D_CUSTOMER (CLV) | `f_order_items.sql` |
| olist_order_payments_dataset.csv | ORDER_PAYMENTS | ORDER_PAYMENTS | F_ORDER_PAYMENTS, F_ORDERS.total_payment_value, D_PAYMENT_TYPE | `f_order_payments.sql`, `d_payment_type.sql` |
| olist_order_reviews_dataset.csv | ORDER_REVIEWS | ORDER_REVIEWS | F_ORDER_REVIEWS, D_DATE (range) | `f_order_reviews.sql` |

Layer rules: CSV -> RDL: typed load, no changes (`ingest_rdl.py`). RDL -> SDL: contract cleaning rules (`clean_sdl.py`). SDL -> FDL: SQL above, loaded incrementally by `elt_fdl.py`.

## B. Column level - derived and renamed columns
| Target column | Source column(s) | Rule |
|---|---|---|
| D_DATE.* | min/max of every timestamp in ORDERS, ORDER_ITEMS, ORDER_REVIEWS | calendar generated for whole years between min and max |
| D_GEOGRAPHY.city / state | GEOLOCATION.geolocation_city/state (else CUSTOMERS/SELLERS) | accents stripped, lower-cased, most frequent spelling per zip |
| D_GEOGRAPHY.latitude / longitude | GEOLOCATION.geolocation_lat/lng | median per zip, only points inside Brazil bounding box |
| D_GEOGRAPHY.region | state | state -> 5 regions mapping |
| D_CUSTOMER (grain) | CUSTOMERS.customer_unique_id | one row per unique customer; zip/city/state from the most recent order |
| D_CUSTOMER.total_orders | ORDERS | distinct valid orders |
| D_CUSTOMER.total_items | ORDER_ITEMS | item rows of valid orders |
| D_CUSTOMER.customer_lifetime_value | ORDER_ITEMS.price + freight_value | sum over valid orders |
| D_CUSTOMER.average_order_value | CLV, total_orders | CLV / total_orders |
| D_CUSTOMER.is_repeat_customer | total_orders | `> 1` |
| D_PRODUCT.category_name_en | PRODUCT_CATEGORY_TRANSLATION | translation, fallback to Portuguese name |
| D_PRODUCT.name_length / description_length | PRODUCTS.product_name_lenght / product_description_lenght | renamed (source typo fixed) |
| D_PRODUCT.volume_cm3 | length x height x width | NULL if any is 0 |
| D_PRODUCT.weight_class | product_weight_g | 0 Unknown, <500 Light, <2000 Medium, <10000 Heavy, else Very Heavy |
| D_PAYMENT_TYPE.payment_method_group | payment_type | credit/debit -> Card; boleto; voucher; else Other |
| F_ORDER_ITEMS.*_date_key | ORDERS.order_purchase_timestamp, ORDER_ITEMS.shipping_limit_date | YYYYMMDD, -1 if NULL |
| F_ORDER_ITEMS.customer_key | ORDER_ITEMS.order_id -> ORDERS.customer_id -> CUSTOMERS.customer_unique_id -> D_CUSTOMER | lookup |
| F_ORDER_ITEMS.total_sale_amount | price, freight_value | price + freight_value |
| F_ORDER_ITEMS.freight_ratio | price, freight_value | freight / price |
| F_ORDERS.item_count, seller_count, total_price, total_freight | ORDER_ITEMS | aggregate per order |
| F_ORDERS.total_order_amount | total_price, total_freight | sum |
| F_ORDERS.total_payment_value | ORDER_PAYMENTS.payment_value | sum per order |
| F_ORDERS.approval_hours | ORDERS approved_at - purchase_timestamp | hours |
| F_ORDERS.delivery_days | order_delivered_customer_date - order_purchase_timestamp | days; NULL if undelivered |
| F_ORDERS.delivery_delay_days | delivered date - estimated date | calendar days, positive = late |
| F_ORDERS.is_late | delivered date, estimated date | delivered date > estimated date; NULL if undelivered |
| F_ORDER_PAYMENTS.installment_value | payment_value, payment_installments | value / max(installments, 1) |
| F_ORDER_REVIEWS.has_comment_* | review_comment_title / _message | not `'Unspecified'` |
| F_ORDER_REVIEWS.response_time_hours | review_answer_timestamp - review_creation_date | hours |
| F_ORDER_REVIEWS.is_positive / is_negative | review_score | >= 4 / <= 2 |
| every dimension and fact `row_hash` | all business columns | md5 for change detection |

## C. Downstream consumers
| Consumer | Reads | Code |
|---|---|---|
| Streamlit dashboard | F_*, D_*, DQ_RESULT_LOG, ETL_RUN_LOG | `app/streamlit_app.py` -> `analysis/eda.py` |
| Notebook | F_*, D_* | `notebooks/01_eda.ipynb` -> `analysis/eda.py` |
| Findings / slides | F_*, D_* | `findings/f1..f5_*.py` -> `slides/` |
