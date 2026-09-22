#Starting the file with imports

import pandas as pd
import matplotlib
matplotlib.use("Agg")   # so it saves files instead of popping up windows
import matplotlib.pyplot as plt
import seaborn as sns

from config import (
    SUBSCRIBERS_CSV, DATASET_XLSX, OUTPUT_DIR, CHART_DIR, DOCS_DIR,
    LEAKAGE_COLUMNS, TENURE_BINS, TENURE_LABELS, ARPU_BINS, ARPU_LABELS,
)

sns.set_theme(style="whitegrid")
CHART_DIR.mkdir(parents=True, exist_ok=True)

#Loading the main subscriber table

subs = pd.read_csv(SUBSCRIBERS_CSV, parse_dates=["join_date", "churn_date"])
print(subs.shape)
print(subs.dtypes)


#Load the supporting sheets from the workbook

xl = pd.ExcelFile(DATASET_XLSX)
service_requests = pd.read_excel(xl, "service_requests", parse_dates=["raised_date", "resolved_date"])
network_sites   = pd.read_excel(xl, "network_sites")
circle_kpi      = pd.read_excel(xl, "circle_monthly_kpi", parse_dates=["month_end"])
circle_targets  = pd.read_excel(xl, "circle_targets")
offer_catalogue = pd.read_excel(xl, "offer_catalogue", parse_dates=["valid_from", "valid_to"])

#Checking the churn base rates

churn30 = subs["churn_flag_30d"].mean()
churn90 = subs["churn_flag_90d"].mean()
print(f"30d churn rate: {churn30:.2%}, 90d churn rate: {churn90:.2%}")

#Confirm the leakage columns exist and note their values are only non-null for churned subscribers

print(subs[LEAKAGE_COLUMNS].isna().mean())

#Finding the most recent month in the KPI table

latest_month = circle_kpi["month_end"].max()
latest_kpi = circle_kpi[circle_kpi["month_end"] == latest_month].copy()

#Bringing in circle-level targets and ownership

latest_kpi = latest_kpi.merge(
    circle_targets[["circle", "churn_ceiling_fy27_pct", "review_status",
                     "circle_owner", "retention_budget_lakh", "budget_utilised_lakh"]],
    on="circle", how="left",
)
latest_kpi["over_ceiling"] = latest_kpi["monthly_churn_pct"] > latest_kpi["churn_ceiling_fy27_pct"]
latest_kpi = latest_kpi.sort_values("monthly_churn_pct", ascending=False)


#Checking over_ceiling before you rely on it

escalated = latest_kpi[latest_kpi["review_status"] == "Escalated"]
print(escalated[["circle", "monthly_churn_pct", "review_status"]])

#Saving the ranked table for your report
latest_kpi.to_csv(OUTPUT_DIR / "day1_circle_kpi_latest_month.csv", index=False)

#Chart 1 — churn % by circle

fig, ax = plt.subplots(figsize=(9, 5))
sns.barplot(data=latest_kpi, x="monthly_churn_pct", y="circle",
            hue="over_ceiling", dodge=False, ax=ax)
ax.set_title(f"Monthly churn % by circle - {latest_month.date()}")
fig.savefig(CHART_DIR / "01_circle_churn_latest_month.png", dpi=150, bbox_inches="tight")
plt.close(fig)

#Chart 2 — top circles by port-out volume (second, independent view of regional pressure)

port_out = latest_kpi.sort_values("port_out_requests", ascending=False).head(10)
fig, ax = plt.subplots(figsize=(9, 5))
sns.barplot(data=port_out, x="port_out_requests", y="circle", ax=ax)
ax.set_title(f"Top 10 circles by port-out requests - {latest_month.date()}")
fig.savefig(CHART_DIR / "02_circle_port_out_top10.png", dpi=150, bbox_inches="tight")
plt.close(fig)

#Building a national, base-weighted monthly churn trend

national_trend = circle_kpi.groupby("month_end").apply(
    lambda g: pd.Series({
        "closing_base": g["closing_base"].sum(),
        "churned_subscribers": g["churned_subscribers"].sum(),
        "weighted_churn_pct": 100 * g["churned_subscribers"].sum() / g["closing_base"].sum(),
    })
).reset_index()
national_trend.to_csv(OUTPUT_DIR / "day1_national_churn_trend.csv", index=False)

#Picking worst circles from Step 4 and overlay them on the national line

top_circles = latest_kpi.head(4)["circle"].tolist()
trend_top = circle_kpi[circle_kpi["circle"].isin(top_circles)]

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(national_trend["month_end"], national_trend["weighted_churn_pct"],
        label="National", color="black", linewidth=2)
for c in top_circles:
    sub = trend_top[trend_top["circle"] == c].sort_values("month_end")
    ax.plot(sub["month_end"], sub["monthly_churn_pct"], label=c, alpha=0.8)
