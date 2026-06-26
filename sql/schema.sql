-- SQLite Star Schema definition for Mutual Fund Analytics

-- Drop tables if they exist to allow clean re-runs
DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_fund;

-- 1. Dimension: dim_fund
CREATE TABLE dim_fund (
    fund_key INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code TEXT UNIQUE NOT NULL,
    scheme_name TEXT NOT NULL,
    amc TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    risk_grade TEXT
);

-- 2. Dimension: dim_date
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY, -- format: YYYYMMDD
    date_actual TEXT NOT NULL,    -- format: YYYY-MM-DD
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    quarter INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name TEXT NOT NULL,
    is_weekend INTEGER NOT NULL   -- 0 = No, 1 = Yes
);

-- 3. Fact: fact_nav
CREATE TABLE fact_nav (
    nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_key INTEGER NOT NULL,
    fund_key INTEGER NOT NULL,
    nav REAL NOT NULL,
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (fund_key) REFERENCES dim_fund(fund_key)
);

-- 4. Fact: fact_transactions
CREATE TABLE fact_transactions (
    transaction_id TEXT PRIMARY KEY,
    date_key INTEGER NOT NULL,
    fund_key INTEGER NOT NULL,
    transaction_type TEXT NOT NULL, -- SIP, Lumpsum, Redemption
    amount REAL NOT NULL,
    kyc_status TEXT NOT NULL,       -- Verified, Pending, Failed
    state TEXT NOT NULL,
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (fund_key) REFERENCES dim_fund(fund_key)
);

-- 5. Fact: fact_performance
CREATE TABLE fact_performance (
    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_key INTEGER NOT NULL,
    returns_1y REAL,
    returns_3y REAL,
    returns_5y REAL,
    expense_ratio REAL,            -- As decimal (e.g. 0.015 for 1.5%)
    FOREIGN KEY (fund_key) REFERENCES dim_fund(fund_key)
);

-- 6. Fact: fact_aum
CREATE TABLE fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    aum_value REAL NOT NULL,        -- AUM in Crores INR
    FOREIGN KEY (fund_key) REFERENCES dim_fund(fund_key),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);
