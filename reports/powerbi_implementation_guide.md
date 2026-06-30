# Power BI Dashboard Implementation & DAX Guide

This guide details the step-by-step connectivity, data relationships, DAX formulas, and visual configurations required to implement the **Bluestock Mutual Fund Analytics Dashboard** in Power BI Desktop.

---

## 🎨 Bluestock Color Theme Design Tokens
To apply the Bluestock visual design, save the following theme as a JSON file and import it via **View > Themes > Browse for themes**:

```json
{
  "name": "Bluestock Dark Slate",
  "dataColors": ["#00B4D8", "#0077B6", "#90E0EF", "#03045E", "#FFB703", "#FB8500", "#E63946"],
  "background": "#0F172A",
  "foreground": "#F8FAFC",
  "tableAccent": "#00B4D8"
}
```

---

## 🔌 1. Data Connection & Modeling

### Data Import
* **Option A: Connect via SQLite ODBC**:
  1. Install the SQLite ODBC Driver on your system.
  2. In Power BI, select **Get Data > ODBC > DSN = SQLite3 Datasource** and browse to the path: `sql/mutual_funds.db`.
  3. Load all 6 database tables: `dim_fund`, `dim_date`, `fact_nav`, `fact_transactions`, `fact_performance`, and `fact_aum`.
* **Option B: Connect via Cleaned CSVs (Alternative)**:
  * Select **Get Data > Text/CSV** and load all datasets from the `data/raw/` or `data/processed/` directories.

### Relational Model Schema (Star Schema)
Configure relationships in the **Model View** using a single-directional `1-to-many (1:*)` setup:

1. **`dim_fund` Relationships**:
   * `dim_fund[amfi_code]` `(1)` ➔ `(*)` `fact_nav[amfi_code]`
   * `dim_fund[amfi_code]` `(1)` ➔ `(*)` `fact_transactions[amfi_code]`
   * `dim_fund[amfi_code]` `(1)` ➔ `(*)` `fact_performance[amfi_code]`
   * `dim_fund[amfi_code]` `(1)` ➔ `(*)` `fact_aum[amfi_code]`
2. **`dim_date` Relationships**:
   * `dim_date[date_key]` `(1)` ➔ `(*)` `fact_nav[date_key]`
   * `dim_date[date_key]` `(1)` ➔ `(*)` `fact_transactions[date_key]`
   * `dim_date[date_key]` `(1)` ➔ `(*)` `fact_aum[date_key]`

---

## 🧮 2. DAX Calculations & Measures

Create a dedicated measures table (e.g., `_Measures`) and implement the following formulas:

### KPI Metrics (Page 1)
```dax
-- 1. Total Assets Under Management (AUM) in Lakh Crores
Total AUM (Lakh Cr) = 
DIVIDE(SUM(fact_aum[aum_value]), 10)

-- 2. Monthly SIP Inflow (in Crores)
SIP Inflow (Cr) = 
DIVIDE(
    CALCULATE(
        SUM(fact_transactions[amount]), 
        fact_transactions[transaction_type] = "SIP"
    ), 
    10000000
)

-- 3. Total Folios (in Crores)
Total Folios (Cr) = 
MAX(folio_growth[folio_count_crores])

-- 4. Active Scheme Registry Count
Active Schemes = 
DISTINCTCOUNT(dim_fund[amfi_code])
```

### Risk & Performance Analytics (Page 2)
```dax
-- 5. Trailing Returns (3-Year CAGR)
3Yr CAGR = 
AVERAGE(fact_performance[returns_3y])

-- 6. Annualized Daily return Volatility
Volatility = 
STDEV.S(fact_returns[daily_return]) * SQRT(252)

-- 7. Sharpe Ratio
Sharpe Ratio = 
DIVIDE([3Yr CAGR] - 6.5, [Volatility] * 100)

-- 8. Downside Deviation (Negative return standard deviation)
Downside Deviation = 
VAR DailyRf = DIVIDE(0.065, 252)
VAR DownsideReturns = 
    FILTER(
        fact_returns, 
        fact_returns[daily_return] < DailyRf
    )
RETURN
STDEV.S(SELECTCOLUMNS(DownsideReturns, "Ret", fact_returns[daily_return])) * SQRT(252)

-- 9. Sortino Ratio
Sortino Ratio = 
DIVIDE([3Yr CAGR] - 6.5, [Downside Deviation] * 100)
```

