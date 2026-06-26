-- 10 Analytical SQL Queries for Mutual Fund Star Schema

-- Query 1: Top 5 funds by AUM
-- Business significance: Identifies the largest funds in terms of assets under management.
SELECT f.scheme_name, f.amc, a.aum_value AS aum_crores
FROM fact_aum a
JOIN dim_fund f ON a.fund_key = f.fund_key
ORDER BY a.aum_value DESC
LIMIT 5;


-- Query 2: Average NAV per month per fund
-- Business significance: Tracks historical trends of Net Asset Value on a monthly basis.
SELECT f.scheme_name, d.year, d.month_name, ROUND(AVG(n.nav), 4) AS avg_nav
FROM fact_nav n
JOIN dim_fund f ON n.fund_key = f.fund_key
JOIN dim_date d ON n.date_key = d.date_key
GROUP BY f.scheme_name, d.year, d.month
ORDER BY f.scheme_name, d.year, d.month;


-- Query 3: SIP YoY growth
-- Business significance: Shows the yearly performance growth of recurring monthly SIPs.
WITH annual_sip AS (
    SELECT d.year, SUM(t.amount) AS total_sip_amount
    FROM fact_transactions t
    JOIN dim_date d ON t.date_key = d.date_key
    WHERE t.transaction_type = 'SIP'
    GROUP BY d.year
)
SELECT curr.year, 
       curr.total_sip_amount,
       prev.total_sip_amount AS prev_year_sip_amount,
       CASE 
           WHEN prev.total_sip_amount IS NOT NULL THEN 
               ROUND(((curr.total_sip_amount - prev.total_sip_amount) / prev.total_sip_amount) * 100, 2)
           ELSE NULL 
       END AS yoy_growth_pct
FROM annual_sip curr
LEFT JOIN annual_sip prev ON curr.year = prev.year + 1
ORDER BY curr.year;


-- Query 4: Transactions by state
-- Business significance: Highlights regional distribution of mutual fund investments.
SELECT state, COUNT(*) AS txn_count, ROUND(SUM(amount), 2) AS total_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_amount DESC;


-- Query 5: Funds with expense_ratio < 1%
-- Business significance: Filters low-cost index and direct mutual funds for cost-sensitive investors.
SELECT f.scheme_name, f.amc, ROUND(p.expense_ratio * 100, 2) AS expense_ratio_pct
FROM fact_performance p
JOIN dim_fund f ON p.fund_key = f.fund_key
WHERE p.expense_ratio < 0.01
ORDER BY p.expense_ratio ASC;


-- Query 6: Total transaction volume and count by transaction type
-- Business significance: Details investor channel preferences (SIP vs Lumpsum vs Redemption).
SELECT transaction_type, COUNT(*) AS txn_count, ROUND(SUM(amount), 2) AS total_amount
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_amount DESC;


-- Query 7: Funds with the highest 3-Year returns
-- Business significance: Shows mid-term growth performance rankings across the portfolio.
SELECT f.scheme_name, f.amc, p.returns_3y
FROM fact_performance p
JOIN dim_fund f ON p.fund_key = f.fund_key
ORDER BY p.returns_3y DESC;


-- Query 8: Daily NAV spread volatility index (Spread between min/max NAV relative to average)
-- Business significance: Visualizes NAV volatility spread to analyze historical standard deviation proxy.
SELECT f.scheme_name, 
       ROUND(MIN(n.nav), 2) AS min_nav, 
       ROUND(MAX(n.nav), 2) AS max_nav, 
       ROUND(AVG(n.nav), 2) AS avg_nav,
       ROUND(((MAX(n.nav) - MIN(n.nav)) / AVG(n.nav)) * 100, 2) AS nav_spread_volatility_pct
FROM fact_nav n
JOIN dim_fund f ON n.fund_key = f.fund_key
GROUP BY f.scheme_name
ORDER BY nav_spread_volatility_pct DESC;


-- Query 9: KYC compliance rate by transaction type
-- Business significance: Identifies compliance verification bottlenecks across product types.
SELECT transaction_type,
       COUNT(*) AS total_txns,
       SUM(CASE WHEN kyc_status = 'Verified' THEN 1 ELSE 0 END) AS verified_txns,
       ROUND(CAST(SUM(CASE WHEN kyc_status = 'Verified' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) * 100, 2) AS kyc_compliance_rate_pct
FROM fact_transactions
GROUP BY transaction_type;


-- Query 10: Holiday/Weekend (Date dimension check) vs. Weekday transaction activity analysis
-- Business significance: Evaluates investor behaviour on market holidays/weekends.
SELECT CASE WHEN d.is_weekend = 1 THEN 'Weekend/Holiday' ELSE 'Weekday' END AS day_classification,
       COUNT(t.transaction_id) AS txn_count,
       ROUND(SUM(t.amount), 2) AS total_amount,
       ROUND(AVG(t.amount), 2) AS avg_amount
FROM fact_transactions t
JOIN dim_date d ON t.date_key = d.date_key
GROUP BY d.is_weekend;
