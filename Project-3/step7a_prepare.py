import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

df = pd.read_csv('data_features.csv')

drop_cols = ['Patient_ID', 'Admission_Date', 'Notes', 'blood_pressure', 'Adverse_Event', 'Readmission_30d']
df = df.drop(columns=[c for c in drop_cols if c in df.columns])

df['duration_ongoing'] = (df['Duration_Days'].astype(str).str.strip().str.lower() == 'ongoing').astype(int)
df['Duration_Days'] = pd.to_numeric(df['Duration_Days'], errors='coerce')
df['Duration_Days'] = df['Duration_Days'].fillna(df['Duration_Days'].median())

df['gender_encoded'] = df['Gender'].map({'Male': 1, 'Female': 0, 'Unknown': -1})
df = df.drop(columns=['Gender'])

# FIX 1: normalize spelling/case/whitespace BEFORE one-hot encoding,
# so "Amoxicillin" / "AMOXICILLIN" / "amoxycillin" collapse into one category
cat_cols = ['Ethnicity', 'Route', 'Diagnosis', 'Smoking_Status', 'Alcohol_Use',
            'kidney_stage', 'bmi_category', 'age_group', 'Drug_Name']
cat_cols = [c for c in cat_cols if c in df.columns]
for col in cat_cols:
    df[col] = df[col].astype(str).str.strip().str.lower()

df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
print('Shape after encoding:', df.shape)

TARGET = 'Treatment_Outcome'
X = df.drop(columns=[TARGET])
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# FIX 2: scale features for the neural network — fit on train only, apply to both
scaler = StandardScaler()
X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns, index=X_train.index)
X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns, index=X_test.index)

joblib.dump((X_train_scaled, X_test_scaled, y_train, y_test), 'outputs/train_test_split_dl.pkl')
joblib.dump(scaler, 'outputs/dl_scaler.pkl')
print('Saved outputs/train_test_split_dl.pkl:', X_train_scaled.shape, X_test_scaled.shape)