import requests
import re
import pprint
import json 
from bs4 import BeautifulSoup
import pycountry

METADATA_URL = "https://en.wikipedia.org/wiki/List_of_circulating_currencies"
SUPPORTED_CURRENCIES_URL = "https://api.frankfurter.app/currencies"

# This dictionary contains the flag country code for currencies available in more than 1 country.
CURRENCY_FLAG_CODES = {
    "EUR": "EU", "USD": "US", "XCD": "AG", "AUD": "AU", "XOF": "SN",
    "INR": "IN", "NOK": "NO", "XAF": "CF", "NZD": "NZ", "ANG": "CW",
    "DKK": "DK", "XPF": "PF", "GBP": "GB", "ZAR": "ZA", "CHF": "CH",
    "MAD": "MA", "SHP": "SH", "RUB": "RU", "BND": "BN", "SGD": "SG", 
    "XCG": "CG", "EGP": "EG", "FKP": "FK", "ILS": "IL", "JOD": "JO",
    "TRY": "TR", 
}

# This dictionary contains exceptions for country names that do not match the ISO codes.
COUNTRY_NAME_EXCEPTIONS = {
    "Cape Verde": "CV", "Gambia, The": "GM", "Korea, North": "KP", "Korea, South": "KR",
    "Macau": "MO", "Turkey": "TR", "Congo, Democratic Republic of the": "CD",
    "South Ossetia": "XO", "Ascension Island": "AC", "Congo, Republic of the": "CG", 
    "Pitcairn Islands": "PN", "Bailiwick of Jersey": "JE", "Bailiwick of Guernsey": "GG",
    "Bahamas, The": "BS", "Sahrawi Republic": "EH", "Northern Cyprus": "XC", 
}

def country_flag(country_code_alpha2):
    """Generates a flag emoji from a two-letter country code (ISO 3166-1 alpha-2)."""
    if not country_code_alpha2 or len(country_code_alpha2) != 2:
        return None
    alpha2_code = country_code_alpha2.upper()
    return ''.join(chr(127397 + ord(char)) for char in alpha2_code)

def get_country_code(country_name):
    """Finds the ISO 3166-1 alpha-2 code for a given country name."""
    
    if country_name in COUNTRY_NAME_EXCEPTIONS:
        return COUNTRY_NAME_EXCEPTIONS[country_name]
    
    try:
        country = pycountry.countries.search_fuzzy(country_name)
        if country:
            return country[0].alpha_2
    except LookupError:
        pass
    return None

def parse_minor_units(text):
    """Parses the 'Fractional unit' text into an integer."""
    clean_text = re.sub(r'\[.*?\]', '', text)
    try:
        return int(clean_text)
    except (ValueError, IndexError):
        return None

def generate_currency_data():
    """Scrapes currency data, correctly handling complex table structures with rowspans."""
    print(f"Fetching data from {METADATA_URL}...")
    try:
        response = requests.get(METADATA_URL, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

    print("Parsing HTML content...")
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', {'class': 'wikitable'})
    if not table:
        print("Error: Could not find the main currency table on the page.")
        return None

    currency_metadata = {}
    last_territory_info = None  # This will hold the context of the current territory

    rows = table.find('tbody').find_all('tr')
    print(f"Found {len(rows)} table rows. Processing with robust logic...")

    for row in rows[1:]:  # Skip header row
        cells = row.find_all(['th', 'td'])
        
        # --- ROBUST LOGIC TO HANDLE ROWSPAN ---
        # A row that defines a new territory has more cells (e.g., 6)
        # A row for a secondary currency under the same territory has fewer (e.g., 5)
        
        if len(cells) >= 6:
            # This is a "master" row defining a new territory.
            territory_name = re.sub(r'\[.*?\]', '', cells[0].get_text(strip=True))
            last_territory_info = {'name': territory_name, 'code': get_country_code(territory_name)}
            currency_cells = cells[1:] # The currency data is in the rest of the cells
        elif len(cells) == 5:
            # This is a secondary currency for the last seen territory.
            currency_cells = cells # The entire row is currency data
        else:
            continue # Skip malformed or irrelevant rows

        # --- EXTRACT CURRENCY DATA FROM THE RELEVANT CELLS ---
        currency_name = re.sub(r'\[.*?\]', '', currency_cells[0].get_text(strip=True))
        symbol = currency_cells[1].get_text(strip=True).split(' ')[0]
        code = currency_cells[2].get_text(strip=True)
        minor_units = parse_minor_units(currency_cells[4].get_text(strip=True))

        if not code or len(code) != 3:
            continue

        # --- POPULATE THE MAIN DICTIONARY ---
        if code not in currency_metadata:
            currency_metadata[code] = {
                'code': code,
                'name': currency_name,
                'symbol': symbol,
                'minor_units': minor_units,
                'territories': []
            }
        
        if last_territory_info:
            currency_metadata[code]['territories'].append(last_territory_info)

    # --- POST-PROCESSING: ADD EMOJIS ---
    print("Enriching data with primary emojis...")
    for code, data in currency_metadata.items():
        flag_code = None
        # 1. Check for a manual override in PRIMARY_COUNTRY_CODES first.
        if code in CURRENCY_FLAG_CODES:
            flag_code = CURRENCY_FLAG_CODES[code]
        # 2. If no in the list, fall back to the first territory's code.
        elif data['territories']:
            flag_code = data['territories'][0]['code']
        data['emoji'] = country_flag(flag_code)

    print(f"Processing complete. Found data for {len(currency_metadata)} currencies.")
    return currency_metadata

def fetch_supported_currencies():
    """Fetches the set of currency codes supported by the exchange rate API."""
    print(f"Fetching supported currencies from {SUPPORTED_CURRENCIES_URL}...")
    try:
        response = requests.get(SUPPORTED_CURRENCIES_URL)
        response.raise_for_status()
        data = response.json()
        # The API returns a dict like {"AED": "United Arab Emirates Dirham", ...}
        # We only need the keys (the currency codes).
        supported_codes = set(data.keys())
        print(f"Successfully fetched {len(supported_codes)} supported currency codes from Frankfurter.")
        return supported_codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching supported currencies from the API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from the API: {e}")
        return None

if __name__ == '__main__':
    # 1. Get the list of currencies supported by the exchange rate API
    currency_codes = fetch_supported_currencies()
    if not currency_codes:
        print("Aborting: Could not get supported currencies from the API.")
        exit()

    # 2. Generate the currency metadata
    print("Generating currency metadata...")
    generated_data = generate_currency_data()
    if not generated_data:
        print("Aborting: No currency data was generated.")
        exit()

    # 3. Filter the generated data to only include currencies supported by the API
    filtered_metadata = {code: data for code, data in generated_data.items() if code in currency_codes}
    print(f"Filtered data to {len(generated_data)} currencies supported by the API.")
    
    output_filename = "currencies.json"
    print(f"Writing data to {output_filename}...")
    with open(output_filename, 'w', encoding='utf-8') as f:
        # Use ensure_ascii=False to correctly save emojis and non-Latin characters
        json.dump(filtered_metadata, f, ensure_ascii=False, indent=4)
        
    print(f"Successfully created {output_filename}!")