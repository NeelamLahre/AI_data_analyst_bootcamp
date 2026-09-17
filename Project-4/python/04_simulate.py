# python/04_simulate.py
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

# ---- pull the real current position from the warehouse ----
base = pd.read_sql("""
    SELECT p.product_category,
           SUM(f.ape_sgd)          AS ape,
           AVG(f.nbp_margin_pct)   AS mean_margin,
           STDEV(f.nbp_margin_pct) AS sd_margin
    FROM fact_policy_new_business f
    JOIN dim_product p ON p.product_key = f.product_key
    WHERE f.dq_row_status = 'OK' AND p.product_category <> 'UNMAPPED'
    GROUP BY p.product_category
""", ENGINE).set_index("product_category")

print(base)

total_ape = base.ape.sum()
mix = base.ape / total_ape

# ---- the scenario lever ----
SHIFT = 0.10
new_mix = mix.copy()
new_mix["Savings & Wealth"] += SHIFT
new_mix["Protection"]        -= SHIFT * 0.6
new_mix["Health & IP"]       -= SHIFT * 0.4
new_mix = new_mix.clip(lower=0)
new_mix = new_mix / new_mix.sum()

# ---- Monte Carlo loop ----
results = np.zeros(ITERATIONS)
for i in range(ITERATIONS):
    drawn = rng.normal(base.mean_margin.values, base.sd_margin.values)
    drawn = np.clip(drawn, 0.01, 0.45)
    results[i] = float((new_mix.values * drawn).sum())

baseline_margin = float((mix.values * base.mean_margin.values).sum())
p05, p50, p95 = np.percentile(results, [5, 50, 95])

print(f"\nBaseline blended margin : {baseline_margin:.3%}")
print(f"Simulated p05/p50/p95   : {p05:.3%} / {p50:.3%} / {p95:.3%}")
print(f"Central impact          : {(p50 - baseline_margin) * 10_000:.0f} bps")
print(f"NBP at risk             : S${(baseline_margin - p50) * total_ape:,.0f}")

# ---- persist the run so Power BI can read it later ----
with ENGINE.begin() as conn:
    row = conn.execute(text("""
        INSERT INTO scenario_run (scenario_code, scenario_name, run_by, iterations, random_seed)
        OUTPUT INSERTED.run_id
        VALUES ('S-01', :name, :who, :iters, :seed)
    """), {"name": f"Product mix +{SHIFT:.0%} to Savings & Wealth",
           "who": "Neelam Lahre", "iters": ITERATIONS, "seed": SEED}).fetchone()
    run_id = row[0]

    conn.execute(text("""
        INSERT INTO scenario_result (run_id, metric_name, p05, p50, p95, baseline, delta_vs_base)
        VALUES (:r, 'blended_nbp_margin', :p05, :p50, :p95, :base, :delta)
    """), {"r": run_id, "p05": p05, "p50": p50, "p95": p95,
           "base": baseline_margin, "delta": p50 - baseline_margin})

print(f"\nSaved as run_id {run_id}")