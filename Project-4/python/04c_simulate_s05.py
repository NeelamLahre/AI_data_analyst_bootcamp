# python/04c_simulate_s05.py
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

# ---- pull real claims with their assessor's real approval limit ----
claims = pd.read_sql("""
    SELECT a.assessor_id, a.assessor_approval_limit_sgd, c.claim_amount_sgd
    FROM fact_claim c
    JOIN dim_assessor a ON a.assessor_key = c.assessor_key
    WHERE c.claim_amount_sgd IS NOT NULL AND a.assessor_approval_limit_sgd IS NOT NULL
""", ENGINE)

claims["ratio"] = claims.claim_amount_sgd / claims.assessor_approval_limit_sgd
claims["near_limit"] = claims.ratio.between(0.85, 1.0)

assessor_stats = claims.groupby("assessor_id").agg(
    n_claims=("claim_amount_sgd", "size"),
    near_limit_rate=("near_limit", "mean"),
).query("n_claims >= 20")   # same stability floor Stage 9's vw_assessor_alerts uses

peer_mean = assessor_stats.near_limit_rate.mean()
peer_sd = assessor_stats.near_limit_rate.std()
assessor_stats["z_score"] = (assessor_stats.near_limit_rate - peer_mean) / peer_sd

print(f"{len(assessor_stats)} assessors with >=20 claims")
print(f"Peer near-limit rate: mean {peer_mean:.2%}, sd {peer_sd:.2%}")
print("\nAlready-suspicious real assessors (z > 2 on this new metric):")
print(assessor_stats[assessor_stats.z_score > 2].sort_values("z_score", ascending=False))

# ---- Monte Carlo: inject a threshold-gaming pattern, test detection ----
FRAUD_MIX = 0.30          # 30% of the rogue assessor's future claims are gamed
DETECT_Z = 2.0            # alert threshold: 2 standard deviations above peers
HORIZON = 60              # claims tested before giving up
WINDOW = 40               # rolling window of recent claims a monitor would actually watch

limit_value = claims.assessor_approval_limit_sgd.median()
seed_near = round(peer_mean * WINDOW)
window_seed = [1] * seed_near + [0] * (WINDOW - seed_near)

detect_at = np.full(ITERATIONS, np.nan)
leak_before = np.zeros(ITERATIONS)
leak_prevented = np.zeros(ITERATIONS)

for i in range(ITERATIONS):
    window = list(window_seed)
    cum_gamed_by_claim = np.zeros(HORIZON)
    detected_k = None
    for k in range(HORIZON):
        gamed = rng.random() < FRAUD_MIX
        window.pop(0)
        if gamed:
            amt = rng.uniform(0.90, 0.99) * limit_value
            cum_gamed_by_claim[k] = amt
            window.append(1)
        else:
            window.append(0)
        rate = sum(window) / WINDOW
        z = (rate - peer_mean) / peer_sd
        if detected_k is None and z > DETECT_Z:
            detected_k = k
    if detected_k is not None:
        detect_at[i] = detected_k + 1
        leak_before[i] = cum_gamed_by_claim[:detected_k + 1].sum()
        leak_prevented[i] = cum_gamed_by_claim[detected_k + 1:].sum()

detection_rate = np.mean(~np.isnan(detect_at))
detected_mask = ~np.isnan(detect_at)

print(f"\n--- Scenario S-05: threshold-gaming injection ({FRAUD_MIX:.0%} of claims gamed) ---")
print(f"Detection rate within {HORIZON} claims : {detection_rate:.1%}")
print(f"Median claims to detect               : {np.nanmedian(detect_at):.0f}")
print(f"Median leakage before detection        : S${np.median(leak_before[detected_mask]):,.0f}")
print(f"Median leakage prevented by detection  : S${np.median(leak_prevented[detected_mask]):,.0f}")

p05, p50, p95 = np.percentile(detect_at[detected_mask], [5, 50, 95])

with ENGINE.begin() as conn:
    row = conn.execute(text("""
        INSERT INTO scenario_run (scenario_code, scenario_name, run_by, iterations, random_seed)
        OUTPUT INSERTED.run_id
        VALUES ('S-05', :name, :who, :iters, :seed)
    """), {"name": f"Threshold-gaming injection, {FRAUD_MIX:.0%} fraud mix, z>{DETECT_Z} alert",
           "who": "Neelam Lahre", "iters": ITERATIONS, "seed": SEED}).fetchone()
    run_id = row[0]

    conn.execute(text("""
        INSERT INTO scenario_result (run_id, metric_name, p05, p50, p95, baseline, delta_vs_base)
        VALUES (:r, 'claims_to_detect', :p05, :p50, :p95, :base, :delta)
    """), {"r": run_id, "p05": float(p05), "p50": float(p50), "p95": float(p95),
           "base": float(HORIZON), "delta": float(p50 - HORIZON)})

print(f"\nSaved as run_id {run_id}")