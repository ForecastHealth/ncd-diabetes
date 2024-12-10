"""
revert_entrypoints.py

Takes a model.json that contains entrypoints and replaces all references to 
entrypoint IDs with their actual values, then removes the entrypoints dictionary.
"""

import json
import sys
from typing import Dict, Any

def replace_entrypoint_references(
    configuration: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Replace all entrypoint ID references with their actual values.

    Args:
        configuration (Dict[str, Any]): The configuration dictionary containing
            entrypoints and nodes/links with entrypoint references

    Returns:
        Dict[str, Any]: Updated configuration with entrypoint references replaced
    """
    # Create a mapping of entrypoint IDs to their values
    entrypoint_values = {
        ep['id']: ep['value'] 
        for ep in configuration.get('entrypoints', [])
    }

    # Replace references in nodes
    for node in configuration.get('nodes', []):
        replace_references_in_dict(node, entrypoint_values)

    # Replace references in links
    for link in configuration.get('links', []):
        replace_references_in_dict(link, entrypoint_values)

    # Remove the entrypoints dictionary
    if 'entrypoints' in configuration:
        del configuration['entrypoints']

    return configuration

def replace_references_in_dict(
    item: Dict[str, Any], 
    entrypoint_values: Dict[str, Any]
):
    """
    Recursively replace entrypoint references in a dictionary.

    Args:
        item (Dict[str, Any]): Dictionary to process
        entrypoint_values (Dict[str, Any]): Mapping of entrypoint IDs to values
    """
    for key, value in item.items():
        if isinstance(value, dict):
            replace_references_in_dict(value, entrypoint_values)
        elif value in entrypoint_values:
            item[key] = entrypoint_values[value]

def main():
    if len(sys.argv) != 2:
        print("Usage: python reverse_entrypoints.py <model.json>")
        sys.exit(1)

    # Read the model configuration
    with open(sys.argv[1], 'r') as f:
        configuration = json.load(f)

    # Replace entrypoint references and remove entrypoints
    updated_config = replace_entrypoint_references(configuration)

    # Write the updated configuration
    output_filename = sys.argv[1]
    with open(output_filename, 'w') as f:
        json.dump(updated_config, f, indent=2)

    print(f"Updated configuration written to {output_filename}")

if __name__ == "__main__":
    main()
