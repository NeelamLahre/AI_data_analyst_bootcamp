

-- =====================================================================
-- TASK 1: RFM SCORES + CUSTOMER SEGMENTATION (Champions / Loyal / At Risk / Lost)
-- =====================================================================
WITH snapshot AS (
    SELECT MAX(date) AS snapshot_date
    FROM bm_sales
),
customer_rfm_raw AS (
    SELECT
        s.customer_id,
        DATEDIFF(sn.snapshot_date, MAX(s.date)) AS recency_days,
        COUNT(DISTINCT s.date)                  AS frequency,
        SUM(s.total_value)                      AS monetary
    FROM bm_sales s
    CROSS JOIN snapshot sn
    WHERE s.customer_id IS NOT NULL
    GROUP BY s.customer_id, sn.snapshot_date
),
customer_rfm_scores AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency  ASC)    AS f_score,
        NTILE(5) OVER (ORDER BY monetary   ASC)    AS m_score
    FROM customer_rfm_raw
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    CONCAT(r_score, f_score, m_score) AS rfm_code,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 4                  THEN 'Loyal'
        WHEN r_score <= 2 AND f_score >= 3                  THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2                  THEN 'Lost'
        ELSE 'Others'
    END AS customer_segment
FROM customer_rfm_scores
ORDER BY monetary DESC;



-- 1b) RFM SEGMENT SUMMARY  (exporting this result grid as RFM_segment_summary.csv)
WITH snapshot AS (
    SELECT MAX(date) AS snapshot_date FROM bm_sales
),
customer_rfm_raw AS (
    SELECT
        s.customer_id,
        DATEDIFF(sn.snapshot_date, MAX(s.date)) AS recency_days,
        COUNT(DISTINCT s.date)                  AS frequency,
        SUM(s.total_value)                      AS monetary
    FROM bm_sales s
    CROSS JOIN snapshot sn
    WHERE s.customer_id IS NOT NULL
    GROUP BY s.customer_id, sn.snapshot_date
),
customer_rfm_scores AS (
    SELECT
        customer_id, recency_days, frequency, monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency  ASC)    AS f_score,
        NTILE(5) OVER (ORDER BY monetary   ASC)    AS m_score
    FROM customer_rfm_raw
),
customer_segments AS (
    SELECT
        customer_id, recency_days, frequency, monetary,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 4                  THEN 'Loyal'
            WHEN r_score <= 2 AND f_score >= 3                  THEN 'At Risk'
            WHEN r_score <= 2 AND f_score <= 2                  THEN 'Lost'
            ELSE 'Others'
        END AS customer_segment
    FROM customer_rfm_scores
)
SELECT
    customer_segment,
    COUNT(*)                                                        AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2)              AS pct_of_customers,
    ROUND(AVG(recency_days), 1)                                     AS avg_recency_days,
    ROUND(AVG(frequency), 1)                                        AS avg_frequency,
    ROUND(AVG(monetary), 2)                                         AS avg_monetary,
    ROUND(SUM(monetary), 2)                                         AS total_revenue,
    ROUND(SUM(monetary) * 100.0 / SUM(SUM(monetary)) OVER (), 2)    AS pct_of_revenue
FROM customer_segments
GROUP BY customer_segment
ORDER BY total_revenue DESC;

-- =====================================================================
-- TASK 2: COHORT RETENTION TABLE BY CUSTOMER SIGNUP MONTH
-- =====================================================================
WITH customer_cohort AS (
    SELECT
        cust_id,
        DATE_FORMAT(registration_date, '%Y-%m-01') AS cohort_month
    FROM bm_customers
),
cohort_size AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT cust_id) AS cohort_customers
    FROM customer_cohort
    GROUP BY cohort_month
),
customer_activity AS (
    SELECT DISTINCT
        s.customer_id,
        DATE_FORMAT(s.date, '%Y-%m-01') AS activity_month
    FROM bm_sales s
    WHERE s.customer_id IS NOT NULL
),
cohort_activity AS (
    SELECT
        cc.cohort_month,
        TIMESTAMPDIFF(MONTH, cc.cohort_month, ca.activity_month) AS month_number,
        COUNT(DISTINCT cc.cust_id) AS retained_customers
    FROM customer_cohort cc
    JOIN customer_activity ca
        ON ca.customer_id = cc.cust_id
    WHERE TIMESTAMPDIFF(MONTH, cc.cohort_month, ca.activity_month) >= 0
    GROUP BY cc.cohort_month, month_number
)
SELECT
    DATE_FORMAT(ca.cohort_month, '%Y-%m') AS cohort_month,
    cs.cohort_customers,
    ca.month_number,
    ca.retained_customers,
    ROUND(ca.retained_customers * 100.0 / cs.cohort_customers, 2) AS retention_pct
