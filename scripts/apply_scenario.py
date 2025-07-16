#!/usr/bin/env python3
"""
Apply scenario parameters to a model JSON file.

This script takes a model JSON file and a scenario JSON file, then applies
the parameter values from the scenario to the model using JSONPath expressions.
"""

import argparse
import json
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

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


def save_json_file(data: Dict[str, Any], file_path: str) -> None:
    """Save data to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error: Failed to write {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def apply_jsonpath_value(model: Dict[str, Any], jsonpath_expr: str, value: Any) -> bool:
    """Apply a value to a model using a JSONPath expression."""
    try:
        # Try extended parser first for complex expressions
        try:
            jsonpath_parser = parse_ext(jsonpath_expr)
        except Exception:
            # Fall back to basic parser
            jsonpath_parser = parse(jsonpath_expr)
        
        # Find matches
        matches = jsonpath_parser.find(model)
        
        if not matches:
            print(f"Warning: JSONPath '{jsonpath_expr}' found no matches", file=sys.stderr)
            return False
        
        # Update all matches
        for match in matches:
            match.full_path.update(model, value)
        
        print(f"Applied value {value} to {len(matches)} location(s) via '{jsonpath_expr}'")
        return True
        
    except Exception as e:
        print(f"Error: Failed to apply JSONPath '{jsonpath_expr}': {e}", file=sys.stderr)
        return False


def apply_scenario_to_model(model: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Apply scenario parameters to the model."""
    if 'parameters' not in scenario:
        print("Error: Scenario file must contain a 'parameters' section", file=sys.stderr)
        sys.exit(1)
    
    applied_count = 0
    failed_count = 0
    
    for param_name, param_config in scenario['parameters'].items():
        if 'paths' not in param_config or 'value' not in param_config:
            print(f"Warning: Parameter '{param_name}' missing 'paths' or 'value' field", file=sys.stderr)
            continue
        
        value = param_config['value']
        paths = param_config['paths']
        
        if not isinstance(paths, list):
            print(f"Warning: Parameter '{param_name}' paths must be a list", file=sys.stderr)
            continue
        
        print(f"\nApplying parameter: {param_name}")
        print(f"  Value: {value}")
        
        param_applied = False
        for jsonpath_expr in paths:
            if apply_jsonpath_value(model, jsonpath_expr, value):
                param_applied = True
            else:
                failed_count += 1
        
        if param_applied:
            applied_count += 1
    
    print(f"\nSummary: Applied {applied_count} parameters successfully")
    if failed_count > 0:
        print(f"Warning: {failed_count} JSONPath expressions failed to find matches")
    
    return model


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Apply scenario parameters to a model JSON file using JSONPath expressions"
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
        '--output',
        required=True,
        help="Path for the output JSON file"
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
    
    # Apply scenario to model
    print(f"\nApplying scenario '{scenario.get('metadata', {}).get('label', 'Unknown')}' to model...")
    updated_model = apply_scenario_to_model(model, scenario)
    
    # Save result
    print(f"\nSaving updated model to: {args.output}")
    save_json_file(updated_model, args.output)
    
    print("Done!")


if __name__ == '__main__':
    main()