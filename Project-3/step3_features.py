import pandas as pd
import numpy as np

df = pd.read_csv('data_cleaned.csv')
print('Starting shape:', df.shape)

def kidney_stage(egfr):
    if egfr >= 90: return 'Normal'
    elif egfr >= 60: return 'Mild'
    elif egfr >= 30: return 'Moderate'
    else: return 'Severe'

df['kidney_stage'] = df['eGFR'].apply(kidney_stage)
print(df['kidney_stage'].value_counts())


def kidney_stage(egfr):
    if egfr >= 90: return 'Normal'
    elif egfr >= 60: return 'Mild'
    elif egfr >= 30: return 'Moderate'
    else: return 'Severe'

df['kidney_stage'] = df['eGFR'].apply(kidney_stage)
print(df['kidney_stage'].value_counts())

df['polypharmacy'] = (df['Concurrent_Drugs'] >= 5).astype(int)

def bmi_category(bmi):
    if bmi < 18.5: return 'Underweight'
    elif bmi < 25: return 'Normal'
    elif bmi < 30: return 'Overweight'
    else: return 'Obese'

df['bmi_category'] = df['BMI'].apply(bmi_category)

df['age_group'] = pd.cut(df['Age'], bins=[0, 18, 40, 60, 80, 120],
                          labels=['Pediatric', 'Young Adult', 'Middle Aged', 'Senior', 'Elderly'])
print(df['age_group'].value_counts())

df['elderly_high_dose'] = ((df['Age'] > 65) & (df['Dosage'] > df['Dosage'].median())).astype(int)

df['de_ritis_ratio'] = df['AST_Enzyme'] / (df['ALT_Enzyme'] + 0.01)


df.to_csv('data_features.csv', index=False)
print(f'Features after engineering: {df.shape[1]} columns')
print('Final shape:', df.shape)

