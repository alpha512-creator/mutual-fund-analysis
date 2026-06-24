import os
import glob
import pandas as pd

RAW_DATA_DIR = "data/raw"

def profile_datasets():
    print("Phase 1: Profiling Datasets")
    csv_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))

    if not csv_files:
        print("No CSV files found in data/raw")
        return {}

    datasets = {}
    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        df = pd.read_csv(file_path)
        datasets[file_name] = df

        print("\n" + "="*50)
        print(f"Dataset: {file_name}")
        print("="*50)
        print(f"Shape: {df.shape}")
        print("\nData Types:")
        print(df.dtypes)
        print("\nHead Preview:")
        print(df.head())

        null_counts = df.isnull().sum().sum()
        if null_counts > 0:
            print(f"Anomaly: Found {null_counts} missing values in this file.")

    return datasets

def explore_fund_master(datasets):
    print("\nPhase 2: Exploring Fund Master Metadata")
    master_file = "fund_master.csv"

    if master_file in datasets:
        df_master = datasets[master_file]
        if "scheme_name" in df_master.columns:
            print("\nExposed Columns in Live Master API:", list(df_master.columns))
            df_master['extracted_amc'] = df_master['scheme_name'].apply(lambda x: str(x).split('-')[0].strip())
            print("\nUnique Asset Management Companies Sample:")
            print(df_master['extracted_amc'].unique()[:10])

        print("\nAMFI Scheme Code Structure:")
        print("Standard AMFI codes are unique 6-digit numeric identifiers")
    else:
        print(f"'{master_file}' not found in dataset")

def validate_amfi_codes(datasets):
    print("\nPhase 3: Data Quality & Cross-Validation Summary")
    master_file = "fund_master.csv"

    if master_file in datasets:
        df_master = datasets[master_file]
        global_master_codes = set(df_master["scheme_code"].dropna().astype(str).unique())

        target_codes = set()
        for name, df in datasets.items():
            if name != master_file and "scheme_code" in df.columns:
                target_codes.update(df["scheme_code"].astype(str).unique())

        missing_targets = target_codes - global_master_codes

        print("\nDATA QUALITY REPORT SUMMARY:")
        print(f"• Unique Codes in Global Master File: {len(global_master_codes)}")
        print(f"• Unique Target Codes Ingested: {len(target_codes)} (Targeting HDFC & 5 Bluechips)")

        if missing_targets:
            print(f"CRITICAL ANOMALY: Your ingested targets {missing_targets} don't exist in the global master list!")
        else:
            print("Referential Integrity Check: Passed")
    else:
        print("Validation: 'fund_master.csv' must be added to data/raw")

if __name__ == "__main__":
    loaded_dfs = profile_datasets()
    explore_fund_master(loaded_dfs)
    validate_amfi_codes(loaded_dfs)
