"""Pandas analysis functions over the FDL_DATA star schema (read-only).

Used by: notebooks/01_eda.ipynb, app/streamlit_app.py and findings/*.py so every number in the
report, the dashboard and the slides comes from the same code.

"Valid" orders = status NOT IN ('canceled','unavailable').
Revenue = SUM(price) (merchandise value);  GMV = SUM(price + freight).
"""
from __future__ import annotations

import duckdb
import pandas as pd

from config import settings

F = settings.FDL
VALID = "order_status NOT IN ('canceled','unavailable')"


def query(sql: str, db_path=None) -> pd.DataFrame:
    con = duckdb.connect(str(db_path or settings.DB_PATH), read_only=True)
    try:
        return con.execute(sql).df()
    finally:
        con.close()


# ------------------------------------------------------------------ headline KPIs
def kpis(db_path=None) -> pd.Series:
    return query(f"""
        SELECT count(DISTINCT order_id)                              AS orders,
               count(*)                                              AS items_sold,
               round(sum(price), 2)                                  AS revenue,
               round(sum(total_sale_amount), 2)                      AS gmv_incl_freight,
               round(sum(price) / count(DISTINCT order_id), 2)       AS avg_order_value,
               count(DISTINCT customer_key)                          AS customers,
               count(DISTINCT seller_key)                            AS sellers,
               count(DISTINCT product_key)                           AS products
        FROM {F}.F_ORDER_ITEMS WHERE {VALID}""", db_path).iloc[0]


# ------------------------------------------------------------------ 1. monthly sales trends
def monthly_sales(db_path=None) -> pd.DataFrame:
    df = query(f"""
        SELECT d.year_month, min(d.full_date) AS month_start,
               count(DISTINCT i.order_id) AS orders, count(*) AS items,
               round(sum(i.price), 2) AS revenue, round(sum(i.total_sale_amount), 2) AS gmv,
               round(sum(i.price) / count(DISTINCT i.order_id), 2) AS avg_order_value
        FROM {F}.F_ORDER_ITEMS i JOIN {F}.D_DATE d ON d.date_key = i.purchase_date_key
        WHERE i.{VALID} GROUP BY d.year_month ORDER BY d.year_month""", db_path)
    df["revenue_mom_pct"] = (df["revenue"].pct_change() * 100).round(1)
    df["revenue_3m_avg"] = df["revenue"].rolling(3).mean().round(2)
    return df


def sales_by_weekday(db_path=None) -> pd.DataFrame:
    return query(f"""
        SELECT d.day_of_week, d.day_name, count(DISTINCT i.order_id) AS orders, round(sum(i.price),2) AS revenue
        FROM {F}.F_ORDER_ITEMS i JOIN {F}.D_DATE d ON d.date_key = i.purchase_date_key
        WHERE i.{VALID} GROUP BY ALL ORDER BY d.day_of_week""", db_path)


# ------------------------------------------------------------------ 2. top-selling products
def top_products(n: int = 10, by: str = "revenue", db_path=None) -> pd.DataFrame:
    order = {"revenue": "revenue", "units": "units"}[by]
    return query(f"""
        SELECT p.product_id, p.category_name_en AS category, count(*) AS units,
               round(sum(i.price), 2) AS revenue, round(avg(i.price), 2) AS avg_price
        FROM {F}.F_ORDER_ITEMS i JOIN {F}.D_PRODUCT p USING (product_key)
        WHERE i.{VALID} GROUP BY ALL ORDER BY {order} DESC LIMIT {int(n)}""", db_path)


def top_categories(n: int = 10, db_path=None) -> pd.DataFrame:
    df = query(f"""
        SELECT p.category_name_en AS category, count(*) AS units, count(DISTINCT i.order_id) AS orders,
               round(sum(i.price), 2) AS revenue, round(avg(i.price), 2) AS avg_price
        FROM {F}.F_ORDER_ITEMS i JOIN {F}.D_PRODUCT p USING (product_key)
        WHERE i.{VALID} GROUP BY ALL ORDER BY revenue DESC""", db_path)
    df["revenue_share_pct"] = (df["revenue"] / df["revenue"].sum() * 100).round(2)
    df["cum_share_pct"] = df["revenue_share_pct"].cumsum().round(2)
    return df.head(n)


def seller_concentration(db_path=None) -> pd.DataFrame:
    df = query(f"""
        SELECT s.seller_id, s.state, count(*) AS units, round(sum(i.price),2) AS revenue
        FROM {F}.F_ORDER_ITEMS i JOIN {F}.D_SELLER s USING (seller_key)
        WHERE i.{VALID} GROUP BY ALL ORDER BY revenue DESC""", db_path)
    df["cum_share_pct"] = (df["revenue"].cumsum() / df["revenue"].sum() * 100).round(2)
    return df


# ------------------------------------------------------------------ 3. customer segmentation
def customer_rfm(db_path=None) -> pd.DataFrame:
    """One row per customer with Recency/Frequency/Monetary + a behavioural segment."""
    df = query(f"""
        SELECT customer_key, customer_unique_id, state, first_purchase_date, last_purchase_date,
               total_orders AS frequency, customer_lifetime_value AS monetary,
               average_order_value, is_repeat_customer
        FROM {F}.D_CUSTOMER WHERE customer_key <> -1 AND total_orders > 0""", db_path)
    df["last_purchase_date"] = pd.to_datetime(df["last_purchase_date"])
    ref = df["last_purchase_date"].max() + pd.Timedelta(days=1)
    df["recency_days"] = (ref - df["last_purchase_date"]).dt.days
    df["monetary"] = df["monetary"].astype(float)
    r_med = df["recency_days"].median()
    m_q75 = df["monetary"].quantile(0.75)
    r_q25 = df["recency_days"].quantile(0.25)

    def seg(r):
        if r.frequency >= 2:
            return "Loyal repeat" if r.recency_days <= r_med else "At-risk repeat"
        if r.monetary >= m_q75:
            return "New high-value" if r.recency_days <= r_q25 else "Big-ticket one-time"
        return "Recent one-time" if r.recency_days <= r_med else "Lapsed one-time"

    df["segment"] = df.apply(seg, axis=1)
    return df


def segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    g = rfm.groupby("segment").agg(customers=("customer_key", "count"), revenue=("monetary", "sum"),
                                   avg_clv=("monetary", "mean"), avg_orders=("frequency", "mean"),
                                   avg_recency_days=("recency_days", "mean")).round(2)
    g["customer_share_pct"] = (g["customers"] / g["customers"].sum() * 100).round(2)
    g["revenue_share_pct"] = (g["revenue"] / g["revenue"].sum() * 100).round(2)
    return g.sort_values("revenue", ascending=False).reset_index()


def repeat_rate(rfm: pd.DataFrame) -> float:
    return round(float((rfm["frequency"] >= 2).mean() * 100), 2)


# ------------------------------------------------------------------ 4. delivery & reviews
def delivery_by_state(db_path=None) -> pd.DataFrame:
    return query(f"""
        SELECT g.state, g.region, count(*) AS delivered_orders,
               round(avg(o.delivery_days), 1) AS avg_delivery_days,
               round(avg(o.estimated_delivery_days), 1) AS avg_estimated_days,
               round(avg(CASE WHEN o.is_late THEN 1.0 ELSE 0 END) * 100, 1) AS late_pct
        FROM {F}.F_ORDERS o JOIN {F}.D_GEOGRAPHY g ON g.geography_key = o.customer_geography_key
        WHERE o.is_delivered AND o.order_status = 'delivered' GROUP BY ALL ORDER BY avg_delivery_days DESC""", db_path)


def review_vs_lateness(db_path=None) -> pd.DataFrame:
    return query(f"""
        SELECT CASE WHEN o.is_late THEN 'Late' ELSE 'On time' END AS delivery,
               count(*) AS reviews, round(avg(r.review_score), 2) AS avg_score,
               round(avg(CASE WHEN r.is_negative THEN 1.0 ELSE 0 END) * 100, 1) AS negative_pct
        FROM {F}.F_ORDER_REVIEWS r JOIN {F}.F_ORDERS o USING (order_id)
        WHERE o.is_delivered AND o.order_status = 'delivered' GROUP BY ALL ORDER BY 1""", db_path)


def review_by_delay_bucket(db_path=None) -> pd.DataFrame:
    return query(f"""
        SELECT CASE WHEN o.delivery_delay_days <= -7 THEN '1) 7+ days early'
                    WHEN o.delivery_delay_days <= 0  THEN '2) 0-6 days early / on day'
                    WHEN o.delivery_delay_days <= 7  THEN '3) 1-7 days late'
                    ELSE '4) 8+ days late' END AS delivery_vs_promise,
               count(*) AS reviews, round(avg(r.review_score), 2) AS avg_score
        FROM {F}.F_ORDER_REVIEWS r JOIN {F}.F_ORDERS o USING (order_id)
        WHERE o.is_delivered AND o.order_status = 'delivered' GROUP BY ALL ORDER BY 1""", db_path)


# ------------------------------------------------------------------ 5. payments & geography
def payment_mix(db_path=None) -> pd.DataFrame:
    df = query(f"""
        SELECT pt.payment_type_name AS payment_type, count(*) AS payments,
               round(sum(p.payment_value), 2) AS value, round(avg(p.payment_installments), 2) AS avg_installments
        FROM {F}.F_ORDER_PAYMENTS p JOIN {F}.D_PAYMENT_TYPE pt USING (payment_type_key)
        GROUP BY ALL ORDER BY value DESC""", db_path)
    df["value_share_pct"] = (df["value"] / df["value"].sum() * 100).round(2)
    return df


def revenue_by_state(db_path=None) -> pd.DataFrame:
    df = query(f"""
        SELECT g.state, g.region, count(DISTINCT i.order_id) AS orders, round(sum(i.price),2) AS revenue,
               count(DISTINCT i.customer_key) AS customers
        FROM {F}.F_ORDER_ITEMS i JOIN {F}.D_GEOGRAPHY g ON g.geography_key = i.customer_geography_key
        WHERE i.{VALID} GROUP BY ALL ORDER BY revenue DESC""", db_path)
    df["revenue_share_pct"] = (df["revenue"] / df["revenue"].sum() * 100).round(2)
    return df


# ------------------------------------------------------------------ pipeline / DQ metadata (dashboard)
def latest_dq(db_path=None) -> pd.DataFrame:
    return query(f"""SELECT * FROM {F}.DQ_RESULT_LOG
                     WHERE run_id = (SELECT run_id FROM {F}.DQ_RESULT_LOG ORDER BY executed_at DESC LIMIT 1)
                     ORDER BY check_id""", db_path)


def etl_runs(db_path=None) -> pd.DataFrame:
    return query(f"SELECT * FROM {F}.ETL_RUN_LOG ORDER BY started_at DESC, target_table", db_path)
