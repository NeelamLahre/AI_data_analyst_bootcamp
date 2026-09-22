import time
from sqlalchemy import create_engine, text
from config import DB_CONN_STR

engine = create_engine(DB_CONN_STR)

def log_query(question, route, sql, status, row_count, latency_ms, error=None):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO chatbot_query_log
                (user_question, route, generated_sql, execution_status, row_count, latency_ms, error_message)
            VALUES
                (:q, :route, :sql, :status, :rc, :lat, :err)
        """), {"q": question, "route": route, "sql": sql or "", "status": status,
               "rc": row_count, "lat": latency_ms, "err": error})
        conn.commit()