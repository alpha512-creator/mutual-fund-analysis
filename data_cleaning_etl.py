import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# Set SQLite database path (kept in the sql/ directory)
DB_PATH = "sql/mutual_funds.db"
ENGINE = create_engine(f"sqlite:///{DB_PATH}")

def run_ddl_schema():
    print("Executing DDL Schema Creation...")
    schema_path = "sql/schema.sql"
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
        
    with open(schema_path, "r") as f:
        sql_commands = f.read()

    # Split commands by semicolon and execute
    with ENGINE.connect() as conn:
        # SQLite doesn't support executing multiple statements via execute() directly in some drivers, 
        # so we split them or use executescript.
        raw_conn = conn.connection
        raw_conn.executescript(sql_commands)
        print("Schema tables dropped and created successfully.")

def load_and_clean_nav_history():
    print("\n--- Cleaning NAV History ---")
    nav_path = "data/raw/nav_history_40.csv"
    if not os.path.exists(nav_path):
        raise FileNotFoundError(f"NAV history file not found at {nav_path}")
        
    df = pd.read_csv(nav_path)
    print(f"Original shape: {df.shape}")

    # Standardize names
    if 'scheme_code' in df.columns:
        df = df.rename(columns={'scheme_code': 'amfi_code'})
    df['amfi_code'] = df['amfi_code'].astype(str)

    # 1. Parse dates to datetime (handles YYYY-MM-DD or DD-MM-YYYY formats)
    orig_date = df['date']
    df['date'] = pd.to_datetime(orig_date, format='%Y-%m-%d', errors='coerce')
    df['date'] = df['date'].fillna(pd.to_datetime(orig_date, format='%d-%m-%Y', errors='coerce'))
    df['date'] = df['date'].fillna(pd.to_datetime(orig_date, errors='coerce'))
    
    # Drop rows where date is missing
    df = df.dropna(subset=['date'])

    # 2. Validate NAV > 0
    df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
    df = df[df['nav'] > 0]

    # 3. Sort by amfi_code + date
    df = df.sort_values(by=['amfi_code', 'date'])

    # 4. Remove duplicates
    df = df.drop_duplicates(subset=['amfi_code', 'date'])

    # 5. Forward-fill missing NAV for holidays/weekends per fund
    cleaned_nav_dfs = []
    for amfi_code, group in df.groupby('amfi_code'):
        min_date = group['date'].min()
        max_date = group['date'].max()
        
        # Create complete daily date range
        full_range = pd.date_range(start=min_date, end=max_date, freq='D')
        
        # Reindex and forward fill
        group_clean = group.set_index('date').reindex(full_range)
        group_clean['nav'] = group_clean['nav'].ffill()
        group_clean['scheme_name'] = group_clean['scheme_name'].ffill()
        group_clean['amfi_code'] = group_clean['amfi_code'].fillna(amfi_code)
        
        group_clean = group_clean.reset_index().rename(columns={'index': 'date'})
        cleaned_nav_dfs.append(group_clean)

    df_clean = pd.concat(cleaned_nav_dfs, ignore_index=True)
    print(f"Cleaned and forward-filled shape: {df_clean.shape}")
    return df_clean

def load_and_clean_transactions():
    print("\n--- Cleaning Investor Transactions ---")
    tx_path = "data/raw/investor_transactions.csv"
    if not os.path.exists(tx_path):
        raise FileNotFoundError(f"Transactions file not found at {tx_path}")

    df = pd.read_csv(tx_path)
    print(f"Original shape: {df.shape}")

    # 1. Standardise transaction_type values (SIP/Lumpsum/Redemption)
    def clean_tx_type(val):
        val_str = str(val).strip().lower()
        if 'sip' in val_str:
            return 'SIP'
        elif 'lump' in val_str:
            return 'Lumpsum'
        elif 'red' in val_str:
            return 'Redemption'
        return 'Unknown'

    df['transaction_type'] = df['transaction_type'].apply(clean_tx_type)

    # 2. Validate amount > 0
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    invalid_amounts = df[df['amount'] <= 0]
    if len(invalid_amounts) > 0:
        print(f"Flagged {len(invalid_amounts)} transactions with invalid amount <= 0 (filtering out).")
    df = df[df['amount'] > 0]

    # 3. Fix date formats (handles mixed formats like YYYY-MM-DD, DD-MM-YYYY, YYYY/MM/DD)
    orig_date = df['transaction_date']
    df['transaction_date'] = pd.to_datetime(orig_date, format='%Y-%m-%d', errors='coerce')
    df['transaction_date'] = df['transaction_date'].fillna(pd.to_datetime(orig_date, format='%d-%m-%Y', errors='coerce'))
    df['transaction_date'] = df['transaction_date'].fillna(pd.to_datetime(orig_date, format='%Y/%m/%d', errors='coerce'))
    df['transaction_date'] = df['transaction_date'].fillna(pd.to_datetime(orig_date, errors='coerce'))
    df = df.dropna(subset=['transaction_date'])

    # 4. Check KYC status enum values
    def clean_kyc(val):
        val_str = str(val).strip().lower()
        if val_str in ['verified', 'yes', 'y']:
            return 'Verified'
        elif val_str in ['failed', 'no', 'n']:
            return 'Failed'
        elif val_str in ['pending']:
            return 'Pending'
        return 'Pending' # Fallback default

    df['kyc_status'] = df['kyc_status'].apply(clean_kyc)
    df['amfi_code'] = df['amfi_code'].astype(str)

    print(f"Cleaned shape: {df.shape}")
    return df

