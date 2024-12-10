import os
import sys
import json

def process_defaults(defaults):
    """Converts the 'defaults' structure from a list of dictionaries to a dictionary."""
    if isinstance(defaults, list):
        new_defaults = {item['id']: item['value'] for item in defaults}
        return new_defaults
    return defaults

def process_json_file(file_path):
    """Processes a JSON file to modify the 'defaults' structure if necessary."""
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Check if the 'defaults' key exists and is a list, then process it
    if 'defaults' in data and isinstance(data['defaults'], list):
        data['defaults'] = process_defaults(data['defaults'])

        # Write the changes back to the file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

        print(f"Processed file: {file_path}")
    else:
        print(f"No changes needed for: {file_path}")

def process_directory(directory_path):
    """Iterates through .json files in the directory and processes them."""
    for filename in os.listdir(directory_path):
        if filename.endswith('.json'):
            file_path = os.path.join(directory_path, filename)
            process_json_file(file_path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_json_defaults.py <directory_path>")
        sys.exit(1)

    directory_path = sys.argv[1]

    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} is not a valid directory.")
        sys.exit(1)

    process_directory(directory_path)
