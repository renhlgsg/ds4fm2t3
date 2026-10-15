"""STEP 5 - data-quality tests for the FDL_DATA star schema.

Every check is a SQL statement returning the NUMBER OF VIOLATIONS (0 = pass).
Categories requested by the contract: GRAIN, NULL, DUPLICATE, REFERENTIAL, BUSINESS (+ integrity).
Severity: ERROR -> pipeline fails.  WARN -> known source-data anomaly, reported but not fatal.
Results are persisted to FDL_DATA.DQ_RESULT_LOG so quality can be trended over runs.

Run:  python -m pipeline.dq_tests        (exit code 1 if any ERROR check fails)
"""
from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass
from datetime import datetime

from config import settings
from pipeline.db import log, session, setup_logging

F, S = settings.FDL, settings.SDL


@dataclass
class Check:
    id: str
    category: str
    severity: str
    description: str
    sql: str            # returns a single integer = violation count


CHECKS: list[Check] = []


def add(cat: str, sev: str, desc: str, sql: str) -> None:
    prefix = {"GRAIN": "G", "NULL": "N", "DUPLICATE": "D", "REFERENTIAL": "R", "BUSINESS": "B"}[cat]
    n = sum(1 for c in CHECKS if c.category == cat) + 1
    CHECKS.append(Check(f"{prefix}{n:02d}", cat, sev, desc, sql))


# ------------------------------------------------------------------ metadata of the design
FACT_PK = {
    "F_ORDER_ITEMS": ("order_id", "order_item_id"),
    "F_ORDERS": ("order_id",),
    "F_ORDER_PAYMENTS": ("order_id", "payment_sequential"),
    "F_ORDER_REVIEWS": ("review_id", "order_id"),
}
FACT_SOURCE = {"F_ORDER_ITEMS": "ORDER_ITEMS", "F_ORDERS": "ORDERS",
               "F_ORDER_PAYMENTS": "ORDER_PAYMENTS", "F_ORDER_REVIEWS": "ORDER_REVIEWS"}
DIM_NK = {"D_DATE": "date_key", "D_GEOGRAPHY": "zip_code_prefix", "D_CUSTOMER": "customer_unique_id",
          "D_PRODUCT": "product_id", "D_SELLER": "seller_id", "D_PAYMENT_TYPE": "payment_type_code"}
DIM_SK = {"D_DATE": "date_key", "D_GEOGRAPHY": "geography_key", "D_CUSTOMER": "customer_key",
          "D_PRODUCT": "product_key", "D_SELLER": "seller_key", "D_PAYMENT_TYPE": "payment_type_key"}
# (fact, fk column, dimension)
FACT_FKS = [
    ("F_ORDER_ITEMS", "purchase_date_key", "D_DATE"), ("F_ORDER_ITEMS", "shipping_limit_date_key", "D_DATE"),
    ("F_ORDER_ITEMS", "customer_key", "D_CUSTOMER"), ("F_ORDER_ITEMS", "product_key", "D_PRODUCT"),
    ("F_ORDER_ITEMS", "seller_key", "D_SELLER"), ("F_ORDER_ITEMS", "customer_geography_key", "D_GEOGRAPHY"),
    ("F_ORDER_ITEMS", "seller_geography_key", "D_GEOGRAPHY"),
    ("F_ORDERS", "customer_key", "D_CUSTOMER"), ("F_ORDERS", "customer_geography_key", "D_GEOGRAPHY"),
    ("F_ORDERS", "purchase_date_key", "D_DATE"), ("F_ORDERS", "approved_date_key", "D_DATE"),
    ("F_ORDERS", "carrier_date_key", "D_DATE"), ("F_ORDERS", "delivered_date_key", "D_DATE"),
    ("F_ORDERS", "estimated_delivery_date_key", "D_DATE"),
    ("F_ORDER_PAYMENTS", "purchase_date_key", "D_DATE"), ("F_ORDER_PAYMENTS", "customer_key", "D_CUSTOMER"),
    ("F_ORDER_PAYMENTS", "payment_type_key", "D_PAYMENT_TYPE"),
    ("F_ORDER_REVIEWS", "customer_key", "D_CUSTOMER"), ("F_ORDER_REVIEWS", "review_creation_date_key", "D_DATE"),
    ("F_ORDER_REVIEWS", "review_answer_date_key", "D_DATE"),
]
NOT_NULL_MEASURES = {
    "F_ORDER_ITEMS": ["price", "freight_value", "total_sale_amount", "item_quantity", "order_status"],
    "F_ORDERS": ["order_status", "purchase_ts", "item_count", "total_order_amount", "total_payment_value", "is_delivered"],
    "F_ORDER_PAYMENTS": ["payment_value", "payment_installments", "installment_value"],
    "F_ORDER_REVIEWS": ["review_score", "has_comment_message", "response_time_hours"],
}

