import json
import csv
from typing import Dict, List, Tuple

def read_countries_json(file_path: str) -> Dict[str, Dict[str, str]]:
    with open(file_path, 'r') as f:
        data = json.load(f)
    return {country['iso3']: country for country in data['countries']}

def read_output_tsv(file_path: str) -> Dict[str, str]:
    status_dict = {}
    with open(file_path, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)  # Skip header
        for row in reader:
            status_dict[row[2]] = row[4]
    return status_dict

def split_countries(countries: Dict[str, Dict[str, str]], statuses: Dict[str, str]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    successful = []
    unsuccessful = []
    for iso3, status in statuses.items():
        if iso3 in countries:
            if status == 'Success':
                successful.append(countries[iso3])
            else:
                unsuccessful.append(countries[iso3])
    
    # Sort the lists alphabetically by country name
    successful.sort(key=lambda x: x['name'])
    unsuccessful.sort(key=lambda x: x['name'])
    
    return successful, unsuccessful

def write_json_output(data: List[Dict[str, str]], file_path: str):
    with open(file_path, 'w') as f:
        json.dump({"countries": data}, f, indent=2)

def main():
    countries = read_countries_json('./data/all_countries.json')
    statuses = read_output_tsv('./data/all_countries_output.tsv')
    
    successful, unsuccessful = split_countries(countries, statuses)
    
    write_json_output(successful, './list_of_countries.json')
    # write_json_output(unsuccessful, './data/unsuccessful_countries.json')
    
    print(f"Successfully processed {len(successful)} successful countries and {len(unsuccessful)} unsuccessful countries.")

if __name__ == "__main__":
    main()