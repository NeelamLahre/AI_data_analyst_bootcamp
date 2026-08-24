
USE bootcamp_sales;


-- Task 1: Find revenue by region and store type
SELECT
    st.city,
    st.store_type,
    SUM(s.total_value) AS total_revenue
FROM bm_sales s
INNER JOIN bm_stores st
    ON s.store_id = st.store_id
GROUP BY
    st.city,
    st.store_type
ORDER BY total_revenue DESC;

-- Task 2: Find top 5 product categories by revenue
-- ==========================================================
-- 2. Top 5 product categories by revenue
-- ==========================================================

SELECT
    sk.category,
    SUM(s.total_value) AS total_revenue
FROM bm_sales s
INNER JOIN bm_skus sk
    ON s.sku_id = sk.sku_id
GROUP BY sk.category
ORDER BY total_revenue DESC
LIMIT 5;

-- Task 3: Group customers into High, Medium, Low spend tiers
SELECT
    customer_id,
    total_spend,
    CASE
        WHEN total_spend >= 1000 THEN 'High'
        WHEN total_spend >= 500 THEN 'Medium'
        ELSE 'Low'
    END AS spend_tier
FROM (
    SELECT
        customer_id,
        SUM(total_value) AS total_spend
    FROM bm_sales
    GROUP BY customer_id
) AS customer_spending
ORDER BY total_spend DESC;

-- Task 4: Check if promotions increased sales
SELECT
    CASE
        WHEN discount_pct > 0 THEN 'Discounted / Promotional'
        ELSE 'No Discount'
    END AS promotion_status,
    COUNT(*) AS number_of_sales,
    SUM(quantity) AS units_sold,
    SUM(total_value) AS total_revenue,
    AVG(total_value) AS average_sale_value
FROM bm_sales
GROUP BY
    CASE
        WHEN discount_pct > 0 THEN 'Discounted / Promotional'
        ELSE 'No Discount'
    END
ORDER BY total_revenue DESC;

-- Task 5: Find customers who spend above average
SELECT
    customer_id,
    total_spend
FROM (
    SELECT
        customer_id,
        SUM(total_value) AS total_spend
    FROM bm_sales
    GROUP BY customer_id
) AS customer_spending
WHERE total_spend > (
    SELECT AVG(total_spend)
    FROM (
        SELECT
            customer_id,
            SUM(total_value) AS total_spend
        FROM bm_sales
        GROUP BY customer_id
    ) AS customer_totals
)
ORDER BY total_spend DESC;

-- ==========================================================
-- 6. Products with falling sales month over month
-- ==========================================================

WITH monthly_sales AS (
    SELECT
        sku_id,
        DATE_FORMAT(date, '%Y-%m') AS sales_month,
        SUM(total_value) AS monthly_revenue
    FROM bm_sales
    GROUP BY
        sku_id,
        DATE_FORMAT(date, '%Y-%m')
),

sales_comparison AS (
    SELECT
        sku_id,
        sales_month,
        monthly_revenue,
        LAG(monthly_revenue) OVER (
            PARTITION BY sku_id
            ORDER BY sales_month
        ) AS previous_month_revenue
    FROM monthly_sales
)

SELECT
    sku_id,
    sales_month,
    monthly_revenue,
    previous_month_revenue,
    monthly_revenue - previous_month_revenue AS revenue_change
FROM sales_comparison
WHERE previous_month_revenue IS NOT NULL
  AND monthly_revenue < previous_month_revenue
ORDER BY
    sku_id,
    sales_month;


-- ==========================================================
-- 7. Rank stores within each city
-- City is used because BM_STORES does not contain region.
-- ==========================================================

WITH store_revenue AS (
    SELECT
        st.store_id,
        st.store_name,
        st.city,
        SUM(s.total_value) AS total_revenue
    FROM bm_stores st
    LEFT JOIN bm_sales s
        ON st.store_id = s.store_id
    GROUP BY
        st.store_id,
        st.store_name,
        st.city
)

SELECT
    store_id,
    store_name,
    city,
    total_revenue,
    RANK() OVER (
        PARTITION BY city
        ORDER BY total_revenue DESC
    ) AS store_rank
FROM store_revenue
ORDER BY
    city,
    store_rank;



-- ==========================================================
-- 8. Data quality check
-- Check for NULL and invalid values in BM_SALES
-- ==========================================================

SELECT
    COUNT(*) AS total_rows,

    SUM(CASE WHEN date IS NULL THEN 1 ELSE 0 END) AS null_dates,

    SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) AS null_store_ids,

    SUM(CASE WHEN sku_id IS NULL THEN 1 ELSE 0 END) AS null_sku_ids,

    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_ids,

    SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END) AS null_quantities,

    SUM(CASE WHEN unit_price IS NULL THEN 1 ELSE 0 END) AS null_unit_prices,

    SUM(CASE WHEN total_value IS NULL THEN 1 ELSE 0 END) AS null_total_values,

    SUM(CASE WHEN discount_pct IS NULL THEN 1 ELSE 0 END) AS null_discounts,

    SUM(CASE WHEN quantity < 0 THEN 1 ELSE 0 END) AS negative_quantities,

    SUM(CASE WHEN unit_price < 0 THEN 1 ELSE 0 END) AS negative_prices,

    SUM(CASE WHEN total_value < 0 THEN 1 ELSE 0 END) AS negative_values,

    SUM(CASE WHEN discount_pct < 0 OR discount_pct > 100
             THEN 1 ELSE 0 END) AS invalid_discounts

FROM bm_sales;


-- ==========================================================
-- 9. Repeat customer rate
-- Since BM_SALES has no order_id, repeat purchase is measured
-- as customers having more than one sales record.
-- ==========================================================

WITH customer_purchase_counts AS (
    SELECT
        customer_id,
        COUNT(*) AS purchase_count
    FROM bm_sales
    GROUP BY customer_id
)

SELECT
    COUNT(CASE WHEN purchase_count > 1 THEN 1 END) AS repeat_customers,
    COUNT(*) AS total_customers,
    ROUND(
        COUNT(CASE WHEN purchase_count > 1 THEN 1 END)
        * 100.0 / COUNT(*),
        2
    ) AS repeat_purchase_rate_pct
FROM customer_purchase_counts;


-- ==========================================================
-- 10. Category mix for each city
-- City is used as the geographic grouping because no region
-- column exists in BM_STORES.
-- ==========================================================

WITH category_city_sales AS (
    SELECT
        st.city,
        sk.category,
        SUM(s.total_value) AS category_revenue
    FROM bm_sales s
    INNER JOIN bm_stores st
        ON s.store_id = st.store_id
    INNER JOIN bm_skus sk
        ON s.sku_id = sk.sku_id
    GROUP BY
        st.city,
        sk.category
)

SELECT
    city,
    category,
    category_revenue,
    ROUND(
        category_revenue * 100.0 /
        SUM(category_revenue) OVER (PARTITION BY city),
        2
    ) AS category_mix_pct
FROM category_city_sales
ORDER BY
    city,
    category_mix_pct DESC;