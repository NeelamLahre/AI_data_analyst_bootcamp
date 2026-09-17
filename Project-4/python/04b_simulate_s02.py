# python/04b_simulate_s02.py
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

ENGINE = create_engine(
    "mssql+pyodbc://localhost\\SQLEXPRESS/prudential_dw"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
)

SEED, ITERATIONS = 42, 10_000
rng = np.random.default_rng(SEED)

riders = pd.read_sql("""
    SELECT lapse_flag, copay_pct, rider_premium_after_sgd
    FROM fact_policy_new_business
    WHERE dq_row_status = 'OK' AND rider_attached_flag = 1
      AND copay_pct IS NOT NULL AND lapse_flag IS NOT NULL
""", ENGINE)
riders["lapse"] = riders.lapse_flag.astype(float)

print("Lapse rate by exact copay_pct value:")
print(riders.groupby("copay_pct").agg(n=("lapse", "size"), lapse_rate=("lapse", "mean")))

# ---- reframe around what the data can actually support ----
# Only 8 distinct copay values exist, heavily skewed to 0 -- a continuous linear
# fit (tried first, discarded) was driven by a thin, noisy tail and produced a
# result backwards from the business hypothesis. Instead: compare the currently
# no-copay book against the REAL 10%-copay cohort (already repriced under the
# MOH mandate) and bootstrap that cohort directly for honest uncertainty bounds.
no_copay = riders[riders.copay_pct == 0]
reference_tier = riders[riders.copay_pct == 10.0]

baseline_lapse = no_copay.lapse.mean()
baseline_premium = no_copay.rider_premium_after_sgd.sum()
n_ref = len(reference_tier)
print(f"\nBaseline (no copay): {len(no_copay):,} policies, lapse {baseline_lapse:.2%}")
print(f"Reference (10% copay, already repriced): {n_ref:,} policies, lapse {reference_tier.lapse.mean():.2%}")

# ---- bootstrap the reference tier's lapse rate 10,000 times ----
results_lapse = np.zeros(ITERATIONS)
for i in range(ITERATIONS):
    sample = reference_tier.lapse.values[rng.integers(0, n_ref, n_ref)]
    results_lapse[i] = sample.mean()

p05, p50, p95 = np.percentile(results_lapse, [5, 50, 95])
baseline_premium_kept = baseline_premium * (1 - baseline_lapse)
projected_premium_kept = baseline_premium * (1 - p50)

print(f"\nScenario: move the no-copay book to a 10% copay tier (matching the real repriced cohort)")
print(f"Projected lapse p05/p50/p95   : {p05:.2%} / {p50:.2%} / {p95:.2%}")
print(f"Lapse change vs baseline (p50): {(p50 - baseline_lapse) * 10_000:.0f} bps")
print(f"Rider premium impact (p50)    : S${projected_premium_kept - baseline_premium_kept:,.0f}")
print("\nCaveat: this compares two real cohorts, not a controlled experiment -- the 10%-copay")
print("group may differ from the no-copay group in tenure or plan mix too. Treat as a")
print("directional estimate, not a precise causal forecast (guide's own risk R-3).")

with ENGINE.begin() as conn:
    row = conn.execute(text("""
        INSERT INTO scenario_run (scenario_code, scenario_name, run_by, iterations, random_seed)
        OUTPUT INSERTED.run_id
        VALUES ('S-02', :name, :who, :iters, :seed)
    """), {"name": "IP rider: move no-copay book to 10% copay tier",
           "who": "Neelam Lahre", "iters": ITERATIONS, "seed": SEED}).fetchone()
    run_id = row[0]

    conn.execute(text("""
        INSERT INTO scenario_result (run_id, metric_name, p05, p50, p95, baseline, delta_vs_base)
        VALUES (:r, 'rider_lapse_rate', :p05, :p50, :p95, :base, :delta)
    """), {"r": run_id, "p05": p05, "p50": p50, "p95": p95,
           "base": baseline_lapse, "delta": p50 - baseline_lapse})

print(f"\nSaved as run_id {run_id}")