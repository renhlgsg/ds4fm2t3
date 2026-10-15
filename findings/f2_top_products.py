"""KEY FINDING 2 - Top-selling products & categories.   Run: python -m findings.f2_top_products"""
from analysis import eda
from findings._common import BLUE, ORANGE, TAB, record, save_fig
import matplotlib.pyplot as plt

cats = eda.top_categories(15)
cats_all = eda.top_categories(1000)
prods_rev = eda.top_products(10, "revenue")
prods_units = eda.top_products(10, "units")
sellers = eda.seller_concentration()
cats.to_csv(TAB / "f2_top_categories.csv", index=False)
prods_rev.to_csv(TAB / "f2_top_products_by_revenue.csv", index=False)
prods_units.to_csv(TAB / "f2_top_products_by_units.csv", index=False)

fig, ax = plt.subplots(figsize=(9, 5))
c10 = cats.head(10).iloc[::-1]
ax.barh(c10.category, c10.revenue / 1e3, color=BLUE)
for y, (v, s) in enumerate(zip(c10.revenue / 1e3, c10.revenue_share_pct)):
    ax.text(v, y, f"  {s:.1f}%", va="center", fontsize=9)
ax.set_xlabel("Revenue (BRL thousand)  -  label = share of total")
ax.set_title("Top 10 product categories by revenue")
save_fig(fig, "f2_top_categories")

n_top10_sellers = int(len(sellers) * 0.10)
record("f2", {"top_category": cats.iloc[0].category, "top_category_share": float(cats.iloc[0].revenue_share_pct),
              "top5_category_share": float(cats.iloc[4].cum_share_pct),
              "n_categories": int(len(cats_all)),
              "top_product_id": prods_rev.iloc[0].product_id, "top_product_revenue": float(prods_rev.iloc[0].revenue),
              "top_product_by_units": prods_units.iloc[0].product_id, "top_product_units": int(prods_units.iloc[0].units),
              "top10pct_sellers_revenue_share": float(sellers.iloc[n_top10_sellers - 1].cum_share_pct),
              "n_sellers_with_sales": int(len(sellers))})
print(cats.head(5)[["category", "revenue", "revenue_share_pct"]])
print(prods_rev.head(5))
print(f"Top 10% of sellers ({n_top10_sellers}) generate {sellers.iloc[n_top10_sellers-1].cum_share_pct}% of revenue")