# ------------------------------------------------------------------ GRAIN
for fact, src in FACT_SOURCE.items():
    add("GRAIN", "ERROR", f"{fact}: row count equals SDL_DATA.{src} row count (grain = 1 row per source record)",
        f"SELECT abs((SELECT count(*) FROM {F}.{fact}) - (SELECT count(*) FROM {S}.{src}))")
for fact, pk in FACT_PK.items():
    add("GRAIN", "ERROR", f"{fact}: exactly one row per ({', '.join(pk)}) - declared grain",
        f"SELECT count(*) - count(DISTINCT ({', '.join(pk)})) FROM {F}.{fact}")
add("GRAIN", "ERROR", "D_CUSTOMER: one row per customer_unique_id (excl. Unknown member)",
    f"SELECT abs((SELECT count(*) FROM {F}.D_CUSTOMER WHERE customer_key <> -1) - (SELECT count(DISTINCT customer_unique_id) FROM {S}.CUSTOMERS))")
add("GRAIN", "ERROR", "D_PRODUCT: one row per product_id",
    f"SELECT abs((SELECT count(*) FROM {F}.D_PRODUCT WHERE product_key <> -1) - (SELECT count(*) FROM {S}.PRODUCTS))")
add("GRAIN", "ERROR", "D_SELLER: one row per seller_id",
    f"SELECT abs((SELECT count(*) FROM {F}.D_SELLER WHERE seller_key <> -1) - (SELECT count(*) FROM {S}.SELLERS))")
add("GRAIN", "ERROR", "D_PAYMENT_TYPE: one row per distinct payment type",
    f"SELECT abs((SELECT count(*) FROM {F}.D_PAYMENT_TYPE WHERE payment_type_key <> -1) - (SELECT count(DISTINCT payment_type) FROM {S}.ORDER_PAYMENTS))")
add("GRAIN", "ERROR", "D_GEOGRAPHY: one row per zip prefix present in geolocation/customers/sellers",
    f"SELECT abs((SELECT count(*) FROM {F}.D_GEOGRAPHY WHERE geography_key <> -1) - (SELECT count(*) FROM (SELECT geolocation_zip_code_prefix z FROM {S}.GEOLOCATION UNION SELECT customer_zip_code_prefix FROM {S}.CUSTOMERS UNION SELECT seller_zip_code_prefix FROM {S}.SELLERS)))")
add("GRAIN", "ERROR", "D_DATE: one row per calendar day, no gaps (rows = max-min+1 days)",
    f"SELECT abs((SELECT count(*) FROM {F}.D_DATE WHERE date_key <> -1) - (SELECT date_diff('day', min(full_date), max(full_date)) + 1 FROM {F}.D_DATE))")
add("GRAIN", "ERROR", "F_ORDERS.item_count rolls up exactly to the F_ORDER_ITEMS row count",
    f"SELECT abs((SELECT sum(item_count) FROM {F}.F_ORDERS) - (SELECT count(*) FROM {F}.F_ORDER_ITEMS))")

# ------------------------------------------------------------------ NULL
for fact, fk, dim in FACT_FKS:
    add("NULL", "ERROR", f"{fact}.{fk} is never NULL (unknown = -1 member)",
        f"SELECT count(*) FROM {F}.{fact} WHERE {fk} IS NULL")
for fact, cols in NOT_NULL_MEASURES.items():
    for c in cols:
        add("NULL", "ERROR", f"{fact}.{c} is never NULL", f"SELECT count(*) FROM {F}.{fact} WHERE {c} IS NULL")
