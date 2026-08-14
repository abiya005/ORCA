import pandas as pd
f = r"d:\ORCA\datasets\apk_scam\SMS_apk_scams_15000.csv"
df = pd.read_csv(f, nrows=1)
cols = [c for c in df.columns if 'permission' in c.lower() or 'sms' in c.lower()]
print(f"Total matching columns: {len(cols)}")
print(cols[:30])
