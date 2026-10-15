"""KEY FINDING 5 - Payment behaviour and geographic concentration.   Run: python -m findings.f5_payments_and_geography"""
from analysis import eda
from findings._common import BLUE, ORANGE, TAB, record, save_fig
import matplotlib.pyplot as plt

pay = eda.payment_mix()
geo = eda.revenue_by_state()
pay.to_csv(TAB / "f5_payment_mix.csv", index=False)
geo.to_csv(TAB / "f5_revenue_by_state.csv", index=False)
region = geo.groupby("region", as_index=False).agg(revenue=("revenue", "sum"), orders=("orders", "sum"))
region["share_pct"] = (region.revenue / region.revenue.sum() * 100).round(1)

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
p = pay[pay.value_share_pct > 0.5]
axes[0].pie(p.value, labels=p.payment_type, autopct="%1.1f%%", colors=[BLUE, ORANGE, "#8c8c8c", "#5aa9e6"], startangle=90)
axes[0].set_title("Payment value by type")
g10 = geo.head(10).iloc[::-1]
axes[1].barh(g10.state, g10.revenue / 1e3, color=BLUE); axes[1].set_title("Top 10 customer states by revenue (BRL k)")
save_fig(fig, "f5_payments_geography")

se = region.set_index("region")
record("f5", {"credit_card_value_pct": float(pay.iloc[0].value_share_pct), "credit_card_avg_installments": float(pay.iloc[0].avg_installments),
              "boleto_value_pct": float(pay[pay.payment_type == "Boleto"].value_share_pct.iloc[0]),
              "top_state": geo.iloc[0].state, "top_state_pct": float(geo.iloc[0].revenue_share_pct),
              "top3_states_pct": round(float(geo.head(3).revenue_share_pct.sum()), 1),
              "southeast_pct": float(se.loc["Southeast", "share_pct"])})
print(pay); print(region)
