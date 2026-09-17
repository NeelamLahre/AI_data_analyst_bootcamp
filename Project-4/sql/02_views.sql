-- BO-1: New business margin by product and channel
CREATE OR ALTER VIEW vw_nbp_margin AS
SELECT d.year_month,
       p.product_category,
       c.channel_name,
       COUNT(*)                                                     AS policies,
       SUM(f.ape_sgd)                                                AS ape_sgd,
       SUM(f.nbp_sgd)                                                 AS nbp_sgd,
       SUM(f.nbp_sgd) / NULLIF(SUM(f.ape_sgd), 0)                     AS blended_margin,
       SUM(CASE WHEN p.is_low_margin = 1 THEN f.ape_sgd ELSE 0 END)
           / NULLIF(SUM(f.ape_sgd), 0)                                 AS low_margin_mix
FROM fact_policy_new_business f
JOIN dim_date d    ON d.date_key = f.start_date_key
JOIN dim_product p ON p.product_key = f.product_key
JOIN dim_channel c ON c.channel_key = f.channel_key
-- product_category <> 'UNMAPPED' added after Stage 10's S-01 simulation surfaced 173 seeded
-- junk category rows (LEGACY-XX, MISC, ...) being silently treated as a real business segment
WHERE f.dq_row_status = 'OK' AND p.product_category <> 'UNMAPPED'
GROUP BY d.year_month, p.product_category, c.channel_name;
GO

-- BO-2: does claim delay drive severity?
CREATE OR ALTER VIEW vw_health_gap AS
WITH banded AS (
    SELECT
        CASE WHEN f.care_delay_days = 0   THEN '0 - no delay'
             WHEN f.care_delay_days <= 30  THEN '1 - up to 1 month'
             WHEN f.care_delay_days <= 90  THEN '2 - 1 to 3 months'
             WHEN f.care_delay_days <= 180 THEN '3 - 3 to 6 months'
             ELSE                          '4 - over 6 months'
        END AS delay_band,
        cl.claim_key, cl.claim_amount_sgd, f.ape_sgd
    FROM fact_policy_new_business f
    LEFT JOIN fact_claim cl ON cl.policy_key = f.policy_key
    WHERE f.dq_row_status = 'OK'
),
with_p90 AS (
    SELECT *,
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY claim_amount_sgd)
            OVER (PARTITION BY delay_band) AS p90_severity
    FROM banded
)
SELECT delay_band,
       COUNT(claim_key)                               AS claims,
       AVG(claim_amount_sgd)                           AS avg_severity,
       MAX(p90_severity)                                AS p90_severity,
       SUM(claim_amount_sgd) / NULLIF(SUM(ape_sgd), 0)   AS loss_ratio
FROM with_p90
GROUP BY delay_band;
GO

-- BO-5: fraud and conduct alerts
CREATE OR ALTER VIEW vw_assessor_alerts AS
WITH per_assessor AS (
    SELECT a.assessor_id,
           COUNT(*)                                                    AS decisions,
           AVG(c.claim_amount_sgd)                                     AS avg_amount,
           SUM(CASE WHEN c.approval_above_limit = 1 THEN 1 ELSE 0 END)  AS above_limit,
           SUM(CASE WHEN c.sod_breach = 1 THEN 1 ELSE 0 END)             AS sod_breaches,
           AVG(c.fraud_risk_score)                                       AS avg_fraud_score
    FROM fact_claim c
    JOIN dim_assessor a ON a.assessor_key = c.assessor_key
    GROUP BY a.assessor_id
)
SELECT *,
       CAST(above_limit AS NUMERIC) / NULLIF(decisions, 0)               AS above_limit_rate,
       (avg_fraud_score - AVG(avg_fraud_score) OVER ())
           / NULLIF(STDEV(avg_fraud_score) OVER (), 0)                    AS z_score
FROM per_assessor
WHERE decisions >= 20;
GO

-- Verification queries (not part of the schema -- run these manually to spot-check):
-- SELECT TOP 10 * FROM vw_nbp_margin ORDER BY year_month;
-- SELECT * FROM vw_health_gap ORDER BY delay_band;
-- SELECT TOP 10 * FROM vw_assessor_alerts ORDER BY z_score DESC;