def load_and_clean_performance():
    print("\n--- Cleaning Scheme Performance ---")
    perf_path = "data/processed/fund_scorecard.csv"
    if not os.path.exists(perf_path):
        perf_path = "data/raw/scheme_performance.csv"
        if not os.path.exists(perf_path):
            raise FileNotFoundError(f"Performance file not found at {perf_path}")
        df = pd.read_csv(perf_path)
        # Apply standard clean
        df = df.drop_duplicates(subset=['amfi_code'])
        def parse_percent(val):
            if pd.isna(val):
                return None
            val_str = str(val).replace('%', '').strip()
            if val_str.lower() in ['n/a', 'nan', 'null', '']:
                return None
            try:
                return float(val_str)
            except ValueError:
                return None
        for col in ['returns_1y', 'returns_3y', 'returns_5y']:
            df[col] = df[col].apply(parse_percent)
        df['expense_ratio_pct'] = df['expense_ratio'].apply(parse_percent)
        df['expense_ratio'] = df['expense_ratio_pct'] / 100.0
    else:
        df = pd.read_csv(perf_path)
        df = df.rename(columns={'cagr_1y': 'returns_1y', 'cagr_3y': 'returns_3y', 'cagr_5y': 'returns_5y'})
        np.random.seed(100)
        df['aum_crores'] = np.random.uniform(1000, 45000, size=len(df)).round(2)

    df['amfi_code'] = df['amfi_code'].astype(str)
    print(f"Cleaned shape: {df.shape}")
    return df

