import pandas as pd
f = r"d:\ORCA\datasets\apk_scam\SMS_apk_scams_15000.csv"
df = pd.read_csv(f, nrows=1)
cols = list(df.columns)
with open(r"d:\ORCA\backend\all_columns.txt", "w") as out:
    for c in cols:
        out.write(c + "\n")
print(f"Total columns: {len(cols)}")
print("First 100 columns:")
print(cols[:100])
