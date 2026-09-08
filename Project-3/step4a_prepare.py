import pandas as pd
import joblib
from sklearn.model_selection import train_test_split

df = pd.read_csv('data_features.csv')
print('Starting shape:', df.shape)


drop_cols = [
    'Patient_ID',        # identifier, no predictive signal
    'Admission_Date',    # raw date string, not usable as-is
    'Notes',              # free text, mostly blank or "See chart"
    'blood_pressure',    # redundant — already split into Systolic_BP/Diastolic_BP
    'Adverse_Event',     # a DIFFERENT outcome recorded at the same encounter — leakage risk
    'Readmission_30d',   # same reason — a separate outcome, not a valid input feature
]
df = df.drop(columns=[c for c in drop_cols if c in df.columns])

df['gender_encoded'] = df['Gender'].map({'Male': 1, 'Female': 0, 'Unknown': -1})
df = df.drop(columns=['Gender'])





# Duration_Days sometimes contains the text "ongoing" instead of a number —
# that's real clinical meaning (long-term/indefinite treatment), not garbage,
# so capture it as its own flag before converting the rest to numeric.
df['duration_ongoing'] = (
    df['Duration_Days'].astype(str).str.strip().str.lower() == 'ongoing'
).astype(int)

df['Duration_Days'] = pd.to_numeric(df['Duration_Days'], errors='coerce')
df['Duration_Days'] = df['Duration_Days'].fillna(df['Duration_Days'].median())






cat_cols = ['Ethnicity', 'Route', 'Diagnosis', 'Smoking_Status', 'Alcohol_Use',
            'kidney_stage', 'bmi_category', 'age_group', 'Drug_Name']
cat_cols = [c for c in cat_cols if c in df.columns]
df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
print('Shape after encoding:', df.shape)


TARGET = 'Treatment_Outcome'
X = df.drop(columns=[TARGET])
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f'Train: {X_train.shape}, Test: {X_test.shape}')

joblib.dump((X_train, X_test, y_train, y_test), 'outputs/train_test_split.pkl')
print('Saved outputs/train_test_split.pkl')