ax.set_title("Monthly churn % over time")
ax.legend()
fig.savefig(CHART_DIR / "03_churn_trend_over_time.png", dpi=150, bbox_inches="tight")
plt.close(fig)

#Now the tenure/cliff analysis. Bucket tenure and compute churn rate per bucket

subs["tenure_bucket"] = pd.cut(subs["tenure_months"], bins=TENURE_BINS,
                                 labels=TENURE_LABELS, right=False)
tenure_churn = subs.groupby("tenure_bucket", observed=True).agg(
    subscribers=("subscriber_id", "count"),
    churn90_rate=("churn_flag_90d", "mean"),
).reset_index()
tenure_churn.to_csv(OUTPUT_DIR / "day1_tenure_churn.csv", index=False)
print(tenure_churn)

#Chart it and note whichever bucket has the highest rate

fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(data=tenure_churn, x="tenure_bucket", y="churn90_rate", ax=ax)
ax.set_title("Churn rate by tenure bucket")
fig.savefig(CHART_DIR / "04_tenure_churn_curve.png", dpi=150, bbox_inches="tight")
plt.close(fig)

#Unresolved complaints vs churn

complaint_churn = subs.groupby("unresolved_complaints").agg(
    subscribers=("subscriber_id", "count"),
    churn90_rate=("churn_flag_90d", "mean"),
).reset_index()
complaint_churn.to_csv(OUTPUT_DIR / "day1_unresolved_complaints_vs_churn.csv", index=False)

fig, ax = plt.subplots(figsize=(7, 5))
sns.barplot(data=complaint_churn, x="unresolved_complaints", y="churn90_rate", ax=ax)
ax.set_title("Unresolved complaints vs churn")
fig.savefig(CHART_DIR / "05_unresolved_complaints_vs_churn.png", dpi=150, bbox_inches="tight")
plt.close(fig)

#Bring in service_requests for an SLA-breach view

sr_agg = service_requests.groupby("subscriber_id").agg(
    total_sr=("sr_id", "count"),
    sla_breaches=("sla_breach_flag", "sum"),
).reset_index()
subs_sr = subs.merge(sr_agg, on="subscriber_id", how="left")
subs_sr[["total_sr", "sla_breaches"]] = subs_sr[["total_sr", "sla_breaches"]].fillna(0)

sla_churn = subs_sr.assign(had_breach=lambda d: d["sla_breaches"] > 0) \
                    .groupby("had_breach")["churn_flag_90d"].mean()
print(sla_churn)

#ARPU band vs churn

subs["arpu_band"] = pd.cut(subs["arpu_last_month_inr"], bins=ARPU_BINS, labels=ARPU_LABELS)
arpu_churn = subs.groupby("arpu_band", observed=True)["churn_flag_90d"].mean().reset_index()
arpu_churn.to_csv(OUTPUT_DIR / "day1_arpu_band_vs_churn.csv", index=False)

fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(data=arpu_churn, x="arpu_band", y="churn_flag_90d", ax=ax)
ax.set_title("ARPU band vs churn")
fig.savefig(CHART_DIR / "06_arpu_band_vs_churn.png", dpi=150, bbox_inches="tight")
plt.close(fig)

#Network quality (SINR) vs churn
subs["sinr_band"] = pd.qcut(subs["avg_sinr_db"], q=5, duplicates="drop")
network_churn = subs.groupby("sinr_band", observed=True)["churn_flag_90d"].mean().reset_index()

fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(data=network_churn, x="sinr_band", y="churn_flag_90d", ax=ax)
ax.set_title("Network quality (SINR quintile) vs churn")
plt.xticks(rotation=30, ha="right")
fig.savefig(CHART_DIR / "07_network_sinr_vs_churn.png", dpi=150, bbox_inches="tight")
plt.close(fig)


#5G adoption vs churn

g5_churn = subs.groupby("is_5g_active")["churn_flag_90d"].agg(["mean", "count"])
print(g5_churn)

#Overall correlation ranking
numeric_cols = [
    "tenure_months", "arpu_last_month_inr", "recharge_count_6m", "avg_recharge_gap_days",
    "days_since_last_recharge", "payment_failures_6m", "data_gb_last_month", "avg_sinr_db",
    "drop_call_rate_pct", "site_congestion_score", "complaints_6m", "unresolved_complaints",
    "outgoing_to_competitor_pct", "app_logins_30d", "churn_flag_90d",
]
corr = subs[numeric_cols].corr()["churn_flag_90d"].drop("churn_flag_90d").sort_values()

fig, ax = plt.subplots(figsize=(7, 7))
sns.barplot(x=corr.values, y=corr.index, ax=ax)
ax.set_title("Correlation with 90-day churn")
fig.savefig(CHART_DIR / "08_correlation_with_churn.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(corr)
