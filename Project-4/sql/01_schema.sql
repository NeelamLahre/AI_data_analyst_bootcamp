-- ===== Dimensions =====
CREATE TABLE dim_product (
    product_key      INT IDENTITY(1,1) PRIMARY KEY,
    product_name     VARCHAR(80) NOT NULL,
    product_category VARCHAR(40) NOT NULL,
    is_low_margin    BIT NOT NULL,
    CONSTRAINT uq_product UNIQUE (product_name, product_category)
);

CREATE TABLE dim_agent (
    agent_key        INT IDENTITY(1,1) PRIMARY KEY,
    agent_id         VARCHAR(20) NOT NULL,
    agent_name       VARCHAR(120),
    agent_tier       VARCHAR(20),
    agency_unit      VARCHAR(10),
    agent_status     VARCHAR(20),
    attrition_risk   NUMERIC(5,3),
    valid_from       DATE NOT NULL,
    valid_to         DATE NOT NULL DEFAULT '9999-12-31',
    is_current       BIT NOT NULL DEFAULT 1,
    -- added during Stage 11 (D-6 Agency Performance needed these; originally ALTER TABLE'd on
    -- the live database, folded back in here so a fresh build doesn't need a separate step)
    agent_productivity_score NUMERIC(6,2),
    agent_tenure_months       INT
);
CREATE INDEX ix_agent_current ON dim_agent (agent_id) WHERE is_current = 1;

CREATE TABLE dim_date (
    date_key    INT PRIMARY KEY,
    [date]      DATE NOT NULL,
    year        SMALLINT NOT NULL,
    quarter     TINYINT NOT NULL,
    month       TINYINT NOT NULL,
    year_month  CHAR(7) NOT NULL
);

CREATE TABLE dim_customer (
    customer_key     INT IDENTITY(1,1) PRIMARY KEY,
    customer_id      VARCHAR(20) NOT NULL UNIQUE,
    gender           VARCHAR(10),
    age              SMALLINT,
    income_band      VARCHAR(20),
    residency_status VARCHAR(30),
    occupation_group VARCHAR(40)
);

CREATE TABLE dim_channel (
    channel_key  INT IDENTITY(1,1) PRIMARY KEY,
    channel_name VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE dim_assessor (
    assessor_key                 INT IDENTITY(1,1) PRIMARY KEY,
    assessor_id                  VARCHAR(20) NOT NULL UNIQUE,
    assessor_approval_limit_sgd  NUMERIC(14,2)
);

CREATE TABLE dim_claim_type (
    claim_type_key INT IDENTITY(1,1) PRIMARY KEY,
    claim_type     VARCHAR(40) NOT NULL UNIQUE
);

-- ===== Facts =====
CREATE TABLE fact_policy_new_business (
    policy_key         BIGINT IDENTITY(1,1) PRIMARY KEY,
    policy_id          VARCHAR(20) NOT NULL UNIQUE,
    customer_key       INT REFERENCES dim_customer(customer_key),
    product_key        INT REFERENCES dim_product(product_key),
    channel_key        INT REFERENCES dim_channel(channel_key),
    agent_key          INT REFERENCES dim_agent(agent_key),
    start_date_key     INT REFERENCES dim_date(date_key),

    annual_premium_sgd NUMERIC(14,2) NOT NULL CHECK (annual_premium_sgd > 0),
    sum_assured_sgd    NUMERIC(16,2),
    ape_sgd            NUMERIC(14,2),
    nbp_margin_pct     NUMERIC(6,4) CHECK (nbp_margin_pct BETWEEN 0 AND 1),
    nbp_sgd            AS (ape_sgd * nbp_margin_pct) PERSISTED,

    months_inforce     INT,
    lapse_flag         BIT,
    persistency_13m    BIT,
    care_delay_days    INT,
    copay_pct          NUMERIC(5,2),

    -- added during Stage 10 (S-02 needed rider fields) and Stage 11 (D-5 needed sentiment/NPS);
    -- originally ALTER TABLE'd on the live database, folded back in here for a fresh build
    rider_attached_flag       BIT,
    ip_plan_tier               VARCHAR(20),
    rider_premium_before_sgd  NUMERIC(14,2),
    rider_premium_after_sgd   NUMERIC(14,2),
    customer_sentiment_score  NUMERIC(5,3),
    nps_score                  INT,

    dq_row_status      VARCHAR(10) NOT NULL DEFAULT 'OK',
    load_ts            DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
CREATE INDEX ix_pnb_date    ON fact_policy_new_business (start_date_key);
CREATE INDEX ix_pnb_product ON fact_policy_new_business (product_key);

CREATE TABLE fact_claim (
    claim_key             BIGINT IDENTITY(1,1) PRIMARY KEY,
    claim_id              VARCHAR(20) NOT NULL UNIQUE,
    policy_key            BIGINT REFERENCES fact_policy_new_business(policy_key),
    assessor_key          INT REFERENCES dim_assessor(assessor_key),
    claim_type_key        INT REFERENCES dim_claim_type(claim_type_key),
    claim_date_key        INT REFERENCES dim_date(date_key),

    claim_amount_sgd      NUMERIC(14,2),
    claim_tat_days        INT,
    claim_status          VARCHAR(20),
    claim_decline_reason  VARCHAR(200),
    approval_above_limit  BIT,
    sod_breach            BIT,
    fraud_risk_score      NUMERIC(5,3),
    disputed_flag         BIT,
    complaint_flag        BIT,

    dq_row_status         VARCHAR(10) NOT NULL DEFAULT 'OK',
    load_ts               DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

-- ===== Scenario store =====
CREATE TABLE scenario_run (
    run_id        BIGINT IDENTITY(1,1) PRIMARY KEY,
    scenario_code VARCHAR(10) NOT NULL,
    scenario_name VARCHAR(160) NOT NULL,
    run_by        VARCHAR(80),
    run_ts        DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    iterations    INT NOT NULL,
    random_seed   INT NOT NULL
);

CREATE TABLE scenario_result (
    run_id        BIGINT REFERENCES scenario_run(run_id),
    metric_name   VARCHAR(60),
    p05           NUMERIC(18,4),
    p50           NUMERIC(18,4),
    p95           NUMERIC(18,4),
    baseline      NUMERIC(18,4),
    delta_vs_base NUMERIC(18,4)
);