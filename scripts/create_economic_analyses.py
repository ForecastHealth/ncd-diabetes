#!/usr/bin/env python3

import json
import glob
import os
import argparse

def create_economic_analyses(countries_file_path=None):
    # Initialize list to store economic analyses
    economic_analyses = []
    
    # Check if countries file exists
    country_iso3_codes = []
    countries_file_exists = False
    
    # Use provided countries file or default to hardcoded path
    if countries_file_path is None:
        countries_file_path = './list_of_countries.json'
    
    if os.path.exists(countries_file_path):
        countries_file_exists = True
        try:
            # Load countries data
            with open(countries_file_path, 'r', encoding='utf-8') as f:
                countries_data = json.load(f)
            
            # Extract ISO3 codes
            country_iso3_codes = [country['iso3'] for country in countries_data['countries']]
            print(f"Using countries from: {countries_file_path}")
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"Error processing countries file: {e}")
            countries_file_exists = False
    else:
        print(f"Countries file not found: {countries_file_path}")
    
    # Process each economic analysis file
    cea_files = glob.glob('./economic-analyses/*.json')
    for file_path in cea_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cea_data = json.load(f)
            
            if countries_file_exists and country_iso3_codes:
                # For each country, create an analysis record
                for iso3 in country_iso3_codes:
                    analysis = {
                        'name': cea_data.get('name', ''),
                        'description': cea_data.get('description', ''),
                        'country_override': iso3,
                        'baseline_scenario_label': cea_data.get('baseline_name', ''),
                        'comparator_scenario_label': cea_data.get('comparator_name', ''),
                        'numerator_label': cea_data.get('numerator', ''),
                        'denominator_label': cea_data.get('denominator', '')
                    }
                    economic_analyses.append(analysis)
            else:
                # Create a single analysis with empty country_override
                analysis = {
                    'name': cea_data.get('name', ''),
                    'description': cea_data.get('description', ''),
                    'country_override': '',
                    'baseline_scenario_label': cea_data.get('baseline_name', ''),
                    'comparator_scenario_label': cea_data.get('comparator_name', ''),
                    'numerator_label': cea_data.get('numerator', ''),
                    'denominator_label': cea_data.get('denominator', '')
                }
                economic_analyses.append(analysis)
                
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"Error processing {file_path}: {e}")
    
    # Write output to file
    with open('./list_of_economic_analyses.json', 'w', encoding='utf-8') as f:
        json.dump(economic_analyses, f, indent=4, ensure_ascii=False)
    
    print(f"Created economic analyses for {len(country_iso3_codes)} countries and {len(cea_files)} analysis types.")
    print(f"Total records: {len(economic_analyses)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create economic analyses using a countries JSON file')
    parser.add_argument('--countries', '-c', dest='countries_file', 
                        help='Path to the JSON file containing country data (default: ./list_of_countries.json)')
    args = parser.parse_args()
    
    create_economic_analyses(args.countries_file)
