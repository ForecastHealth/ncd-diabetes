"""
reverse_entrypoints.py

Takes a model.json that contains entrypoints and replaces all references to 
entrypoint IDs with their actual values, then removes the entrypoints dictionary.
"""

import json
import sys
from typing import Dict, Any, Union, List

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
        replace_references_in_item(node, entrypoint_values)

    # Replace references in links
    for link in configuration.get('links', []):
        replace_references_in_item(link, entrypoint_values)

    # Remove the entrypoints dictionary
    if 'entrypoints' in configuration:
        del configuration['entrypoints']

    return configuration

def replace_references_in_item(
    item: Union[Dict, List, Any], 
    entrypoint_values: Dict[str, Any]
) -> Union[Dict, List, Any]:
    """
    Recursively replace entrypoint references in a dictionary or list.

    Args:
        item: Dictionary, list, or value to process
        entrypoint_values (Dict[str, Any]): Mapping of entrypoint IDs to values
    """
    if isinstance(item, dict):
        for key, value in item.items():
            item[key] = replace_references_in_item(value, entrypoint_values)
        return item
    
    elif isinstance(item, list):
        return [replace_references_in_item(element, entrypoint_values) for element in item]
    
    else:
        # If the item is a value that exists in entrypoint_values, replace it
        return entrypoint_values.get(item, item)

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
