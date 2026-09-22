from sqlalchemy import create_engine, inspect
import json
from config import DB_CONN_STR, DATA_PROCESSED

engine = create_engine(DB_CONN_STR)
insp = inspect(engine)

schema = {}
for table in insp.get_table_names():
    schema[table] = [{"name": c["name"], "type": str(c["type"])} for c in insp.get_columns(table)]

with open(DATA_PROCESSED / "schema_catalog.json", "w") as f:
    json.dump(schema, f, indent=2)
print(json.dumps(schema, indent=2))