import os
import pandas as pd
import sqlite3
import argparse

def get_recommendations(risk_appetite):
    # Normalize input
    risk = str(risk_appetite).strip().lower()
    
    # Map input risk appetite to database risk_grade values
    # low -> Low to Moderate, Moderate
    # moderate -> High
    # high -> Very High
    if risk == 'low':
        target_grades = ["Low to Moderate", "Moderate"]
    elif risk == 'moderate':
        target_grades = ["High"]
    elif risk == 'high':
        target_grades = ["Very High"]
    else:
        print(f"Unknown risk appetite: '{risk_appetite}'. Defaulting to 'Moderate'.")
        target_grades = ["High"]
        risk = 'moderate'

    db_path = "sql/mutual_funds.db"
    scorecard_path = "data/processed/fund_scorecard.csv"
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}. Please run data_cleaning_etl.py first.")
    if not os.path.exists(scorecard_path):
        raise FileNotFoundError(f"Fund scorecard not found at {scorecard_path}. Please run Performance_Analytics.ipynb first.")

    # 1. Query schemes details from SQLite dim_fund
    conn = sqlite3.connect(db_path)
    query_funds = "SELECT amfi_code, scheme_name, amc, category, sub_category, risk_grade FROM dim_fund"
    df_funds = pd.read_sql(query_funds, conn)
    conn.close()

    # Filter by risk grade
    df_filtered_funds = df_funds[df_funds['risk_grade'].isin(target_grades)]

    # 2. Load performance metrics from fund_scorecard.csv
    df_scorecard = pd.read_csv(scorecard_path)
    df_scorecard['amfi_code'] = df_scorecard['amfi_code'].astype(str)
    
    # Merge
    df_rec = df_filtered_funds.merge(df_scorecard[['amfi_code', 'cagr_3y', 'sharpe_ratio', 'expense_ratio']], on='amfi_code')
    
    # Sort by Sharpe Ratio descending and get Top 3
    df_rec = df_rec.sort_values(by='sharpe_ratio', ascending=False).head(3)
    
    # Format columns for presentation
    df_rec['cagr_3y'] = df_rec['cagr_3y'].map(lambda x: f"{x:.2f}%")
    df_rec['sharpe_ratio'] = df_rec['sharpe_ratio'].map(lambda x: f"{x:.3f}")
    df_rec['expense_ratio'] = df_rec['expense_ratio'].map(lambda x: f"{x*100:.2f}%")
    
    return df_rec, risk.capitalize()

def main():
    parser = argparse.ArgumentParser(description="Bluestock Mutual Fund Recommender Tool")
    parser.add_argument('--risk', type=str, choices=['Low', 'Moderate', 'High'], 
                        help="Your risk appetite (Low / Moderate / High)")
    args = parser.parse_args()

    risk_input = args.risk
    if not risk_input:
        print("--- Bluestock Mutual Fund Recommender ---")
        risk_input = input("Enter your risk appetite (Low / Moderate / High): ").strip()

    try:
        recommendations, risk_label = get_recommendations(risk_input)
        
        print("\n" + "="*80)
        print(f" TOP 3 RECOMMENDED FUNDS FOR RISK PROFILE: {risk_label.upper()} ")
        print("="*80)
        
        if len(recommendations) == 0:
            print("No matching schemes found in the database.")
        else:
            cols_to_print = ['amfi_code', 'scheme_name', 'risk_grade', 'cagr_3y', 'sharpe_ratio', 'expense_ratio']
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)
            print(recommendations[cols_to_print].to_string(index=False))
            
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"Error during recommendation generation: {e}")

if __name__ == "__main__":
    main()
