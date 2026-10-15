"""Streamlit dashboard over the FDL_DATA star schema.

Run from the project root:   streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # make `config` / `analysis` importable

import plotly.express as px
import streamlit as st

from analysis import eda
from config import settings

st.set_page_config(page_title="Olist DW - ds4fm2t3", layout="wide")


@st.cache_data(ttl=300, show_spinner="Querying DuckDB ...")
def load(name: str, *args):
    return getattr(eda, name)(*args)


if not Path(settings.DB_PATH).exists():
    st.error(f"Database not found at {settings.DB_PATH}. Run `python -m pipeline.run_all` first.")
    st.stop()

page = st.sidebar.radio("Page", ["Overview", "Monthly sales", "Products & sellers", "Customers",
                                 "Delivery & reviews", "Payments & geography", "Pipeline & data quality"])
st.sidebar.caption("Source: DuckDB schema FDL_DATA (star schema). 'Valid' orders exclude canceled/unavailable.")

if page == "Overview":
    st.title("Olist e-commerce - executive overview")
    k = load("kpis")
    c = st.columns(4)
    c[0].metric("Revenue (BRL)", f"{k.revenue:,.0f}")
    c[1].metric("Orders", f"{int(k.orders):,}")
    c[2].metric("Avg order value", f"{k.avg_order_value:,.2f}")
    c[3].metric("Customers", f"{int(k.customers):,}")
    c = st.columns(4)
    c[0].metric("GMV incl. freight", f"{k.gmv_incl_freight:,.0f}")
    c[1].metric("Items sold", f"{int(k.items_sold):,}")
    c[2].metric("Sellers", f"{int(k.sellers):,}")
    c[3].metric("Products", f"{int(k.products):,}")
    m = load("monthly_sales")
    m = m[m.orders >= 100]
    st.plotly_chart(px.bar(m, x="year_month", y="revenue", title="Monthly revenue (months with >= 100 orders)"),
                    width="stretch")

elif page == "Monthly sales":
    st.title("Monthly sales trends")
    m = load("monthly_sales")
    hide = st.checkbox("Hide partial months (< 100 orders)", value=True)
    if hide:
        m = m[m.orders >= 100]
    metric = st.selectbox("Metric", ["revenue", "gmv", "orders", "items", "avg_order_value"])
    st.plotly_chart(px.line(m, x="year_month", y=metric, markers=True), width="stretch")
    st.dataframe(m, width="stretch")
    w = load("sales_by_weekday")
    st.plotly_chart(px.bar(w, x="day_name", y="orders", title="Orders by weekday"), width="stretch")

elif page == "Products & sellers":
    st.title("Top-selling products, categories and sellers")
    n = st.slider("Top N", 5, 30, 10)
    by = st.radio("Rank products by", ["revenue", "units"], horizontal=True)
    cats = load("top_categories", n)
    st.plotly_chart(px.bar(cats, x="revenue", y="category", orientation="h", title="Top categories by revenue")
                    .update_yaxes(autorange="reversed"), width="stretch")
    st.subheader(f"Top {n} products by {by}")
    st.dataframe(load("top_products", n, by), width="stretch")
    s = load("seller_concentration")
    st.caption(f"Top 10% of sellers generate {s.iloc[int(len(s) * .1) - 1].cum_share_pct:.1f}% of revenue.")

elif page == "Customers":
    st.title("Customer segmentation by purchase behaviour")
    rfm = load("customer_rfm")
    seg = eda.segment_summary(rfm)
    st.metric("Repeat-purchase rate", f"{eda.repeat_rate(rfm)}%")
    a, b = st.columns(2)
    a.plotly_chart(px.pie(seg, names="segment", values="customers", title="Customers"), width="stretch")
    b.plotly_chart(px.pie(seg, names="segment", values="revenue", title="Lifetime revenue"), width="stretch")
    st.dataframe(seg, width="stretch")

elif page == "Delivery & reviews":
    st.title("Delivery performance and reviews")
    st.dataframe(load("review_vs_lateness"), width="stretch")
    st.plotly_chart(px.bar(load("review_by_delay_bucket"), x="delivery_vs_promise", y="avg_score"), width="stretch")
    d = load("delivery_by_state")
    st.plotly_chart(px.bar(d, x="state", y="avg_delivery_days", color="late_pct", title="Avg delivery days by state"),
                    width="stretch")

elif page == "Payments & geography":
    st.title("Payments and geography")
    p = load("payment_mix")
    a, b = st.columns(2)
    a.plotly_chart(px.pie(p[p.value > 0], names="payment_type", values="value", title="Payment value"), width="stretch")
    g = load("revenue_by_state")
    b.plotly_chart(px.bar(g.head(10), x="state", y="revenue", title="Top 10 states by revenue"), width="stretch")
    st.dataframe(g, width="stretch")

else:
    st.title("Pipeline runs and data quality")
    dq = eda.latest_dq()
    if dq.empty:
        st.info("No DQ results yet - run `python -m pipeline.dq_tests`.")
    else:
        c = st.columns(3)
        c[0].metric("Checks", len(dq))
        c[1].metric("Failed (ERROR)", int((dq.status == "FAIL").sum()))
        c[2].metric("Warnings (known source anomalies)", int((dq.status == "WARN").sum()))
        st.dataframe(dq[dq.status != "PASS"], width="stretch")
        with st.expander("All checks"):
            st.dataframe(dq, width="stretch")
    st.subheader("Recent ETL runs")
    st.dataframe(eda.etl_runs().head(40), width="stretch")