FROM cohort_activity ca
JOIN cohort_size cs
    ON cs.cohort_month = ca.cohort_month
ORDER BY ca.cohort_month, ca.month_number;


-- =====================================================================
-- TASK 3: TOP PRODUCT PAIRS BOUGHT TOGETHER
-- =====================================================================
-- Notes:
--  - bm_sales has no order_id, so a "basket" is defined as all SKUs a
--    given customer bought on the same date (consistent with the
--    Frequency definition used in Task 1's RFM analysis).
--  - Guest checkouts (customer_id IS NULL) are excluded — baskets can't
--    be reliably reconstructed without a customer identifier.
--  - Self-join with sku_id_1 < sku_id_2 avoids counting (A,B) and (B,A)
--    as two different pairs, and avoids pairing a product with itself.
-- =====================================================================

WITH customer_orders AS (
    SELECT DISTINCT
        customer_id,
        date,
        sku_id
    FROM bm_sales
    WHERE customer_id IS NOT NULL
),
product_pairs AS (
    SELECT
        a.sku_id AS sku_id_1,
        b.sku_id AS sku_id_2,
        COUNT(*) AS times_bought_together
    FROM customer_orders a
    JOIN customer_orders b
        ON a.customer_id = b.customer_id
       AND a.date        = b.date
       AND a.sku_id       < b.sku_id
    GROUP BY a.sku_id, b.sku_id
)
SELECT
    p.sku_id_1,
    s1.sku_name AS product_1,
    p.sku_id_2,
    s2.sku_name AS product_2,
    p.times_bought_together
FROM product_pairs p
JOIN bm_skus s1 ON s1.sku_id = p.sku_id_1
JOIN bm_skus s2 ON s2.sku_id = p.sku_id_2
ORDER BY p.times_bought_together DESC
LIMIT 20;


-- =====================================================================
-- TASK 4: YEAR-OVER-YEAR REVENUE GROWTH
-- =====================================================================
-- Note: 2025 is a PARTIAL year (data ends 2025-10-31, missing Nov-Dec),
-- so its YoY growth % is not directly comparable to full-year figures.
-- Flagged explicitly via year_note below rather than hidden.
-- =====================================================================

WITH yearly_revenue AS (
    SELECT
        YEAR(date)        AS sales_year,
        SUM(total_value)  AS total_revenue
    FROM bm_sales
    GROUP BY YEAR(date)
),
yoy_growth AS (
    SELECT
        sales_year,
        total_revenue,
        LAG(total_revenue) OVER (ORDER BY sales_year) AS prev_year_revenue,
        ROUND(
            (total_revenue - LAG(total_revenue) OVER (ORDER BY sales_year))
            / LAG(total_revenue) OVER (ORDER BY sales_year) * 100
        , 2) AS yoy_growth_pct
    FROM yearly_revenue
)
SELECT
    sales_year,
    total_revenue,
    prev_year_revenue,
    yoy_growth_pct,
    CASE
        WHEN sales_year = 2025 THEN 'Partial year (Jan-Oct only)'
        ELSE 'Full year'
    END AS year_note
FROM yoy_growth
ORDER BY sales_year;




-- =====================================================================
-- TASK 5: RUNNING TOTAL REVENUE BY MONTH
-- =====================================================================
WITH monthly_revenue AS (
    SELECT
        DATE_FORMAT(date, '%Y-%m') AS sales_month,
        SUM(total_value)           AS monthly_revenue
    FROM bm_sales
    GROUP BY DATE_FORMAT(date, '%Y-%m')
)
SELECT
    sales_month,
    monthly_revenue,
    SUM(monthly_revenue) OVER (ORDER BY sales_month) AS running_total_revenue
FROM monthly_revenue
ORDER BY sales_month;
