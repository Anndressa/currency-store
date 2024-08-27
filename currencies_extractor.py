import requests
from countries_extractor import fetch_countries
from utils import *

CURRENCY_LIST_URL = "https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-one.xml"
CURRENCY_SYMBOLS_URL = "https://www.currencyremitapp.com/world-currency-symbols"
HEADERS_TO_CURRENCY_SYMBOLS_PAGE = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

COUNTRIES_NAME_EXCEPTIONS = {
    "KOREA (THE DEMOCRATIC PEOPLE’S REPUBLIC OF)": "KP",
    "LAO PEOPLE’S DEMOCRATIC REPUBLIC (THE)": "LA",
    "NORTH MACEDONIA": "MK",
    "TÜRKİYE": "TR",
}

FLAG_EXCEPTIONS = {
    "EUR": "EU",
    "USD": "US",
    "XCD": "AG",
    "AUD": "AU",
    "XOF": "CF",
    "INR": "IN",
    "NOK": "NO",
    "XAF": "CF",
    "NZD": "NZ",
    "ANG": "NL",
    "DKK": "DK",
    "XPF": "PF",
    "GBP": "GB",
    "ZAR": "ZA",
    "CHF": "CH",
    "MAD": "MA"
}

def fetch_currencies_by_country():
    xml_content = requests.get(CURRENCY_LIST_URL).content

    node_info = {
        "name": "CcyNm",
        "country": "CtryNm",
        "code_alpha3": "Ccy",
        "code_numeric": "CcyNbr",
        "minor_units": "CcyMnrUnts",
    }
    return extract_from_xml(xml_content, 'CcyTbl', 'CcyNtry', node_info)

def fetch_currencies_symbols():
    html_content = requests.get(CURRENCY_SYMBOLS_URL, headers = HEADERS_TO_CURRENCY_SYMBOLS_PAGE).content
    table_info = {
        "code_alpha3": 3,
        "symbol": 4,
    }
    return extract_list_from_html_table(html_content,'', table_info)

def fetch_currencies():
    data = fetch_currencies_by_country()
    countries = fetch_countries()
    symbols = fetch_currencies_symbols()
    currencies = {}
    
    for item in data:
        currency_code = item['code_alpha3'] if 'code_alpha3' in item else None
        if currency_code is not None:
            country = find_country(countries, item['country'])
            if country is not None:
                if currency_code not in currencies:
                    symbol = find_item(symbols, 'code_alpha3', currency_code)
                    currencies[currency_code] = { 
                        "code_alpha3": currency_code, 
                        "code_numeric": int(item['code_numeric']),
                        "symbol": symbol['symbol'] if symbol is not None else '',
                        "name": item['name'],
                        "minor_units": int(item['minor_units']) if item['minor_units'] != 'N.A.' else 0,
                        "countries": [],
                    }
        
                currencies[currency_code]['countries'].append(country['code_alpha2']) 

    for currency in currencies.values():
        flag = currency_flag(currency)
        if flag is not None: currency['flag'] = flag 

    return [item for item in currencies.values()]

def find_country(countries, country_name):
    if country_name in COUNTRIES_NAME_EXCEPTIONS:
        return find_item(countries, "code_alpha2", COUNTRIES_NAME_EXCEPTIONS[country_name])
    else:
        return find_item(countries, "name", country_name)

def find_item(items, key, value):
    return next((item for item in items if key in item and item[key].casefold() == value.casefold()), None)

def currency_flag(currency):
    currency_code = currency['code_alpha3']
    if currency_code in FLAG_EXCEPTIONS: 
        return country_flag(FLAG_EXCEPTIONS[currency_code]) 
    if(len(currency['countries']) == 1): 
        return country_flag(currency['countries'][0])
    return None

def country_flag(country_code_alpha2):
    alpha2_code = country_code_alpha2.upper()
    return ''.join(chr(127397 + ord(char)) for char in alpha2_code)

def main():
    save_json_to_file(fetch_currencies(), "currencies.json")
    
if __name__ == "__main__":
    main()