import json, re
from sqlalchemy import create_engine, text
from config import DB_CONN_STR, DATA_PROCESSED, DOCS_DIR

ALLOWED_TABLES = {"subscribers", "service_requests", "network_sites",
                  "circle_monthly_kpi", "circle_targets", "offer_catalogue", "scored_subscribers"}

engine = create_engine(DB_CONN_STR)
schema = json.load(open(DATA_PROCESSED / "schema_catalog.json"))
few_shots = json.load(open(DATA_PROCESSED / "few_shot_queries.json"))
semantic_layer = open(DOCS_DIR / "semantic_layer.md").read()


def build_prompt(question):
    return f"""You are a SQL Server expert. Use ONLY these tables/columns - do not invent any:
{json.dumps(schema, indent=2)}

Certified definitions (use these exactly, do not use your own interpretation):
{semantic_layer}

Example question -> SQL pairs:
{json.dumps(few_shots, indent=2)}

Write a single read-only SELECT query (SQL Server syntax - use TOP, not LIMIT) to answer:
{question}

Return ONLY the raw SQL. No explanation, no markdown code fences, no commentary."""


def validate_sql(sql):
    sql = sql.strip()
    # Strip markdown fences if the LLM added them despite instructions
    sql = re.sub(r"^```sql\s*|\s*```$", "", sql, flags=re.IGNORECASE).strip()

    sql_upper = sql.upper()
    if not sql_upper.startswith("SELECT"):
        raise ValueError("Blocked: query does not start with SELECT")
    if any(word in sql_upper for word in
           ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "EXEC", "MERGE", "GRANT"]):
        raise ValueError("Blocked: non-SELECT statement detected")

    tables_used = re.findall(r"FROM\s+(\w+)|JOIN\s+(\w+)", sql, re.IGNORECASE)
    for a, b in tables_used:
        t = (a or b).lower()
        if t not in ALLOWED_TABLES:
            raise ValueError(f"Blocked: table '{t}' not in allow-list")

    if " TOP " not in sql_upper and "COUNT(" not in sql_upper and "AVG(" not in sql_upper and "GROUP BY" not in sql_upper:
        sql = re.sub(r"SELECT", "SELECT TOP 200", sql, count=1, flags=re.IGNORECASE)

    return sql


from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def ask_llm(prompt):
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def run_query(question):
    raw_sql = ask_llm(build_prompt(question))
    sql = validate_sql(raw_sql)
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        rows = result.fetchall()
        columns = list(result.keys())
    return sql, columns, rows


if __name__ == "__main__":
    q = "Top 5 circles by port-out requests last month"
    sql, cols, rows = run_query(q)
    print("SQL:", sql)
    print("Columns:", cols)
    for r in rows:
        print(r)