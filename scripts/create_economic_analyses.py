#!/usr/bin/env python3

import json
import glob
import os

def create_economic_analyses():
    # Initialize list to store economic analyses
    economic_analyses = []
    
    # Check if countries file exists
    country_iso3_codes = []
    countries_file_exists = os.path.exists('./list_of_countries.json')
    
    if countries_file_exists:
        try:
            # Load countries data
            with open('./list_of_countries.json', 'r', encoding='utf-8') as f:
                countries_data = json.load(f)
            
            # Extract ISO3 codes
            country_iso3_codes = [country['iso3'] for country in countries_data['countries']]
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"Error processing countries file: {e}")
            countries_file_exists = False
    
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
    create_economic_analyses() 
