"""
Step 6 - 15 SQL Queries on the churn dataset
Uses SQLite in-memory so no external DB server is needed.
"""
import sqlite3
import pandas as pd
from config import DATA_RAW

# Load the raw CSV into an in-memory SQLite table called 'customers'
df = pd.read_csv(DATA_RAW)
conn = sqlite3.connect(":memory:")
df.to_sql("customers", conn, index=False, if_exists="replace")

QUERIES = {
    "Q01: Total number of customers": """
        SELECT COUNT(*) AS total_customers
        FROM customers;
    """,

    "Q02: Churn vs Non-Churn count": """
        SELECT Churn, COUNT(*) AS count
        FROM customers
        GROUP BY Churn;
    """,

    "Q03: Average age of churned vs non-churned": """
        SELECT Churn,
               ROUND(AVG(Age), 2) AS avg_age,
               MIN(Age) AS min_age,
               MAX(Age) AS max_age
        FROM customers
        GROUP BY Churn;
    """,

    "Q04: Churn rate by Subscription Type": """
        SELECT [Subscription Type],
               COUNT(*) AS total,
               SUM(Churn) AS churned,
               ROUND(AVG(Churn) * 100, 2) AS churn_rate_pct
        FROM customers
        GROUP BY [Subscription Type]
        ORDER BY churn_rate_pct DESC;
    """,

    "Q05: Churn rate by Contract Length": """
        SELECT [Contract Length],
               COUNT(*) AS total,
               SUM(Churn) AS churned,
               ROUND(AVG(Churn) * 100, 2) AS churn_rate_pct
        FROM customers
        GROUP BY [Contract Length]
        ORDER BY churn_rate_pct DESC;
    """,

    "Q06: Average Total Spend by Churn status": """
        SELECT Churn,
               ROUND(AVG([Total Spend]), 2) AS avg_spend,
               ROUND(SUM([Total Spend]), 2) AS total_spend
        FROM customers
        GROUP BY Churn;
    """,

    "Q07: Top 10 highest spending customers": """
        SELECT CustomerID, Age, Gender,
               [Total Spend], Churn
        FROM customers
        ORDER BY [Total Spend] DESC
        LIMIT 10;
    """,

    "Q08: Average Support Calls by Churn": """
        SELECT Churn,
               ROUND(AVG([Support Calls]), 2) AS avg_support_calls
        FROM customers
        GROUP BY Churn;
    """,

    "Q09: High vs Low support calls - churn rate": """
        SELECT CASE
                   WHEN [Support Calls] > 5 THEN 'High' ELSE 'Low'
               END AS support_level,
               COUNT(*) AS total,
               SUM(Churn) AS churned,
               ROUND(AVG(Churn) * 100, 2) AS churn_rate_pct
        FROM customers
        GROUP BY support_level;
    """,

    "Q10: Usage Frequency buckets and churn rate": """
        SELECT CASE
                   WHEN [Usage Frequency] <= 10 THEN '0-10'
                   WHEN [Usage Frequency] <= 20 THEN '11-20'
                   ELSE '21+'
               END AS usage_bucket,
               COUNT(*) AS total,
               ROUND(AVG(Churn) * 100, 2) AS churn_rate_pct
        FROM customers
        GROUP BY usage_bucket
        ORDER BY usage_bucket;
    """,

    "Q11: Average Tenure by Churn status": """
        SELECT Churn,
               ROUND(AVG(Tenure), 2) AS avg_tenure
        FROM customers
        GROUP BY Churn;
    """,

    "Q12: Short vs Long tenure churn rate": """
        SELECT CASE
                   WHEN Tenure < 12 THEN 'Short (<12m)'
                   ELSE 'Long (12m+)'
               END AS tenure_group,
               COUNT(*) AS total,
               SUM(Churn) AS churned,
               ROUND(AVG(Churn) * 100, 2) AS churn_rate_pct
        FROM customers
        GROUP BY tenure_group;
    """,

    "Q13: Churn rate by Gender": """
        SELECT Gender,
               COUNT(*) AS total,
               SUM(Churn) AS churned,
               ROUND(AVG(Churn) * 100, 2) AS churn_rate_pct
        FROM customers
        GROUP BY Gender;
    """,

    "Q14: Average Payment Delay by Churn": """
        SELECT Churn,
               ROUND(AVG([Payment Delay]), 2) AS avg_payment_delay,
               MAX([Payment Delay]) AS max_delay
        FROM customers
        GROUP BY Churn;
    """,

    "Q15: High-risk customer segment": """
        SELECT COUNT(*) AS high_risk_count,
               SUM(Churn) AS churned,
               ROUND(AVG(Churn) * 100, 2) AS churn_rate_pct
        FROM customers
        WHERE [Support Calls] >= 7
          AND Tenure < 15
          AND [Payment Delay] >= 20;
    """,
}

# Run every query in order and print its result as a small table
for title, sql in QUERIES.items():
    print("=" * 65)
    print(title)
    print("-" * 65)
    result = pd.read_sql_query(sql, conn)
    print(result.to_string(index=False))
    print()

conn.close()
print("All 15 SQL queries executed.")
