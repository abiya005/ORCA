import pandas as pd
import glob
import os

datasets_path = r"d:\ORCA\datasets\apk_scam"
csv_files = glob.glob(os.path.join(datasets_path, "*.csv"))

print(f"Found {len(csv_files)} CSV files in {datasets_path}")

for f in csv_files:
    print(f"\nAnalyzing file: {os.path.basename(f)}")
    # Read just the first few rows to speed up inspection
    df = pd.read_csv(f, nrows=5)
    print(f"Columns: {list(df.columns[:5])}... Total columns: {len(df.columns)}")
    print(f"Sample data columns: {df.columns.tolist()[-5:]}")
    # Read the whole file class distribution
    full_df = pd.read_csv(f, usecols=['Class', 'category'] if 'Class' in df.columns else ['category'])
    print(f"Shape: {full_df.shape}")
    if 'Class' in full_df.columns:
        print("Class distribution:")
        print(full_df['Class'].value_counts())
    if 'category' in full_df.columns:
        print("Category distribution:")
        print(full_df['category'].value_counts())
