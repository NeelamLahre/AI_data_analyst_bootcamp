import sqlite3
import pandas as pd

df = pd.read_csv('data_features.csv')
conn = sqlite3.connect(':memory:')
df.to_sql('patients', conn, index=False, if_exists='replace')

def run_query(title, sql):
    print(f'\n{title}')
    print('=' * 60)
    result = pd.read_sql_query(sql, conn)
    print(result.to_string(index=False))
    return result


run_query('Q1: Overall Treatment Outcomes', '''
    SELECT Treatment_Outcome,
           COUNT(*) as patient_count,
           ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM patients), 2) as pct
    FROM patients
    GROUP BY Treatment_Outcome
''')

run_query('Q2: Efficacy by Age Group', '''
    SELECT age_group,
           COUNT(*) as total_patients,
           SUM(Treatment_Outcome) as effective_count,
           ROUND(AVG(Treatment_Outcome) * 100, 2) as efficacy_pct
    FROM patients
    GROUP BY age_group
    ORDER BY efficacy_pct DESC
''')

run_query('Q3: Drug Efficacy Ranking (min 100 prescriptions)', '''
    SELECT Drug_Name,
           COUNT(*) as total_prescribed,
           ROUND(AVG(Treatment_Outcome) * 100, 2) as efficacy_rate
    FROM patients
    GROUP BY Drug_Name
    HAVING total_prescribed >= 100
    ORDER BY efficacy_rate DESC
    LIMIT 10
''')

run_query('Q4: High-Risk Patients', '''
    SELECT Patient_ID, Age, Creatinine, Concurrent_Drugs, polypharmacy, kidney_stage
    FROM patients
    WHERE Age > 65 AND Creatinine > 1.5 AND polypharmacy = 1
    ORDER BY Creatinine DESC
    LIMIT 20
''')

run_query('Q5: Outcome vs Dosage Level', '''
    SELECT CASE
             WHEN Dosage < 100 THEN 'Low (<100mg)'
             WHEN Dosage BETWEEN 100 AND 500 THEN 'Medium (100-500mg)'
             ELSE 'High (>500mg)'
           END as dosage_level,
           COUNT(*) as patients,
           ROUND(AVG(Treatment_Outcome) * 100, 2) as efficacy_pct
    FROM patients
    GROUP BY dosage_level
''')

