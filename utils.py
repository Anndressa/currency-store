from bs4 import BeautifulSoup
import html
import json
import xml.etree.ElementTree as ET

def extract_list_from_html_table(html_content, id, selectors):
    soup = BeautifulSoup(html_content, 'lxml')
    table = soup.find('table', id = id)
    rows = table.find_all('tr')

    data = []
    for row in rows:
        cols = row.find_all('td')
        size = len(cols)

        item_data = {}
        for key, position in selectors.items():
            if position >= size : continue
            item_data[key] = html.unescape(cols[position].text.strip())

        if len(item_data) == len(selectors):
            data.append(item_data)

    return data


def extract_from_xml(xml_content, root_tag, item_tag, selectors):
    root = ET.fromstring(xml_content).find(root_tag)
    data = []
    items = root.findall(item_tag)
    for item in items:
        item_data = {}

        for key, tag in selectors.items():
            if(value := item.find(tag)) is not None:
                item_data[key] = value.text

        data.append(item_data)

    return data

def save_json_to_file(data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)