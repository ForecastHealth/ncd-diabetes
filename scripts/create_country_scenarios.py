#!/usr/bin/env python3

import argparse
import json
import glob
import os
import sys

def create_country_scenarios(countries_file_path=None):
    # Initialize counter for created scenarios
    scenarios_created = 0
    
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
            sys.exit(1)
    else:
        print(f"Countries file not found: {countries_file_path}")
        sys.exit(1)
    
    # Ensure scenarios directory exists
    os.makedirs('./scenarios', exist_ok=True)
    
    # Process each scenario template
    template_files = glob.glob('./scenario-templates/*.json')
    if not template_files:
        print("No scenario templates found in ./scenario-templates/")
        sys.exit(1)
    
    for template_path in template_files:
        try:
            # Load the template
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            template_filename = os.path.basename(template_path)
            template_name = os.path.splitext(template_filename)[0]
            
            # For each country, create a scenario
            for iso3 in country_iso3_codes:
                # Create a deep copy of the template
                scenario_data = json.loads(json.dumps(template_data))
                
                # Check if the template has a Country parameter
                if 'parameters' in scenario_data and 'Country' in scenario_data['parameters']:
                    # Replace the value with the country's ISO3 code
                    scenario_data['parameters']['Country']['value'] = iso3
                    
                    # Create the output filename
                    output_filename = f"{template_name}_{iso3}.json"
                    output_path = os.path.join('./scenarios', output_filename)
                    
                    # Write the updated scenario to file
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(scenario_data, f, indent=2, ensure_ascii=False)
                    
                    scenarios_created += 1
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"Error processing template {template_path}: {e}")
    
    print(f"Created {scenarios_created} country-specific scenarios for {len(country_iso3_codes)} countries and {len(template_files)} scenario templates.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create country-specific scenarios from templates')
    parser.add_argument('--countries', '-c', dest='countries_file', 
                        help='Path to the JSON file containing country data (default: ./list_of_countries.json)')
    args = parser.parse_args()
    
    create_country_scenarios(args.countries_file)