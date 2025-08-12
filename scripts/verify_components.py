#!/usr/bin/env python3

import json
import argparse
import re
import sys
from pathlib import Path

def extract_node_and_link_info(model_data):
    """Extract all node and link IDs with their labels from the model"""
    id_to_label = {}
    
    # Extract node IDs and labels
    if 'nodes' in model_data:
        for node in model_data['nodes']:
            if 'id' in node:
                label = node.get('label', node['id'])  # Use label if available, otherwise use ID
                id_to_label[node['id']] = label
    
    # Extract link IDs and labels
    if 'links' in model_data:
        for link in model_data['links']:
            if 'id' in link:
                label = link.get('label', link['id'])  # Use label if available, otherwise use ID
                id_to_label[link['id']] = label
    
    return id_to_label

def extract_ids_from_jsonpath(jsonpath_expression):
    """Extract ID values from JSONPath expressions like $.nodes[?(@.id=='SomeId')]"""
    # Pattern to match @.id=='value' or @.id=="value"
    pattern = r"@\.id\s*==\s*['\"]([^'\"]+)['\"]"
    matches = re.findall(pattern, jsonpath_expression)
    return matches

def verify_component_file(component_file, id_to_label):
    """Verify a single component file against model IDs"""
    print(f"\n=== {component_file} ===")
    
    try:
        with open(component_file, 'r') as f:
            component_data = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not read component file: {e}")
        return False
    
    all_valid = True
    
    for param_name, param_config in component_data.items():
        if not isinstance(param_config, dict) or 'paths' not in param_config:
            continue
            
        print(f"\n{param_name}:")
        
        for path in param_config['paths']:
            # Extract referenced IDs from this path
            referenced_ids = extract_ids_from_jsonpath(path)
            
            if not referenced_ids:
                print(f"  {path} → [no ID reference]")
                continue
                
            for ref_id in referenced_ids:
                if ref_id in id_to_label:
                    label = id_to_label[ref_id]
                    print(f"  {ref_id} → {label}")
                else:
                    print(f"  {ref_id} → *** NOT FOUND ***")
                    all_valid = False
    
    return all_valid

def main():
    parser = argparse.ArgumentParser(
        description="Verify that component JSONPath expressions reference valid model IDs"
    )
    parser.add_argument(
        '--model', 
        required=True, 
        help='Path to model JSON file (e.g., model.json)'
    )
    parser.add_argument(
        '--components', 
        nargs='+', 
        required=True,
        help='Path(s) to component JSON files to verify'
    )
    
    args = parser.parse_args()
    
    # Load and validate model file
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"ERROR: Model file '{model_path}' does not exist")
        sys.exit(1)
    
    try:
        with open(model_path, 'r') as f:
            model_data = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not read model file: {e}")
        sys.exit(1)
    
    # Extract all IDs and labels from model
    id_to_label = extract_node_and_link_info(model_data)
    print(f"Found {len(id_to_label)} IDs in model: {args.model}")
    
    # Verify each component file
    all_files_valid = True
    
    for component_file in args.components:
        component_path = Path(component_file)
        if not component_path.exists():
            print(f"ERROR: Component file '{component_path}' does not exist")
            all_files_valid = False
            continue
            
        file_valid = verify_component_file(component_path, id_to_label)
        all_files_valid = all_files_valid and file_valid
    
    # Summary
    if not all_files_valid:
        print("\n*** ERRORS FOUND ***")
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()