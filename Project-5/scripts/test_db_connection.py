from sqlalchemy import create_engine, text
from config import DB_CONN_STR

engine = create_engine(DB_CONN_STR)
with engine.connect() as conn:
    result = conn.execute(text("SELECT TOP 5 * FROM subscribers"))
    for row in result:
        print(row)