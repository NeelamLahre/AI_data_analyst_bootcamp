# python/03d_backfill_sentiment.py
import pandas as pd
from sqlalchemy import create_engine, text

ENGINE = create_engine(
    "mssql+pyodbc://localhost\\SQLEXPRESS/prudential_dw"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
)

df = pd.read_parquet("data_clean/policy_clean.parquet")
sentiment_cols = df[["policy_id", "customer_sentiment_score", "nps_score"]]
sentiment_cols.to_sql("stg_sentiment_fields", ENGINE, if_exists="replace", index=False)

with ENGINE.begin() as conn:
    conn.execute(text("""
        UPDATE f
        SET f.customer_sentiment_score = s.customer_sentiment_score,
            f.nps_score                 = s.nps_score
        FROM fact_policy_new_business f
        JOIN stg_sentiment_fields s ON s.policy_id = f.policy_id
    """))
print("Backfilled sentiment fields")