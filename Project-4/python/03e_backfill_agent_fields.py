# python/03e_backfill_agent_fields.py
import pandas as pd
from sqlalchemy import create_engine, text

ENGINE = create_engine(
    "mssql+pyodbc://localhost\\SQLEXPRESS/prudential_dw"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
)

df = pd.read_parquet("data_clean/policy_clean.parquet")
agent_extra = (df[["agent_id", "agent_productivity_score", "agent_tenure_months"]]
               .dropna(subset=["agent_id"]).drop_duplicates(subset="agent_id"))
agent_extra.to_sql("stg_agent_extra", ENGINE, if_exists="replace", index=False)

with ENGINE.begin() as conn:
    conn.execute(text("""
        UPDATE d
        SET d.agent_productivity_score = s.agent_productivity_score,
            d.agent_tenure_months        = s.agent_tenure_months
        FROM dim_agent d
        JOIN stg_agent_extra s ON s.agent_id = d.agent_id
    """))
print("Backfilled agent productivity/tenure fields")