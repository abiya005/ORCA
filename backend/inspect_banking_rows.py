import pandas as pd
f = r"d:\ORCA\datasets\apk_scam\banking_apk_scams_synthetic_15000.csv"
df = pd.read_csv(f, nrows=5)
for col in ['app_name', 'package_name', 'target_sdk', 'risk_level', 'dangerous_permissions_list', 'malware_permission_matches']:
    print(f"\nCol: {col}")
    print(df[col].tolist())
