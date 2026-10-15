"""KEY FINDING 3 - Customer segmentation by purchase behaviour (RFM-style).   Run: python -m findings.f3_customer_segmentation"""
from analysis import eda
from findings._common import BLUE, GREY, ORANGE, TAB, record, save_fig
import matplotlib.pyplot as plt

rfm = eda.customer_rfm()
seg = eda.segment_summary(rfm)
seg.to_csv(TAB / "f3_customer_segments.csv", index=False)
rate = eda.repeat_rate(rfm)

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
s = seg.sort_values("customer_share_pct")
axes[0].barh(s.segment, s.customer_share_pct, color=GREY); axes[0].set_title("Share of customers (%)")
s = seg.sort_values("revenue_share_pct")
axes[1].barh(s.segment, s.revenue_share_pct, color=BLUE); axes[1].set_title("Share of lifetime revenue (%)")
axes[1].set_yticklabels([])
save_fig(fig, "f3_segments")

top = seg.iloc[0]
repeat_rev = seg[seg.segment.isin(["Loyal repeat", "At-risk repeat"])].revenue_share_pct.sum()
record("f3", {"customers_analysed": int(len(rfm)), "repeat_rate_pct": rate,
              "avg_clv": round(float(rfm.monetary.mean()), 2),
              "avg_clv_repeat": round(float(rfm[rfm.frequency >= 2].monetary.mean()), 2),
              "avg_clv_one_time": round(float(rfm[rfm.frequency == 1].monetary.mean()), 2),
              "top_segment": top.segment, "top_segment_customer_pct": float(top.customer_share_pct),
              "top_segment_revenue_pct": float(top.revenue_share_pct), "repeat_revenue_pct": float(repeat_rev),
              "segments": seg[["segment", "customers", "customer_share_pct", "revenue_share_pct", "avg_clv"]].to_dict("records")})
print(seg)
print(f"Repeat-purchase rate: {rate}%")