### Benchmarks & Regressions
```dax
-- 10. Alpha (Excess intercept return)
Alpha = 
AVERAGE(fact_performance[alpha])

-- 11. Beta (Market sensitivity slope)
Beta = 
AVERAGE(fact_performance[beta])

-- 12. Annualized Tracking Error
Tracking Error = 
STDEVX.P(
    fact_nav, 
    [Daily Fund Return] - [Daily Nifty 100 Return]
) * SQRT(252)
```

---

## 📊 3. Visualizations Configuration By Page

### Page 1 — Industry Overview
* **Cards (KPIs)**: Create 4 KPI cards utilizing the measures `[Total AUM (Lakh Cr)]`, `[SIP Inflow (Cr)]`, `[Total Folios (Cr)]`, and `[Active Schemes]`.
* **Line Chart**: 
  * *X-axis:* `dim_date[date_actual]`
  * *Y-axis:* `Total AUM (Lakh Cr)` (Tracks industry growth 2022–2025).
* **Bar Chart**: 
  * *X-axis:* `AUM (Lakh Cr)`
  * *Y-axis:* `dim_fund[amc]` (Horizontal bar ordered descending to show SBI at the top).

### Page 2 — Fund Performance
* **Scatter Plot**: 
  * *X-axis:* `3Yr CAGR` (Returns)
  * *Y-axis:* `Volatility` (Risk)
  * *Details:* `dim_fund[scheme_name]`
  * *Size:* `Total AUM (Lakh Cr)`
* **Scorecard Table**: Columns `[final_rank]`, `[scheme_name]`, `[amc]`, `[3Yr CAGR]`, `[Sharpe Ratio]`, `[Sortino Ratio]`, `[Alpha]`, `[Beta]`, and `[max_drawdown]`.
* **Line Chart**: Daily price trend comparing `fact_nav[nav]` vs Nifty indices (`nifty_50` and `nifty_100`).
* **Slicers Panel**: `dim_fund[amc]`, `dim_fund[category]`, `dim_fund[plan]`.

### Page 3 — Investor Analytics
* **State Bar Chart**: 
  * *X-axis:* `SUM(fact_transactions[amount])`
  * *Y-axis:* `fact_transactions[state]` (Horizontal bar representing geographic volume).
* **Donut Chart**: 
  * *Legend:* `fact_transactions[transaction_type]`
  * *Values:* `COUNT(fact_transactions[transaction_id])` (SIP/Lumpsum/Redemption split).
* **Demographics Bar Chart**: 
  * *X-axis:* `dim_investor[age_group]`
  * *Y-axis:* `AVERAGE(fact_transactions[amount])` (Age group vs average SIP amount).
* **Slicers**: `fact_transactions[state]`, `dim_investor[age_group]`, `fact_transactions[city_tier]`.

### Page 4 — SIP & Market Trends
* **Line & Clustered Column Chart (Dual-Axis)**:
  * *Shared X-axis:* `dim_date[date_actual]` (aggregated monthly)
  * *Column Values:* `SIP Inflow (Cr)` (representing the monthly SIP inflow trend)
  * *Line Values:* `AVERAGE(benchmarks[nifty_50])` (representing Nifty 50 movement overlay)
* **Heatmap Grid**: Heatmap visual displaying months on X-axis, categories on Y-axis, and net inflow as the color saturation.

---

## 🔄 4. Interactivity & Advanced Setup

### Drill-Through Configuration
1. Create a detailed target page named **NAV Detail**.
2. Drag `dim_fund[scheme_name]` or `dim_fund[amfi_code]` into the **Drill-through filters** well.
3. Configure the main scorecard table on Page 2 to enable right-click drill-through, transporting users to the detailed NAV page showing historical NAV daily movements.

### Tooltips
* Enable custom tooltips across all scatter plots and heatmaps, mapping key fund stats (`AUM`, `Sharpe`, `AMC`) to hover states.
