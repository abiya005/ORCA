import pandas as pd
f = r"d:\ORCA\datasets\apk_scam\banking_apk_scams_synthetic_15000.csv"
df = pd.read_csv(f, nrows=2)
print("Banking Scam Columns:")
print(list(df.columns))
