"""
Scenario application and validation utilities.
"""
import json
import sys
from typing import Dict, Any
from pathlib import Path

try:
    from jsonpath_ng.ext import parse
except ImportError:
    print("Error: jsonpath-ng is required. Install with: pip install jsonpath-ng", file=sys.stderr)
    sys.exit(1)

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Loads and parses a JSON file, exiting on error."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"L Error reading or parsing {file_path}: {e}", file=sys.stderr)
        sys.exit(1)

def save_json_file(data: Dict[str, Any], file_path: str):
    """Saves data to a JSON file."""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"L Error writing to {file_path}: {e}", file=sys.stderr)
        sys.exit(1)

def apply_jsonpath_value(model: Dict[str, Any], jsonpath_expr: str, value: Any) -> bool:
    """Apply a value to a model using a JSONPath expression with detailed logging."""
    try:
        jsonpath_parser = parse(jsonpath_expr)
        matches = jsonpath_parser.find(model)
        
        if not matches:
            print(f"⚠️  Warning: JSONPath '{jsonpath_expr}' found no matches")
            return False
        
        # Update all matches
        for match in matches:
            match.full_path.update(model, value)
        
        print(f"✅ Applied value {value} to {len(matches)} location(s) via '{jsonpath_expr}'")
        return True
        
    except Exception as e:
        print(f"❌ Error: Failed to apply JSONPath '{jsonpath_expr}': {e}")
        return False

def apply_scenario_to_model_data(model: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Applies scenario parameters to a model data dictionary with detailed output."""
    if 'parameters' not in scenario:
        print("❌ Error: Scenario file must contain a 'parameters' section", file=sys.stderr)
        return model

    applied_count = 0
    failed_count = 0
    
    print(f"\n🔄 Applying scenario '{scenario.get('name', 'Unknown')}' to model...")
    
    for param_name, param_config in scenario['parameters'].items():
        if 'paths' not in param_config or 'value' not in param_config:
            print(f"⚠️  Warning: Parameter '{param_name}' missing 'paths' or 'value' field")
            continue
        
        value = param_config['value']
        paths = param_config['paths']
        
        if not isinstance(paths, list):
            print(f"⚠️  Warning: Parameter '{param_name}' paths must be a list")
            continue
        
        print(f"\n🔧 Applying parameter: {param_name}")
        print(f"   Value: {value}")
        
        param_applied = False
        for path_str in paths:
            if apply_jsonpath_value(model, path_str, value):
                param_applied = True
            else:
                failed_count += 1
        
        if param_applied:
            applied_count += 1
    
    print(f"\n📊 Summary: Applied {applied_count} parameters successfully")
    if failed_count > 0:
        print(f"⚠️  Warning: {failed_count} JSONPath expressions failed to find matches")
    
    return model
    
def apply_scenario_to_model(model_path: str, scenario_path: str, output_path: str) -> bool:
    """Loads model and scenario, applies changes, and saves the result."""
    print(f"📂 Loading model: {model_path}")
    model = load_json_file(model_path)
    print(f"📂 Loading scenario: {scenario_path}")
    scenario = load_json_file(scenario_path)
    
    updated_model = apply_scenario_to_model_data(model, scenario)
    
    print(f"\n💾 Saving updated model to: {output_path}")
    save_json_file(updated_model, output_path)
    print("✅ Scenario application completed successfully!")
    return True

def validate_json_files(model_path: str, scenario_path: str) -> bool:
    """Validates that JSON files are well-formed."""
    try:
        load_json_file(model_path)
        load_json_file(scenario_path)
        return True
    except SystemExit: # load_json_file calls sys.exit on error
        return False