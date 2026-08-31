"""Central configuration for paths and constants."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the raw dataset CSV
DATA_RAW = os.path.join(BASE_DIR, "customer_churn_dataset-testing-master.csv")

# Path where the cleaned dataset will be saved (created in Step 2)
DATA_CLEANED = os.path.join(BASE_DIR, "data_cleaned.csv")

# Folder where all plots, models, and result CSVs get saved
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# The column we are trying to predict
TARGET = "Churn"

# Used so results are reproducible (same "random" split every time)
RANDOM_STATE = 42
TEST_SIZE = 0.2
