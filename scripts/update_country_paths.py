import json
import glob
import os
from pathlib import Path
import argparse

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def update_country_paths(keywords):
    # Load default scenario paths
    default_scenario_path = Path('./scenarios/default_scenario.json')
    default_scenario = load_json(default_scenario_path)
    default_paths = default_scenario['parameters']['Country']['paths']

    # Process each keyword
    for keyword in keywords:
        # Find all matching scenario files
        scenario_pattern = f'./scenarios/{keyword}*.json'
        scenario_files = glob.glob(scenario_pattern)

        # Remove default_scenario.json from the list if it matches the pattern
        if default_scenario_path in map(Path, scenario_files):
            scenario_files.remove(str(default_scenario_path))

        print(f"\nKeyword '{keyword}': Found {len(scenario_files)} scenario files to update")

        # Process each scenario file
        for scenario_file in scenario_files:
            print(f"Processing {scenario_file}")
            
            # Load scenario
            scenario = load_json(scenario_file)
            
            # Ensure the required structure exists
            if 'parameters' not in scenario:
                scenario['parameters'] = {}
            if 'Country' not in scenario['parameters']:
                scenario['parameters']['Country'] = {'paths': []}
            if 'paths' not in scenario['parameters']['Country']:
                scenario['parameters']['Country']['paths'] = []

            # Get current paths
            current_paths = scenario['parameters']['Country']['paths']
            
            # Add missing paths
            paths_added = 0
            for path in default_paths:
                if path not in current_paths:
                    current_paths.append(path)
                    paths_added += 1

            print(f"Added {paths_added} new paths")

            # Save updated scenario
            save_json(scenario, scenario_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update country paths in scenario files')
    parser.add_argument('keywords', nargs='+', help='One or more keywords to match scenario files')
    
    args = parser.parse_args()
    update_country_paths(args.keywords) 