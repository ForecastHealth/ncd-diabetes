#!/usr/bin/env python3
"""
Diagnose scenario warnings by analyzing JSONPath expressions.

This script performs a dry run of scenario application and diagnoses warnings:
- ID does not exist
- ID is a node/link (not a link/node)
- Other warnings

Additionally, it searches for "AFG" strings in the model and checks if these
JSONPaths are missing from the "Country" parameter.
"""

import argparse
import json
import sys
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from collections import defaultdict

try:
    from jsonpath_ng import parse
    from jsonpath_ng.ext import parse as parse_ext
except ImportError:
    print("Error: jsonpath-ng is required. Install with: pip install jsonpath-ng", file=sys.stderr)
    sys.exit(1)


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to read {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def extract_id_from_jsonpath(jsonpath_expr: str) -> Optional[str]:
    """Extract the ID value from a JSONPath expression like $.nodes[?(@.id=='xxx')]."""
    import re
    # Match patterns like $.nodes[?(@.id=='ID')] or $.links[?(@.id=='ID')]
    match = re.search(r"@\.id=='([^']+)'", jsonpath_expr)
    if match:
        return match.group(1)
    return None


def extract_type_from_jsonpath(jsonpath_expr: str) -> Optional[str]:
    """Extract whether the JSONPath refers to nodes or links."""
    if jsonpath_expr.startswith("$.nodes"):
        return "node"
    elif jsonpath_expr.startswith("$.links"):
        return "link"
    return None


def diagnose_jsonpath_warning(model: Dict[str, Any], jsonpath_expr: str) -> Tuple[str, str]:
    """
    Diagnose why a JSONPath expression produces a warning.
    
    Returns: (diagnosis, details)
    """
    # Extract ID and type from JSONPath
    id_value = extract_id_from_jsonpath(jsonpath_expr)
    path_type = extract_type_from_jsonpath(jsonpath_expr)
    
    if not id_value:
        return "other", "Could not extract ID from JSONPath expression"
    
    # Build ID sets for nodes and links
    node_ids = set(node['id'] for node in model.get('nodes', []))
    link_ids = set(link['id'] for link in model.get('links', []))
    
    # Check if ID exists anywhere
    if id_value not in node_ids and id_value not in link_ids:
        return "id_not_exist", f"ID '{id_value}' does not exist in model"
    
    # Check if ID is in wrong collection
    if path_type == "node" and id_value in link_ids:
        return "wrong_type", f"ID '{id_value}' is a link but JSONPath looks in nodes"
    elif path_type == "link" and id_value in node_ids:
        return "wrong_type", f"ID '{id_value}' is a node but JSONPath looks in links"
    
    # Try to evaluate the JSONPath
    try:
        try:
            jsonpath_parser = parse_ext(jsonpath_expr)
        except Exception:
            jsonpath_parser = parse(jsonpath_expr)
        
        matches = jsonpath_parser.find(model)
        if not matches:
            return "other", f"JSONPath expression found no matches (ID exists but path may be incorrect)"
    except Exception as e:
        return "other", f"JSONPath parsing error: {e}"
    
    return "other", "Unknown warning reason"


def check_afg_in_model(model: Dict[str, Any]) -> List[str]:
    """
    Search for "AFG" strings in model nodes and links and return JSONPath expressions
    that would target those locations.
    """
    afg_paths = []
    
    # Check nodes
    for node in model.get('nodes', []):
        node_id = node.get('id', '')
        # Check if AFG appears in generate_array.parameters
        if 'generate_array' in node and 'parameters' in node['generate_array']:
            params = node['generate_array']['parameters']
            if isinstance(params, dict):
                for key, value in params.items():
                    if value == "AFG":
                        path = f"$.nodes[?(@.id=='{node_id}')].generate_array.parameters.{key}"
                        afg_paths.append(path)
    
    # Check links
    for link in model.get('links', []):
        link_id = link.get('id', '')
        # Check if AFG appears in generate_array.parameters
        if 'generate_array' in link and 'parameters' in link['generate_array']:
            params = link['generate_array']['parameters']
            if isinstance(params, dict):
                for key, value in params.items():
                    if value == "AFG":
                        path = f"$.links[?(@.id=='{link_id}')].generate_array.parameters.{key}"
                        afg_paths.append(path)
    
    return afg_paths


def diagnose_scenario(model: Dict[str, Any], scenario: Dict[str, Any], terse: bool = False) -> None:
    """Diagnose scenario application warnings."""
    if 'parameters' not in scenario:
        print("Error: Scenario file must contain a 'parameters' section", file=sys.stderr)
        sys.exit(1)
    
    # Track warnings by diagnosis type
    warnings_by_type = defaultdict(list)
    total_paths = 0
    successful_paths = 0
    
    print(f"Analyzing scenario: {scenario.get('metadata', {}).get('label', 'Unknown')}")
    print("=" * 80)
    
    # Process each parameter
    for param_name, param_config in scenario['parameters'].items():
        if 'paths' not in param_config or 'value' not in param_config:
            print(f"Warning: Parameter '{param_name}' missing 'paths' or 'value' field", file=sys.stderr)
            continue
        
        paths = param_config['paths']
        if not isinstance(paths, list):
            print(f"Warning: Parameter '{param_name}' paths must be a list", file=sys.stderr)
            continue
        
        # Test each JSONPath
        for jsonpath_expr in paths:
            total_paths += 1
            try:
                # Try to parse and find matches
                try:
                    jsonpath_parser = parse_ext(jsonpath_expr)
                except Exception:
                    jsonpath_parser = parse(jsonpath_expr)
                
                matches = jsonpath_parser.find(model)
                
                if not matches:
                    # Diagnose the warning
                    diagnosis, details = diagnose_jsonpath_warning(model, jsonpath_expr)
                    warnings_by_type[diagnosis].append({
                        'parameter': param_name,
                        'path': jsonpath_expr,
                        'details': details
                    })
                else:
                    successful_paths += 1
                    
            except Exception as e:
                warnings_by_type['other'].append({
                    'parameter': param_name,
                    'path': jsonpath_expr,
                    'details': f"JSONPath error: {e}"
                })
    
    # Display results
    print(f"\nTotal JSONPath expressions: {total_paths}")
    print(f"Successful matches: {successful_paths}")
    print(f"Warnings: {total_paths - successful_paths}")
    
    if warnings_by_type:
        print("\nWarning Diagnoses:")
        print("-" * 80)
        
        # ID does not exist
        if 'id_not_exist' in warnings_by_type:
            print(f"\n1. ID DOES NOT EXIST ({len(warnings_by_type['id_not_exist'])} warnings):")
            display_limit = 5 if terse else len(warnings_by_type['id_not_exist'])
            for warning in warnings_by_type['id_not_exist'][:display_limit]:
                print(f"   - Parameter: {warning['parameter']}")
                print(f"     Path: {warning['path']}")
                print(f"     {warning['details']}")
            if terse and len(warnings_by_type['id_not_exist']) > 5:
                print(f"   ... and {len(warnings_by_type['id_not_exist']) - 5} more")
        
        # Wrong type (node/link mismatch)
        if 'wrong_type' in warnings_by_type:
            print(f"\n2. ID IS WRONG TYPE (node/link mismatch) ({len(warnings_by_type['wrong_type'])} warnings):")
            display_limit = 5 if terse else len(warnings_by_type['wrong_type'])
            for warning in warnings_by_type['wrong_type'][:display_limit]:
                print(f"   - Parameter: {warning['parameter']}")
                print(f"     Path: {warning['path']}")
                print(f"     {warning['details']}")
            if terse and len(warnings_by_type['wrong_type']) > 5:
                print(f"   ... and {len(warnings_by_type['wrong_type']) - 5} more")
        
        # Other warnings
        if 'other' in warnings_by_type:
            print(f"\n3. OTHER WARNINGS ({len(warnings_by_type['other'])} warnings):")
            display_limit = 5 if terse else len(warnings_by_type['other'])
            for warning in warnings_by_type['other'][:display_limit]:
                print(f"   - Parameter: {warning['parameter']}")
                print(f"     Path: {warning['path']}")
                print(f"     {warning['details']}")
            if terse and len(warnings_by_type['other']) > 5:
                print(f"   ... and {len(warnings_by_type['other']) - 5} more")
    
    # Check for AFG strings in model
    print("\n" + "=" * 80)
    print("AFG String Analysis:")
    print("-" * 80)
    
    afg_paths = check_afg_in_model(model)
    country_paths = set()
    
    # Get Country parameter paths from scenario
    if 'Country' in scenario['parameters'] and 'paths' in scenario['parameters']['Country']:
        country_paths = set(scenario['parameters']['Country']['paths'])
    
    print(f"\nFound {len(afg_paths)} instances of 'AFG' in model")
    
    # Check which AFG paths are missing from Country parameter
    missing_from_country = []
    for path in afg_paths:
        if path not in country_paths:
            missing_from_country.append(path)
    
    if missing_from_country:
        print(f"\nJSONPaths with 'AFG' MISSING from Country parameter ({len(missing_from_country)} paths):")
        display_limit = 10 if terse else len(missing_from_country)
        for path in missing_from_country[:display_limit]:
            print(f"   - {path}")
        if terse and len(missing_from_country) > 10:
            print(f"   ... and {len(missing_from_country) - 10} more")
    else:
        print("\nAll AFG paths are included in the Country parameter")
    
    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Diagnose scenario warnings by analyzing JSONPath expressions"
    )
    parser.add_argument(
        '--model',
        required=True,
        help="Path to the model JSON file"
    )
    parser.add_argument(
        '--scenario',
        required=True,
        help="Path to the scenario JSON file"
    )
    parser.add_argument(
        '--terse',
        action='store_true',
        help="Show only first few warnings of each type (default: show all warnings)"
    )
    
    args = parser.parse_args()
    
    # Validate input files exist
    if not Path(args.model).exists():
        print(f"Error: Model file does not exist: {args.model}", file=sys.stderr)
        sys.exit(1)
    
    if not Path(args.scenario).exists():
        print(f"Error: Scenario file does not exist: {args.scenario}", file=sys.stderr)
        sys.exit(1)
    
    # Load files
    print(f"Loading model: {args.model}")
    model = load_json_file(args.model)
    
    print(f"Loading scenario: {args.scenario}")
    scenario = load_json_file(args.scenario)
    
    # Diagnose scenario
    diagnose_scenario(model, scenario, terse=args.terse)


if __name__ == '__main__':
    main()