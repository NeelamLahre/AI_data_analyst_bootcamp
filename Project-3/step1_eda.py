import pandas as pd
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns


DATA_PATH = 'clinical_data_raw.csv'
OUTPUT_DIR = 'outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(DATA_PATH)
print('Dataset Shape:', df.shape)

print('\nColumn Names:')
for col in df.columns:
    print(repr(col))

print('\nColumn Types:')
print(df.dtypes)

print('\nFirst 5 Rows:')
print(df.head())

print('\nDescriptive Statistics:')
print(df.describe())

print('\nMissing Values:')
print(df.isnull().sum())

print('\nTarget Distribution:')
print(df['Treatment_Outcome'].value_counts(dropna=False))
print(df['Treatment_Outcome'].value_counts(normalize=True, dropna=False))




numeric_cols = df.select_dtypes(include='number').columns.tolist()
numeric_cols = [c for c in numeric_cols if 'ID' not in c and 'unnamed' not in c.lower()]

fig, axes = plt.subplots(3, 3, figsize=(15, 12))
for ax, col in zip(axes.flatten(), numeric_cols[:9]):
    sns.histplot(df[col].dropna(), kde=True, ax=ax, color='teal')
    ax.set_title(f'Distribution of {col}')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/step1_distributions.png', dpi=150)
print('Saved distribution plots to outputs/step1_distributions.png')

plt.figure(figsize=(12, 10))
corr = df[numeric_cols].corr()
sns.heatmap(corr, annot=True, cmap='RdYlGn', center=0, fmt='.2f')
plt.title('Feature Correlation Matrix')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/step1_correlation.png', dpi=150)
print('Saved correlation heatmap to outputs/step1_correlation.png')