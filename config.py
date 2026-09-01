"""Central configuration for paths and constants."""
import os
from sklearn.model_selection import train_test_split

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

# Three-way split proportions of the FULL dataset:
# Train 60% -> the model learns from this
# Validation 20% -> used to check performance while building each model
# Test 20% -> held out untouched, used only once for the final comparison
TEST_SIZE = 0.2
VAL_SIZE = 0.2


def split_data(X, y):
    """
    Splits X, y into Train / Validation / Test sets.

    Every script that calls this with the same X, y gets the exact same
    split (because RANDOM_STATE is fixed), so Decision Tree and Random
    Forest are always trained and judged on identical data - a fair fight.
    """
    # Step 1: carve off the Test set first. It stays untouched until Step 5.
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    # Step 2: split what's left into Train and Validation.
    # val_ratio is recalculated so VAL_SIZE ends up correct as a % of the
    # ORIGINAL data, not just of the leftover chunk.
    val_ratio = VAL_SIZE / (1 - TEST_SIZE)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_ratio,
        random_state=RANDOM_STATE, stratify=y_temp,
    )

    return X_train, X_val, X_test, y_train, y_val, y_test
