"""KEY FINDING 1 - Monthly sales trend.   Run: python -m findings.f1_monthly_sales_trend"""
from analysis import eda
from findings._common import BLUE, ORANGE, TAB, record, save_fig
import matplotlib.pyplot as plt

m = eda.monthly_sales()
m.to_csv(TAB / "f1_monthly_sales.csv", index=False)

# Edge months hold only a handful of orders (data starts Sep-2016, one stray order in Sep-2018).
full = m[(m.orders >= 100)].copy()
first, last = full.iloc[0], full.iloc[-1]
peak = full.loc[full.revenue.idxmax()]
y17 = m[m.year_month.between("2017-01", "2017-08")].revenue.sum()
y18 = m[m.year_month.between("2018-01", "2018-08")].revenue.sum()
yoy = (y18 / y17 - 1) * 100

fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(full.year_month, full.revenue / 1e3, color=BLUE, label="Monthly revenue")
ax.plot(full.year_month, full.revenue_3m_avg / 1e3, color=ORANGE, lw=2, label="3-month average")
ax.set_ylabel("Revenue (BRL thousand)")
ax.set_title("Monthly revenue (valid orders, months with >=100 orders)")
ax.tick_params(axis="x", rotation=60)
ax.legend()
save_fig(fig, "f1_monthly_revenue")

record("f1", {"first_full_month": first.year_month, "last_full_month": last.year_month,
              "peak_month": peak.year_month, "peak_revenue": float(peak.revenue), "peak_orders": int(peak.orders),
              "ytd_2017_jan_aug": float(y17), "ytd_2018_jan_aug": float(y18), "ytd_yoy_pct": round(float(yoy), 1),
              "partial_months": m[m.orders < 100].year_month.tolist(),
              "aov_peak": float(peak.avg_order_value)})
print(f"Peak month {peak.year_month}: revenue {peak.revenue:,.0f} from {peak.orders:,} orders")
print(f"Jan-Aug revenue 2017 {y17:,.0f} -> 2018 {y18:,.0f} ({yoy:+.1f}%)")
print("Partial/edge months excluded from trend:", m[m.orders < 100].year_month.tolist())
