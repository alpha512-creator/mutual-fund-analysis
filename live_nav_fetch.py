import os
import pandas as pd
import requests

def fetch_data(scheme_code, scheme_name):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    print(f"Fetching data for: {scheme_name} (Code: {scheme_code})")

    try:
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()

            if "data" in json_data and len(json_data["data"]) > 0:
                df = pd.DataFrame(json_data["data"])
                df["scheme_code"] = scheme_code
                df["scheme_name"] = json_data["meta"].get("scheme_name", scheme_name)
                df = df[["scheme_code", "scheme_name", "date", "nav"]]

                file_safe_name = scheme_name.lower().replace(" ", "_")
                output_path = os.path.join("data", "raw", f"{file_safe_name}.csv")
                
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                df.to_csv(output_path, index=False)
                print(f"Successfully saved to {output_path}")
            else:
                print(f"Data key missing or empty for code {scheme_code}")
        else:
            print(f"Failed connection: {response.status_code}")

    except Exception as e:
        print(f"Fetching Error {scheme_code}: {e}")

if __name__ == "__main__":
    # Fetch HDFC Top 100
    fetch_data("125497", "HDFC Top 100 Direct")

    # Fetch bluechip schemes
    bluechip_schemes = {
        "119551": "SBI Bluechip",
        "120503": "ICICI Bluechip",
        "118632": "Nippon Large Cap",
        "119092": "Axis Bluechip",
        "120841": "Kotak Bluechip"
    }
    
    print("\nFetching Key Bluechip Schemes")
    for code, name in bluechip_schemes.items():
        fetch_data(code, name)