for dim, nk in DIM_NK.items():
    add("NULL", "ERROR", f"{dim}.{nk} (natural key) is never NULL", f"SELECT count(*) FROM {F}.{dim} WHERE {nk} IS NULL")
for fact in FACT_PK:
    add("NULL", "ERROR", f"{fact}.row_hash is never NULL", f"SELECT count(*) FROM {F}.{fact} WHERE row_hash IS NULL")

# ------------------------------------------------------------------ DUPLICATE
for dim, nk in DIM_NK.items():
    add("DUPLICATE", "ERROR", f"{dim}: natural key {nk} is unique",
        f"SELECT count(*) - count(DISTINCT {nk}) FROM {F}.{dim}")
    add("DUPLICATE", "ERROR", f"{dim}: surrogate key {DIM_SK[dim]} is unique",
        f"SELECT count(*) - count(DISTINCT {DIM_SK[dim]}) FROM {F}.{dim}")
add("DUPLICATE", "ERROR", "F_ORDER_ITEMS: no two rows carry identical business content with the same order+item",
    f"SELECT count(*) - count(DISTINCT row_hash || order_id || order_item_id) FROM {F}.F_ORDER_ITEMS")

# ------------------------------------------------------------------ REFERENTIAL
for fact, fk, dim in FACT_FKS:
    sk = DIM_SK[dim]
    add("REFERENTIAL", "ERROR", f"{fact}.{fk} -> {dim}.{sk} (no orphan keys)",
        f"SELECT count(*) FROM {F}.{fact} f LEFT JOIN {F}.{dim} d ON d.{sk} = f.{fk} WHERE d.{sk} IS NULL")
for fact, fk, dim in [("F_ORDER_ITEMS", "customer_geography_key", "D_GEOGRAPHY"),
                      ("F_ORDER_ITEMS", "seller_geography_key", "D_GEOGRAPHY"),
                      ("F_ORDER_ITEMS", "product_key", "D_PRODUCT"), ("F_ORDER_ITEMS", "customer_key", "D_CUSTOMER"),
                      ("F_ORDERS", "customer_key", "D_CUSTOMER"), ("F_ORDER_PAYMENTS", "payment_type_key", "D_PAYMENT_TYPE")]:
    add("REFERENTIAL", "WARN", f"{fact}.{fk} rows mapped to the Unknown (-1) {dim} member",
        f"SELECT count(*) FROM {F}.{fact} WHERE {fk} = -1")
add("REFERENTIAL", "ERROR", "Order lineage: every F_ORDER_ITEMS/F_ORDER_PAYMENTS/F_ORDER_REVIEWS order_id exists in F_ORDERS",
    f"""SELECT (SELECT count(*) FROM {F}.F_ORDER_ITEMS i WHERE order_id NOT IN (SELECT order_id FROM {F}.F_ORDERS))
            + (SELECT count(*) FROM {F}.F_ORDER_PAYMENTS WHERE order_id NOT IN (SELECT order_id FROM {F}.F_ORDERS))
            + (SELECT count(*) FROM {F}.F_ORDER_REVIEWS WHERE order_id NOT IN (SELECT order_id FROM {F}.F_ORDERS))""")

# ------------------------------------------------------------------ BUSINESS LOGIC
add("BUSINESS", "ERROR", "F_ORDER_ITEMS.total_sale_amount = price + freight_value",
    f"SELECT count(*) FROM {F}.F_ORDER_ITEMS WHERE total_sale_amount <> price + freight_value")
add("BUSINESS", "ERROR", "F_ORDER_ITEMS: price > 0 and freight_value >= 0",
    f"SELECT count(*) FROM {F}.F_ORDER_ITEMS WHERE price <= 0 OR freight_value < 0")
add("BUSINESS", "ERROR", "F_ORDER_ITEMS total price reconciles to SDL_DATA.ORDER_ITEMS (within 0.01)",
    f"SELECT CASE WHEN abs((SELECT sum(price) FROM {F}.F_ORDER_ITEMS) - (SELECT sum(price) FROM {S}.ORDER_ITEMS)) < 0.01 THEN 0 ELSE 1 END")
