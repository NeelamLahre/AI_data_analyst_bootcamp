# Certified Metric Definitions

- **Churn (90-day)**: `subscribers.churn_flag_90d = 1`
- **Churn (30-day)**: `subscribers.churn_flag_30d = 1`
- **Churn score**: `scored_subscribers.churn_score` - a RANKING score (higher = riskier), NOT a
  calibrated probability. Never state it as "X% chance of churning."
- **CLV (Customer Lifetime Value)**: `scored_subscribers.clv_predicted` - a projected 12-month
  value estimate in INR.
- **Uplift segment**: `scored_subscribers.segment` - one of "Persuadable" (target with offers),
  "Sure thing / Lost cause" (offer won't change outcome), "Sleeping dog (do not disturb)"
  (offer increases churn risk - exclude from campaigns).
- **ARPU (subscriber-level)**: `subscribers.arpu_last_month_inr`
- **ARPU (circle-level)**: `circle_monthly_kpi.arpu_inr`
- **Net add**: `circle_monthly_kpi.net_adds`
- **Active subscriber**: any row present in `subscribers` (the table holds active and recently
  churned subscribers only, not a full historical archive)
- **Unresolved complaints**: `subscribers.unresolved_complaints` (count, last 6 months)
- **SLA breach**: `service_requests.sla_breach_flag = 1`