from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
CHART_DIR = OUTPUT_DIR / "charts"
DOCS_DIR = PROJECT_ROOT / "docs"

SUBSCRIBERS_CSV = DATA_RAW / "subscribers.csv"
DATASET_XLSX = DATA_RAW / "Jio_Retention_Dataset.xlsx"

# These 3 columns reveal the churn outcome directly - never use them
# to explain churn, or your "findings" are just restating the answer.
LEAKAGE_COLUMNS = ["mnp_enquiry_flag", "churn_reason", "churn_date"]

TENURE_BINS = [0, 3, 6, 12, 24, 48, 1000]
TENURE_LABELS = ["0-3m", "3-6m", "6-12m", "12-24m", "24-48m", "48m+"]

ARPU_BINS = [0, 100, 150, 200, 250, 300, 100000]
ARPU_LABELS = ["<100", "100-150", "150-200", "200-250", "250-300", "300+"]

DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

RANDOM_STATE = 42

import os
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

DB_CONN_STR = (
    f"mssql+pyodbc://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_SERVER']}/{os.environ['DB_NAME']}"
    "?driver=ODBC+Driver+17+for+SQL+Server"
)


GROQ_API_KEY = os.environ["GROQ_API_KEY"]