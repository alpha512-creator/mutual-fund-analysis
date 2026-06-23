{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "396ed1f3-b20f-4755-b19e-d9bc8521d67e",
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\n",
    "import pandas as pd\n",
    "import requests"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "f8d2c499-c922-4eef-a5cc-419528f960cc",
   "metadata": {},
   "outputs": [],
   "source": [
    "def fetch_data(scheme_code, scheme_name):\n",
    "\n",
    "    url = f\"https://api.mfapi.in/mf/{scheme_code}\"\n",
    "\n",
    "    print(f\"Fetching data for: {scheme_name} (Code: {scheme_code})\")\n",
    "\n",
    "    try:\n",
    "        response = requests.get(url)\n",
    "        if response.status_code == 200:\n",
    "            json_data = response.json()\n",
    "\n",
    "            if \"data\" in json_data and len(json_data[\"data\"]) > 0:\n",
    "                df = pd.DataFrame(json_data[\"data\"])\n",
    "\n",
    "                df[\"scheme_code\"] = scheme_code\n",
    "                df[\"scheme_name\"] = json_data[\"meta\"].get(\"scheme_name\", scheme_name)\n",
    "\n",
    "                df = df[[\"scheme_code\", \"scheme_name\", \"date\", \"nav\"]]\n",
    "\n",
    "                file_safe_name = scheme_name.lower().replace(\" \", \"_\")\n",
    "                output_path = os.path.join(\"data\", \"raw\", f\"{file_safe_name}.csv\")\n",
    "\n",
    "                df.to_csv(output_path, index=False)\n",
    "            else:\n",
    "                print(f\"data key missing\")\n",
    "        else:\n",
    "            print(f\"Failed connection: {response.status_code}\")\n",
    "\n",
    "    except Exception as e:\n",
    "        print(f\"Fetching Error {scheme_code}: {e}\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "387936db-a047-4f0a-951a-1bcd105d582b",
   "metadata": {},
   "outputs": [],
   "source": [
    "if __name__ == \"__main__\":\n",
    "\n",
    "    fetch_data(\"125497\", \"HDFC Top 100 Direct\")\n",
    "\n",
    "    bluechip_schemes = {\n",
    "        \"119551\": \"SBI Bluechip\",\n",
    "        \"120503\": \"ICICI Bluechip\",\n",
    "        \"118632\": \"Nippon Large Cap\",\n",
    "        \"119092\": \"Axis Bluechip\",\n",
    "        \"120841\": \"Kotak Bluechip\"\n",
    "    }\n",
    "    print(\"\\nFetching Key Bluechip Schemes\")\n",
    "    for code, name in bluechip_schemes.items():\n",
    "        fetch_data(code, name)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.13.9"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
