import argparse
import json
import sys
from jsonpath_ng.ext import parse

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Check scenario parameters against a model using JSONPaths.')
    parser.add_argument('--model', required=True, help='Path to the model JSON file')
    parser.add_argument('--scenario', required=True, help='Path to the scenario JSON file')
    args = parser.parse_args()

    # Load model and scenario
    try:
        with open(args.model, 'r', encoding='utf-8') as f:
            model = json.load(f)
    except FileNotFoundError:
        print(f"Error: Model file '{args.model}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error decoding model JSON: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.scenario, 'r', encoding='utf-8') as f:
            scenario = json.load(f)
    except FileNotFoundError:
        print(f"Error: Scenario file '{args.scenario}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error decoding scenario JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract parameters from scenario
    parameters = scenario.get('parameters', {})
    if not parameters:
        print("No parameters found in scenario.", file=sys.stderr)
        sys.exit(0)  # Not necessarily an error, just nothing to check.

    missing_paths_found = False

    # Iterate over parameters
    for param_name, param_data in parameters.items():
        paths = param_data.get('paths', [])
        for p in paths:
            # Parse the JSONPath
            jsonpath_expr = parse(p)
            matches = jsonpath_expr.find(model)

            if not matches:
                # No matches means the path does not exist in the model
                missing_paths_found = True
                print(f"Missing path for parameter '{param_name}': {p}")

    if not missing_paths_found:
        # If you want to indicate success when everything matches:
        # print("All scenario paths exist in the model.")
        pass

if __name__ == '__main__':
    main()
