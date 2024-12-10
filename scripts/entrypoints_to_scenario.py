import sys
import json
from typing import List, Dict, Any

def find_path(data: Dict[str, Any], target_id: str, current_path: List[str] = None) -> List[str]:
    if current_path is None:
        current_path = []

    if isinstance(data, dict):
        for key, value in data.items():
            new_path = current_path + [key]
            if isinstance(value, dict):
                for k, v in value.items():
                    if v == target_id:
                        return new_path + [k]
            result = find_path(value, target_id, new_path)
            if result:
                return result
    elif isinstance(data, list):
        for i, item in enumerate(data):
            result = find_path(item, target_id, current_path)
            if result:
                return result
    return None

def create_scenario_json(model_data: Dict[str, Any], entrypoints: List[Dict[str, Any]]) -> Dict[str, Any]:
    scenario = {
        "metadata": {
            "name": "Model Scenario",
            "description": "Scenario for all entrypoints in the model"
        },
        "parameters": {}
    }

    for entrypoint in entrypoints:
        parameter = {
            "label": entrypoint['id'],
            "default_value": entrypoint['value'],
            "description": entrypoint['description'],
            "ids": []
        }

        for section in ["nodes", "links"]:
            if section in model_data:
                for item in model_data[section]:
                    path = find_path(item, entrypoint['id'])
                    if path:
                        full_path = [section, item.get("id", "")] + path
                        parameter["ids"].append(full_path)

        scenario["parameters"][entrypoint['id']] = parameter

    return scenario

def process_model_file(filepath: str):
    with open(filepath, 'r') as file:
        model_data = json.load(file)

    if "entrypoints" in model_data:
        scenario = create_scenario_json(model_data, model_data["entrypoints"])
        output_filename = "./scenarios/default_scenario.json"
        with open(output_filename, 'w') as outfile:
            json.dump(scenario, outfile, indent=2)
        print(f"Created scenario file: {output_filename}")
    else:
        print("No entrypoints found in the model file.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ifmain.py <filepath>")
        sys.exit(1)

    filepath = sys.argv[1]
    process_model_file(filepath)
