-- ============================================================================
-- Schema changes applied AFTER the initial Stage 7 build.
--
-- These were run ad-hoc in SSMS during Stage 10 and Stage 11 when the
-- simulation engine and dashboards needed columns that Stage 8's original
-- FACT_COLS list (matching the guide's own limited list) never loaded.
--
-- They are already folded into 01_schema.sql's CREATE TABLE statements, so a
-- fresh build from 01_schema.sql does NOT need to run this file. This file
-- exists purely as an audit record of what actually happened to the live
-- database, in the order it happened.
-- ============================================================================

-- Stage 10 (S-02 needed real before/after rider premiums and co-pay context)
ALTER TABLE fact_policy_new_business ADD
    rider_attached_flag      BIT,
    ip_plan_tier              VARCHAR(20),
    rider_premium_before_sgd NUMERIC(14,2),
    rider_premium_after_sgd  NUMERIC(14,2);

-- Stage 11 (D-5 Claims & Customer Trust needed a sentiment vs. lapse scatter)
ALTER TABLE fact_policy_new_business ADD
    customer_sentiment_score NUMERIC(5,3),
    nps_score                 INT;

-- Stage 11 (D-6 Agency Performance needed the productivity quadrant)
ALTER TABLE dim_agent ADD
    agent_productivity_score NUMERIC(6,2),
    agent_tenure_months       INT;
