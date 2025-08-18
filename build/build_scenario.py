#!/usr/bin/env python3
"""
Build scenario files by composing component JSONs using YAML configuration.

Usage:
    python3 build_scenario.py configs/asthma_baseline.yml
    python3 build_scenario.py configs/asthma_cr1.yml configs/asthma_cr3.yml
    python3 build_scenario.py --all  # Build all configs in configs/
"""

import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime


def merge_parameters(base_params, new_params):
    """Deep merge parameters, with new_params overwriting base_params."""
    result = base_params.copy()
    for key, value in new_params.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Deep merge for nested dicts
            result[key] = {**result[key], **value}
        else:
            result[key] = value
    return result


def build_scenario_from_config(config_file):
    """Build a scenario from a YAML configuration file."""
    
    # Load the configuration
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Start with empty parameters
    parameters = {}
    
    # Read and merge each component file
    for component_file in config.get('components', []):
        component_path = Path("components") / component_file
        if not component_path.exists():
            raise FileNotFoundError(f"Component file not found: {component_path}")
        
        with open(component_path, 'r') as f:
            component_data = json.load(f)
            parameters = merge_parameters(parameters, component_data)
    
    # Apply any overrides
    overrides = config.get('overrides', {})
    for param_name, override_value in overrides.items():
        if param_name in parameters:
            # Preserve the existing structure, just update the value
            if isinstance(override_value, dict) and 'value' in override_value:
                parameters[param_name]['value'] = override_value['value']
            else:
                # If override is just a value, update it
                parameters[param_name]['value'] = override_value
        else:
            # Add new parameter from override
            parameters[param_name] = override_value
    
    # Build the scenario structure
    metadata = config.get('metadata', {})
    if 'date_created' not in metadata:
        metadata['date_created'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    scenario = {
        "metadata": metadata,
        "parameters": parameters
    }
    
    return scenario, config.get('output', 'output.json')


def main():
    parser = argparse.ArgumentParser(description='Build scenario files from YAML configurations')
    parser.add_argument('configs', nargs='*', 
                        help='YAML configuration file(s) (e.g., configs/asthma_baseline.yml)')
    parser.add_argument('--all', action='store_true',
                        help='Build all configuration files in configs/')
    
    args = parser.parse_args()
    
    if args.all:
        # Build all configs
        config_dir = Path("configs")
        config_files = sorted(config_dir.glob("*.yml"))
        
        if not config_files:
            print("No configuration files found in configs/")
            return
        
        print(f"Building {len(config_files)} scenarios...")
        for config_file in config_files:
            try:
                scenario, output_path = build_scenario_from_config(config_file)
                
                # Write the output
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w') as f:
                    json.dump(scenario, f, indent=2)
                
                print(f"✓ Built {config_file.name} → {output_path}")
                
            except Exception as e:
                print(f"✗ Failed to build {config_file.name}: {e}")
    
    elif args.configs:
        # Build specified config files
        config_files = [Path(c) for c in args.configs]
        
        # Check if all files exist
        missing_files = [f for f in config_files if not f.exists()]
        if missing_files:
            print("Configuration file(s) not found:")
            for f in missing_files:
                print(f"  - {f}")
            return
        
        # Build each config file
        if len(config_files) == 1:
            # Single file - keep original output format for backward compatibility
            config_file = config_files[0]
            scenario, output_path = build_scenario_from_config(config_file)
            
            # Write the output
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(scenario, f, indent=2)
            
            print(f"Scenario built successfully: {output_path}")
            print(f"  Configuration: {config_file}")
            print(f"  Total parameters: {len(scenario['parameters'])}")
        else:
            # Multiple files
            print(f"Building {len(config_files)} scenarios...")
            for config_file in config_files:
                try:
                    scenario, output_path = build_scenario_from_config(config_file)
                    
                    # Write the output
                    output_path = Path(output_path)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_path, 'w') as f:
                        json.dump(scenario, f, indent=2)
                    
                    print(f"✓ Built {config_file.name} → {output_path}")
                    
                except Exception as e:
                    print(f"✗ Failed to build {config_file.name}: {e}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()