# python/03c_backfill_rider_fields.py
import pandas as pd
from sqlalchemy import create_engine, text

ENGINE = create_engine(
    "mssql+pyodbc://localhost\\SQLEXPRESS/prudential_dw"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
)

df = pd.read_parquet("data_clean/policy_clean.parquet")
rider_cols = df[["policy_id", "rider_attached_flag", "ip_plan_tier",
                  "rider_premium_before_sgd", "rider_premium_after_sgd"]]
rider_cols.to_sql("stg_rider_fields", ENGINE, if_exists="replace", index=False)

with ENGINE.begin() as conn:
    conn.execute(text("""
        UPDATE f
        SET f.rider_attached_flag      = s.rider_attached_flag,
            f.ip_plan_tier              = s.ip_plan_tier,
            f.rider_premium_before_sgd = s.rider_premium_before_sgd,
            f.rider_premium_after_sgd  = s.rider_premium_after_sgd
        FROM fact_policy_new_business f
        JOIN stg_rider_fields s ON s.policy_id = f.policy_id
    """))
print("Backfilled rider fields")