add("BUSINESS", "ERROR", "F_ORDERS.total_order_amount = SUM(F_ORDER_ITEMS.total_sale_amount) per order",
    f"""SELECT count(*) FROM {F}.F_ORDERS o LEFT JOIN
        (SELECT order_id, sum(total_sale_amount) a FROM {F}.F_ORDER_ITEMS GROUP BY order_id) i USING (order_id)
        WHERE o.total_order_amount <> COALESCE(i.a, 0)""")
add("BUSINESS", "ERROR", "F_ORDERS.total_payment_value = SUM(F_ORDER_PAYMENTS.payment_value) per order",
    f"""SELECT count(*) FROM {F}.F_ORDERS o LEFT JOIN
        (SELECT order_id, sum(payment_value) p FROM {F}.F_ORDER_PAYMENTS GROUP BY order_id) p USING (order_id)
        WHERE o.total_payment_value <> COALESCE(p.p, 0)""")
add("BUSINESS", "ERROR", "D_CUSTOMER.customer_lifetime_value = SUM(total_sale_amount) of the customer's non-cancelled orders",
    f"""SELECT count(*) FROM {F}.D_CUSTOMER c LEFT JOIN
        (SELECT customer_key, sum(total_sale_amount) v FROM {F}.F_ORDER_ITEMS
          WHERE order_status NOT IN ('canceled','unavailable') GROUP BY customer_key) f USING (customer_key)
        WHERE c.customer_key <> -1 AND c.customer_lifetime_value <> COALESCE(f.v, 0)""")
add("BUSINESS", "ERROR", "D_CUSTOMER.is_repeat_customer consistent with total_orders > 1; average_order_value <= CLV",
    f"SELECT count(*) FROM {F}.D_CUSTOMER WHERE customer_key <> -1 AND (is_repeat_customer <> (total_orders > 1) OR average_order_value > customer_lifetime_value)")
add("BUSINESS", "ERROR", "F_ORDER_REVIEWS.review_score is between 1 and 5",
    f"SELECT count(*) FROM {F}.F_ORDER_REVIEWS WHERE review_score NOT BETWEEN 1 AND 5")
add("BUSINESS", "ERROR", "F_ORDER_REVIEWS.is_positive / is_negative consistent with review_score",
    f"SELECT count(*) FROM {F}.F_ORDER_REVIEWS WHERE is_positive <> (review_score >= 4) OR is_negative <> (review_score <= 2)")
add("BUSINESS", "ERROR", "F_ORDER_REVIEWS.response_time_hours >= 0 (answer not before creation)",
    f"SELECT count(*) FROM {F}.F_ORDER_REVIEWS WHERE response_time_hours < 0")
add("BUSINESS", "ERROR", "F_ORDER_PAYMENTS.payment_value >= 0",
    f"SELECT count(*) FROM {F}.F_ORDER_PAYMENTS WHERE payment_value < 0")
add("BUSINESS", "WARN", "F_ORDER_PAYMENTS.payment_installments >= 1 (source has 0-instalment rows)",
    f"SELECT count(*) FROM {F}.F_ORDER_PAYMENTS WHERE payment_installments < 1")
add("BUSINESS", "ERROR", "F_ORDERS timeline: approval and customer delivery never precede purchase",
    f"SELECT count(*) FROM {F}.F_ORDERS WHERE delivered_customer_ts < purchase_ts OR approved_ts < purchase_ts")
add("BUSINESS", "WARN", "F_ORDERS timeline: carrier hand-over dated before purchase (source anomaly)",
    f"SELECT count(*) FROM {F}.F_ORDERS WHERE delivered_carrier_ts < purchase_ts")
add("BUSINESS", "WARN", "F_ORDERS timeline: carrier hand-over dated before approval (source anomaly)",
    f"SELECT count(*) FROM {F}.F_ORDERS WHERE delivered_carrier_ts < approved_ts")
add("BUSINESS", "WARN", "F_ORDERS timeline: customer delivery dated before carrier hand-over (source anomaly)",
    f"SELECT count(*) FROM {F}.F_ORDERS WHERE delivered_customer_ts < delivered_carrier_ts")
