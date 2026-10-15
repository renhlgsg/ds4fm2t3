"""KEY FINDING 4 - Delivery performance drives customer satisfaction.   Run: python -m findings.f4_delivery_and_reviews"""
from analysis import eda
from findings._common import BLUE, GREEN, ORANGE, RED, TAB, record, save_fig
import matplotlib.pyplot as plt

lateness = eda.review_vs_lateness()
bucket = eda.review_by_delay_bucket()
state = eda.delivery_by_state()
lateness.to_csv(TAB / "f4_review_vs_lateness.csv", index=False)
bucket.to_csv(TAB / "f4_review_by_delay_bucket.csv", index=False)
state.to_csv(TAB / "f4_delivery_by_state.csv", index=False)

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].bar(bucket.delivery_vs_promise.str[3:], bucket.avg_score, color=[GREEN, GREEN, ORANGE, RED])
axes[0].set_ylim(1, 5); axes[0].set_ylabel("Average review score"); axes[0].set_title("Review score vs. delivery against promise")
axes[0].tick_params(axis="x", rotation=20)
big = state[state.delivered_orders >= 300].sort_values("avg_delivery_days")
axes[1].barh(big.state, big.avg_delivery_days, color=BLUE)
axes[1].set_title("Avg delivery days by customer state (>=300 orders)"); axes[1].set_xlabel("days")
save_fig(fig, "f4_delivery_reviews")

late = lateness.set_index("delivery")
overall_late = float((lateness.reviews[lateness.delivery == "Late"].sum() / lateness.reviews.sum()) * 100)
record("f4", {"avg_score_on_time": float(late.loc["On time", "avg_score"]), "avg_score_late": float(late.loc["Late", "avg_score"]),
              "negative_pct_on_time": float(late.loc["On time", "negative_pct"]),
              "negative_pct_late": float(late.loc["Late", "negative_pct"]),
              "late_share_of_reviews_pct": round(overall_late, 1),
              "slowest_big_state": big.sort_values("avg_delivery_days").iloc[-1].state,
              "slowest_big_state_days": float(big.sort_values("avg_delivery_days").iloc[-1].avg_delivery_days),
              "fastest_state": state.sort_values("avg_delivery_days").iloc[0].state,
              "fastest_state_days": float(state.sort_values("avg_delivery_days").iloc[0].avg_delivery_days),
              "score_8plus_days_late": float(bucket.iloc[3].avg_score)})
print(lateness); print(bucket); print(state.head(5))
