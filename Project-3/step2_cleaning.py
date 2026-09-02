import pandas as pd
import numpy as np

df = pd.read_csv('clinical_data_raw.csv')
print('Starting shape:', df.shape)

df = df.drop(columns=['patient_id', ' age', 'gender '])

df['Drug_Name'] = df['Drug_Name'].fillna(df['drug_name'])
df = df.drop(columns=['drug_name'])

df = df.drop(columns=['Extra_Col_1', 'Extra_Col_2', 'unnamed_0'])

df.loc[(df['Age'] < 0) | (df['Age'] > 120), 'Age'] = np.nan
df.loc[(df['Weight_kg'] <= 0) | (df['Weight_kg'] > 300), 'Weight_kg'] = np.nan
df.loc[(df['BMI'] <= 0) | (df['BMI'] > 80), 'BMI'] = np.nan
df.loc[df['eGFR'] < 0, 'eGFR'] = np.nan
df.loc[df['ALT_Enzyme'] < 0, 'ALT_Enzyme'] = np.nan
df.loc[df['AST_Enzyme'] < 0, 'AST_Enzyme'] = np.nan
df.loc[(df['HbA1c'] < 3.5) | (df['HbA1c'] > 20), 'HbA1c'] = np.nan

df['Gender'] = df['Gender'].astype(str).str.strip().str.lower()
gender_map = {
    'f': 'Female', 'female': 'Female',
    'm': 'Male', 'male': 'Male',
}
df['Gender'] = df['Gender'].map(gender_map).fillna('Unknown')
print(df['Gender'].value_counts())

df['Adverse_Event'] = df['Adverse_Event'].replace({'Yes': 1, 'yes': 1, 'No': 0, 'no': 0})
df['Adverse_Event'] = pd.to_numeric(df['Adverse_Event'], errors='coerce')

df['Treatment_Outcome'] = pd.to_numeric(df['Treatment_Outcome'], errors='coerce')
# Drop rows where the target itself is missing — we can't train/validate on those
df = df.dropna(subset=['Treatment_Outcome'])
print('Shape after dropping missing targets:', df.shape)

def parse_dosage(val):
    val = str(val).strip()
    if '/' in val:
        try:
            num, denom = val.split('/')
            return float(num) / float(denom.split()[0])
        except Exception:
            return np.nan
    try:
        return float(val)
    except Exception:
        return np.nan

df['Dosage'] = df['Dosage'].apply(parse_dosage)

numeric_cols = df.select_dtypes(include='number').columns
for col in numeric_cols:
    if df[col].isnull().sum() > 0:
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
        print(f'Filled {col} with median={median_val:.2f}')

cat_cols = df.select_dtypes(include='object').columns
for col in cat_cols:
    if df[col].isnull().sum() > 0:
        mode_val = df[col].mode()[0]
        df[col] = df[col].fillna(mode_val)

dupes = df.duplicated().sum()
print(f'Duplicate rows: {dupes}')
df = df.drop_duplicates()


def cap_outliers(df, col):
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower, upper = Q1 - 1.5*IQR, Q3 + 1.5*IQR
    before = ((df[col] < lower) | (df[col] > upper)).sum()
    df[col] = df[col].clip(lower, upper)
    print(f'{col}: capped {before} outliers to [{lower:.2f}, {upper:.2f}]')
    return df

for col in ['Age', 'BMI', 'Weight_kg', 'Hemoglobin', 'Creatinine', 'ALT_Enzyme', 'AST_Enzyme']:
    df = cap_outliers(df, col)


df.to_csv('data_cleaned.csv', index=False)
print('Saved data_cleaned.csv, final shape:', df.shape) 