add("BUSINESS", "ERROR", "F_ORDERS.is_late consistent with delivery_delay_days > 0",
    f"SELECT count(*) FROM {F}.F_ORDERS WHERE is_delivered AND is_late <> (delivery_delay_days > 0)")
add("BUSINESS", "ERROR", "F_ORDERS: delivery_days >= 0 and NULL exactly when not delivered",
    f"SELECT count(*) FROM {F}.F_ORDERS WHERE delivery_days < 0 OR (is_delivered AND delivery_days IS NULL) OR (NOT is_delivered AND delivery_days IS NOT NULL)")
add("BUSINESS", "ERROR", "Date keys agree with timestamps (purchase_date_key = D_DATE of purchase_ts)",
    f"""SELECT count(*) FROM {F}.F_ORDERS o JOIN {F}.D_DATE d ON d.date_key = o.purchase_date_key
        WHERE d.full_date <> CAST(o.purchase_ts AS DATE)""")
add("BUSINESS", "WARN", "Orders with status 'delivered' but no delivery date (source anomaly)",
    f"SELECT count(*) FROM {F}.F_ORDERS WHERE order_status = 'delivered' AND NOT is_delivered")
add("BUSINESS", "WARN", "Orders NOT 'delivered' that nevertheless have a delivery date (source anomaly)",
    f"SELECT count(*) FROM {F}.F_ORDERS WHERE order_status <> 'delivered' AND is_delivered")
add("BUSINESS", "WARN", "Orders whose payments differ from items+freight by more than 1.00 (source anomaly)",
    f"SELECT count(*) FROM {F}.F_ORDERS WHERE item_count > 0 AND abs(total_payment_value - total_order_amount) > 1.00")
add("BUSINESS", "WARN", "Non-cancelled/unavailable orders with zero items",
    f"SELECT count(*) FROM {F}.F_ORDERS WHERE item_count = 0 AND order_status NOT IN ('canceled','unavailable')")
add("BUSINESS", "WARN", "Orders without any payment record",
    f"SELECT count(*) FROM {F}.F_ORDERS WHERE order_id NOT IN (SELECT order_id FROM {F}.F_ORDER_PAYMENTS)")


# ------------------------------------------------------------------ runner
def run_checks(db_path=None, persist: bool = True) -> list[dict]:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
    results = []
    with session(db_path) as con:
        for c in CHECKS:
            try:
                v = int(con.execute(c.sql).fetchone()[0] or 0)
                status = "PASS" if v == 0 else ("FAIL" if c.severity == "ERROR" else "WARN")
            except Exception as e:  # a broken test must be visible, never silently passing
                log.error("Check %s crashed: %s", c.id, e)
                v, status = -1, "FAIL"
            results.append({"run_id": run_id, "check_id": c.id, "category": c.category, "severity": c.severity,
                            "description": c.description[:250], "violations": v, "status": status,
                            "executed_at": datetime.now()})
        if persist:
            con.execute("BEGIN")
            for r in results:
                con.execute(f"INSERT INTO {F}.DQ_RESULT_LOG VALUES (?,?,?,?,?,?,?,?)", list(r.values()))
            con.execute("COMMIT")
    return results


def summarize(results: list[dict]) -> int:
    fails = [r for r in results if r["status"] == "FAIL"]
    warns = [r for r in results if r["status"] == "WARN"]
    for r in results:
        if r["status"] != "PASS":
            log.warning("%-4s %-4s %-11s %-80s violations=%d", r["status"], r["check_id"], r["category"],
                        r["description"][:80], r["violations"])
    by_cat: dict[str, list[int]] = {}
    for r in results:
        by_cat.setdefault(r["category"], [0, 0])[0 if r["status"] == "PASS" else 1] += 1
    log.info("DQ summary: %d checks | %d passed | %d failed | %d warnings | by category (pass, not-pass): %s",
             len(results), len(results) - len(fails) - len(warns), len(fails), len(warns), by_cat)
    return len(fails)


if __name__ == "__main__":
    setup_logging()
    sys.exit(1 if summarize(run_checks()) else 0)
