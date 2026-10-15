"""Generates notebooks/01_eda.ipynb (so the notebook source is reviewable as plain Python).
Run:  python notebooks/build_notebook.py   then   jupyter nbconvert --to notebook --execute --inplace notebooks/01_eda.ipynb
"""
import nbformat as nbf
from pathlib import Path

nb = nbf.v4.new_notebook()
C = lambda s: nbf.v4.new_code_cell(s.strip("\n"))
M = lambda s: nbf.v4.new_markdown_cell(s.strip("\n"))

nb.cells = [
M("""# Olist e-commerce - exploratory data analysis
Source: DuckDB star schema `FDL_DATA` (built by `pipeline/run_all.py`). All queries live in `analysis/eda.py`
so the notebook, the Streamlit app and the slide findings share one implementation.
*Valid orders = status not in (canceled, unavailable). Revenue = sum of item price; GMV = price + freight.*"""),
C("""
import sys; sys.path.insert(0, '..')
import pandas as pd, plotly.express as px
from analysis import eda
pd.options.display.float_format = '{:,.2f}'.format
pd.options.display.width = 160
"""),
M("## 0. Data model sanity check - row counts of the star schema"),
C("""
eda.query('''SELECT table_name, estimated_size AS rows FROM duckdb_tables()
             WHERE schema_name = 'FDL_DATA' ORDER BY table_name''')
"""),
M("## 1. Headline KPIs"),
C("eda.kpis().to_frame('value')"),
M("## 2. Monthly sales trends\nMonths with fewer than 100 orders (Sep-2016, Dec-2016, Sep-2018) are data-edge artefacts and are excluded from trend statements."),
C("""
m = eda.monthly_sales()
m
"""),
C("""
full = m[m.orders >= 100]
fig = px.bar(full, x='year_month', y='revenue', title='Monthly revenue')
fig.add_scatter(x=full.year_month, y=full.revenue_3m_avg, name='3-month average')
fig.show()
"""),
C("""
y17 = m[m.year_month.between('2017-01','2017-08')].revenue.sum(); y18 = m[m.year_month.between('2018-01','2018-08')].revenue.sum()
print(f'Jan-Aug revenue: 2017 = {y17:,.0f}  2018 = {y18:,.0f}  growth = {(y18/y17-1)*100:+.1f}%')
print('Peak month:', full.loc[full.revenue.idxmax(), 'year_month'])
"""),
M("## 3. Top-selling products and categories"),
C("eda.top_categories(10)"),
C("eda.top_products(10, 'revenue')"),
C("eda.top_products(10, 'units')"),
C("""
s = eda.seller_concentration()
print(f"Top 10% of sellers ({int(len(s)*.1)}) = {s.iloc[int(len(s)*.1)-1].cum_share_pct}% of revenue")
"""),
M("## 4. Customer segmentation by purchase behaviour\nOlist `customer_id` is per order; the real customer is `customer_unique_id` (= one row of `D_CUSTOMER`)."),
C("""
rfm = eda.customer_rfm()
print('Repeat-purchase rate (%):', eda.repeat_rate(rfm))
eda.segment_summary(rfm)
"""),
C("rfm.groupby('frequency').agg(customers=('customer_key','count'), avg_clv=('monetary','mean')).round(2)"),
C("""
px.scatter(rfm.sample(5000, random_state=1), x='recency_days', y='monetary', color='segment',
           log_y=True, opacity=.5, title='Recency vs lifetime value (5,000 sampled customers)').show()
"""),
M("## 5. Delivery performance vs. customer reviews"),
C("eda.review_vs_lateness()"),
C("eda.review_by_delay_bucket()"),
C("eda.delivery_by_state().head(10)"),
M("## 6. Payments and geography"),
C("eda.payment_mix()"),
C("eda.revenue_by_state().head(10)"),
M("""## 7. Takeaways
* Revenue grew strongly through 2017 and plateaued between BRL 0.84M and 0.99M/month in 2018 (see section 2).
* Demand is broad across categories (no category > 10% of revenue) but concentrated among sellers (top 10% ~ two thirds of revenue).
* ~97% of customers buy once - retention, not acquisition mix, is the largest commercial lever.
* Late deliveries cut the average review score roughly in half; remote Northern/Northeastern states wait 2-3x longer than Sao Paulo."""),
]
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
out = Path(__file__).parent / "01_eda.ipynb"
nbf.write(nb, out)
print("wrote", out)