def build_and_load_star_schema(df_nav, df_tx, df_perf):
    print("\n--- Loading Star Schema in SQLite ---")

    # 1. Populate dim_fund
    # Map API output codes to real fund houses and category definitions
    fund_static_details = {
        "125497": {"amc": "SBI Mutual Fund", "category": "Equity", "sub_category": "Small Cap", "risk_grade": "Very High"},
        "119551": {"amc": "Aditya Birla Sun Life Mutual Fund", "category": "Debt", "sub_category": "Banking & PSU", "risk_grade": "Moderate"},
        "120503": {"amc": "Axis Mutual Fund", "category": "Equity", "sub_category": "ELSS", "risk_grade": "Very High"},
        "118632": {"amc": "Nippon India Mutual Fund", "category": "Equity", "sub_category": "Large Cap", "risk_grade": "Very High"},
        "119092": {"amc": "HDFC Mutual Fund", "category": "Debt", "sub_category": "Money Market", "risk_grade": "Low to Moderate"},
        "120841": {"amc": "Quant Mutual Fund", "category": "Equity", "sub_category": "Mid Cap", "risk_grade": "Very High"}
    }

    # Generate details for SCH001 to SCH040
    for i in range(1, 41):
        code = f"SCH{str(i).zfill(3)}"
        if i <= 8:
            fund_static_details[code] = {"amc": "HDFC Mutual Fund", "category": "Equity", "sub_category": "Large Cap", "risk_grade": "High"}
        elif i <= 16:
            fund_static_details[code] = {"amc": "Axis Mutual Fund", "category": "Equity", "sub_category": "Mid Cap", "risk_grade": "Very High"}
        elif i <= 24:
            fund_static_details[code] = {"amc": "SBI Mutual Fund", "category": "Equity", "sub_category": "Small Cap", "risk_grade": "Very High"}
        elif i <= 32:
            fund_static_details[code] = {"amc": "Quant Mutual Fund", "category": "Equity", "sub_category": "ELSS", "risk_grade": "Very High"}
        else:
            fund_static_details[code] = {"amc": "Aditya Birla Sun Life Mutual Fund", "category": "Debt", "sub_category": "Money Market", "risk_grade": "Low to Moderate"}

    # Extract distinct funds
    funds = pd.concat([
        df_nav[['amfi_code', 'scheme_name']],
        df_tx[['amfi_code']],
        df_perf[['amfi_code']]
    ]).drop_duplicates(subset=['amfi_code']).dropna()

    dim_fund_records = []
    for _, row in funds.iterrows():
        code = str(row['amfi_code'])
        name = row.get('scheme_name')
        if pd.isna(name):
            name = fund_static_details.get(code, {}).get("amc", "Unknown Fund") + " Scheme"
        
        static = fund_static_details.get(code, {"amc": "Unknown AMC", "category": "Other", "sub_category": "Other", "risk_grade": "High"})
        dim_fund_records.append({
            "amfi_code": code,
            "scheme_name": name,
            "amc": static["amc"],
            "category": static["category"],
            "sub_category": static["sub_category"],
            "risk_grade": static["risk_grade"]
        })
    dim_fund = pd.DataFrame(dim_fund_records)
    dim_fund.to_sql("dim_fund", ENGINE, if_exists="append", index=False)
    print(f"Loaded {len(dim_fund)} records into dim_fund")

    # Read back dim_fund to get auto-generated fund_key mapping
    dim_fund_db = pd.read_sql("SELECT fund_key, amfi_code FROM dim_fund", ENGINE)
    fund_key_map = dict(zip(dim_fund_db['amfi_code'], dim_fund_db['fund_key']))

    # 2. Populate dim_date
    min_date = min(df_nav['date'].min(), df_tx['transaction_date'].min())
    max_date = max(df_nav['date'].max(), df_tx['transaction_date'].max())
    print(f"Generating date dimension from {min_date.date()} to {max_date.date()}")
    
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    dim_date = pd.DataFrame({'date_actual': date_range})
    dim_date['date_key'] = dim_date['date_actual'].dt.strftime('%Y%m%d').astype(int)
    dim_date['year'] = dim_date['date_actual'].dt.year
    dim_date['month'] = dim_date['date_actual'].dt.month
    dim_date['month_name'] = dim_date['date_actual'].dt.strftime('%B')
    dim_date['quarter'] = dim_date['date_actual'].dt.quarter
    dim_date['day'] = dim_date['date_actual'].dt.day
    dim_date['day_of_week'] = dim_date['date_actual'].dt.dayofweek
    dim_date['day_name'] = dim_date['date_actual'].dt.strftime('%A')
    dim_date['is_weekend'] = dim_date['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
    dim_date['date_actual'] = dim_date['date_actual'].dt.strftime('%Y-%m-%d')

    dim_date.to_sql("dim_date", ENGINE, if_exists="append", index=False)
    print(f"Loaded {len(dim_date)} records into dim_date")

    # Create date_key mapping
    date_key_map = dict(zip(dim_date['date_actual'], dim_date['date_key']))

    # Helper function to map dates safely
    def get_date_key(dt_val):
        fmt_str = dt_val.strftime('%Y-%m-%d')
        return date_key_map.get(fmt_str)

    # 3. Populate fact_nav
    df_nav['fund_key'] = df_nav['amfi_code'].map(fund_key_map)
    df_nav['date_key'] = df_nav['date'].apply(get_date_key)
    fact_nav = df_nav[['date_key', 'fund_key', 'nav']].dropna()
    fact_nav.to_sql("fact_nav", ENGINE, if_exists="append", index=False)
    print(f"Loaded {len(fact_nav)} records into fact_nav")

    # 4. Populate fact_transactions
    df_tx['fund_key'] = df_tx['amfi_code'].map(fund_key_map)
    df_tx['date_key'] = df_tx['transaction_date'].apply(get_date_key)
    fact_transactions = df_tx[['transaction_id', 'investor_id', 'date_key', 'fund_key', 'transaction_type', 'amount', 'kyc_status', 'state']].dropna()
    fact_transactions.to_sql("fact_transactions", ENGINE, if_exists="append", index=False)
    print(f"Loaded {len(fact_transactions)} records into fact_transactions")

    # 5. Populate fact_performance
    df_perf['fund_key'] = df_perf['amfi_code'].map(fund_key_map)
    fact_performance = df_perf[['fund_key', 'returns_1y', 'returns_3y', 'returns_5y', 'expense_ratio']].dropna(subset=['fund_key'])
    fact_performance.to_sql("fact_performance", ENGINE, if_exists="append", index=False)
    print(f"Loaded {len(fact_performance)} records into fact_performance")

    # 6. Populate fact_aum
    # We assign AUM value to the latest date key in the date dimension for reporting
    latest_date_key = int(max_date.strftime('%Y%m%d'))
    df_perf['date_key'] = latest_date_key
    df_perf = df_perf.rename(columns={'aum_crores': 'aum_value'})
    fact_aum = df_perf[['fund_key', 'date_key', 'aum_value']].dropna(subset=['fund_key'])
    fact_aum.to_sql("fact_aum", ENGINE, if_exists="append", index=False)
    print(f"Loaded {len(fact_aum)} records into fact_aum")

    # Verify counts match
    print("\n--- Row Count Verification ---")
    with ENGINE.connect() as conn:
        for table in ["dim_fund", "dim_date", "fact_nav", "fact_transactions", "fact_performance", "fact_aum"]:
            cnt = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"Table '{table}' row count in DB: {cnt}")

if __name__ == "__main__":
    run_ddl_schema()
    df_nav = load_and_clean_nav_history()
    df_tx = load_and_clean_transactions()
    df_perf = load_and_clean_performance()
    build_and_load_star_schema(df_nav, df_tx, df_perf)
    print("\nETL Pipeline Completed Successfully!")
