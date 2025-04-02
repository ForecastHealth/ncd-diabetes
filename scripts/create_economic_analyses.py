#!/usr/bin/env python3

import json
import glob
import os
import argparse
import re

def create_economic_analyses():
    # Initialize list to store economic analyses
    economic_analyses = []
    
    # Dynamically extract countries from scenario filenames
    scenario_files = glob.glob('./scenarios/*.json')
    country_iso3_codes = set()
    
    # Extract unique ISO3 codes from scenario filenames
    for scenario_file in scenario_files:
        filename = os.path.basename(scenario_file)
        match = re.search(r'_([A-Z]{3})\.json$', filename)
        if match:
            country_iso3_codes.add(match.group(1))
    
    country_iso3_codes = sorted(list(country_iso3_codes))
    print(f"Found {len(country_iso3_codes)} countries from scenario files: {', '.join(country_iso3_codes)}")
    
    if not country_iso3_codes:
        print("No countries found in scenario filenames.")
        return
    
    # Ensure economic-analyses directory exists
    os.makedirs('./economic-analyses', exist_ok=True)
    
    # Process each economic analysis template
    template_files = glob.glob('./economic-analyses-templates/*.json')
    if not template_files:
        print("No economic analysis templates found in ./economic-analyses-templates/")
        return
    
    analyses_created = 0
    
    for template_path in template_files:
        try:
            # Load the template
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            template_filename = os.path.basename(template_path)
            template_name = os.path.splitext(template_filename)[0]
            
            baseline_scenario_stub = template_data.get('baseline_name', '')
            comparison_scenario_stub = template_data.get('comparator_name', '')
            
            # For each country, create an analysis record if both scenarios exist
            for iso3 in country_iso3_codes:
                baseline_scenario_file = f"./scenarios/{baseline_scenario_stub}_{iso3}.json"
                comparison_scenario_file = f"./scenarios/{comparison_scenario_stub}_{iso3}.json"
                
                # Check if both scenario files exist for this country
                if os.path.exists(baseline_scenario_file) and os.path.exists(comparison_scenario_file):
                    # Get the actual scenario names and metadata labels from their JSON files
                    try:
                        with open(baseline_scenario_file, 'r', encoding='utf-8') as f:
                            baseline_data = json.load(f)
                        baseline_label = baseline_data.get('metadata', {}).get('label')
                        if not baseline_label:
                            print(f"Warning: Missing metadata.label in {baseline_scenario_file}")
                            # Use filename stem as fallback
                            baseline_label = baseline_scenario_stub
                        baseline_user_friendly_name = f"{baseline_label} - {iso3}"
                    except Exception as e:
                        print(f"Error reading baseline scenario {baseline_scenario_file}: {e}")
                        # Use filename as fallback
                        baseline_user_friendly_name = f"{baseline_scenario_stub}_{iso3}"

                    try:
                        with open(comparison_scenario_file, 'r', encoding='utf-8') as f:
                            comparison_data = json.load(f)
                        comparison_label = comparison_data.get('metadata', {}).get('label')
                        if not comparison_label:
                            print(f"Warning: Missing metadata.label in {comparison_scenario_file}")
                            comparison_label = comparison_scenario_stub
                        comparison_user_friendly_name = f"{comparison_label} - {iso3}"
                    except Exception as e:
                        print(f"Error reading comparison scenario {comparison_scenario_file}: {e}")
                        # Use filename as fallback
                        comparison_user_friendly_name = f"{comparison_scenario_stub}_{iso3}"
                    
                    # Use template name and append country
                    name = template_data.get('name', '')
                    description = template_data.get('description', '')
                    
                    if name:
                        name = f"{name} - {iso3}"
                    
                    if description:
                        description = f"{description} - {iso3}"
                        
                    analysis = {
                        'name': name,
                        'description': description,
                        'baseline_scenario_label': baseline_user_friendly_name,
                        'comparator_scenario_label': comparison_user_friendly_name,
                        'numerator_label': template_data.get('numerator', ''),
                        'denominator_label': template_data.get('denominator', '')
                    }
                    economic_analyses.append(analysis)
                    analyses_created += 1
                else:
                    if not os.path.exists(baseline_scenario_file):
                        print(f"Warning: Baseline scenario file not found for {iso3}: {baseline_scenario_file}")
                    if not os.path.exists(comparison_scenario_file):
                        print(f"Warning: Comparison scenario file not found for {iso3}: {comparison_scenario_file}")
                
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"Error processing template {template_path}: {e}")
    
    # Write output to file
    with open('./list_of_economic_analyses.json', 'w', encoding='utf-8') as f:
        json.dump(economic_analyses, f, indent=4, ensure_ascii=False)
    
    print(f"Created {analyses_created} economic analyses for {len(country_iso3_codes)} countries and {len(template_files)} analysis templates.")
    print(f"Total records: {len(economic_analyses)}")

def get_scenario_name(scenario_file):
    """Extract the scenario name from its JSON file."""
    try:
        with open(scenario_file, 'r', encoding='utf-8') as f:
            scenario_data = json.load(f)
        return scenario_data.get('metadata', {}).get('label', os.path.basename(scenario_file).split('.')[0])
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading scenario file {scenario_file}: {e}")
        return os.path.basename(scenario_file).split('.')[0]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create economic analyses using templates and country-specific scenarios')
    args = parser.parse_args()
    
    create_economic_analyses()