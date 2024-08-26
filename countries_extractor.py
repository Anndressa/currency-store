import requests
import json
from utils import extract_list_from_html_table
from utils import save_json_to_file

COUNTRY_LIST_URL = "https://www.iban.com/country-codes"

def fetch_countries():
    html_content = requests.get(COUNTRY_LIST_URL).content
    table_info = {
        "name": 0,
        "code_alpha2": 1,
        "code_alpha3": 2,
        "code_numeric": 3,
    }
    data = extract_list_from_html_table(html_content, 'myTable', table_info)
    return data

def main():
    save_json_to_file(fetch_countries(), "countries.json")

if __name__ == "__main__":
    main()