#!/usr/bin/env python3

"""
Interactive script to upload models, scenarios, resources, and economic analyses 
from the current project directory to the API.
"""

import json
import sys
import re
import os
import csv
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple, NamedTuple
from dotenv import load_dotenv


def load_environment_variables() -> Tuple[str, str, str]:
    """
    Load environment variables from .env.local file.
    Returns a tuple of (api_base_url, admin_token, superuser_id)
    """
    # Load environment variables from .env.local into os.environ
    load_dotenv(".env.local")
    
    # Extract required variables from os.environ
    api_base_url = os.environ.get('API_BASE_URL')
    if not api_base_url:
        print("Error: API_BASE_URL not found in .env.local")
        sys.exit(1)
    
    admin_token = os.environ.get('ADMIN_TOKEN')
    if not admin_token:
        print("Warning: ADMIN_TOKEN not found in .env.local, using default")
        admin_token = "supersecret"
    else:
        print("Using ADMIN_TOKEN from .env.local")
    
    superuser_id = os.environ.get('SUPERUSER_ID')
    if not superuser_id:
        print("Warning: SUPERUSER_ID not found in .env.local, defaulting to user ID 1")
        superuser_id = "1"
    else:
        print(f"Using SUPERUSER_ID: {superuser_id}")
    
    return api_base_url, admin_token, superuser_id


def call_api(method: str, endpoint: str, data: Optional[Dict] = None, 
             api_base_url: str = '', admin_token: Optional[str] = None) -> Dict:
    """Make API calls to the backend."""
    url = f"{api_base_url}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    # Add admin token header if provided
    if admin_token:
        headers["x-admin-token"] = admin_token
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")
        # Print the response content if available
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_content = e.response.json()
                print(f"Error response: {json.dumps(error_content, indent=2)}")
            except json.JSONDecodeError:
                print(f"Error response content: {e.response.text}")
        return {"error": str(e)}
    except json.JSONDecodeError:
        print(f"Couldn't parse JSON response (response text omitted)")
        return {"error": "Invalid JSON response"}


def extract_id_from_response(response: Dict) -> Optional[str]:
    """Extract ID from API response with fallback mechanisms."""
    # Try direct access to structured response
    try:
        # Check common patterns in API responses
        if 'data' in response:
            data = response['data']
            for key in ['model', 'scenario', 'resource', 'economicAnalysis']:
                if key in data and 'id' in data[key]:
                    return data[key]['id']
        
        # Direct ID in response
        if 'id' in response:
            return response['id']
    except (TypeError, KeyError):
        pass
    
    # Fallback to regex extraction from string representation
    try:
        response_str = json.dumps(response)
        id_match = re.search(r'"id"\s*:\s*"([^"]*)"', response_str)
        if id_match:
            return id_match.group(1)
    except:
        pass
    
    return None


def extract_json_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from JSON file with fallbacks, constructing user-friendly name."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metadata = data.get('metadata', {})
        label = metadata.get('label')  # Prioritize label
        description = metadata.get('description', '')
        is_baseline = metadata.get('isBaseline', False)
        
        # Attempt to construct user-friendly name: "Label - ISO3"
        name = None
        if label:
            try:
                # Extract country code from parameters if possible
                country_code = data.get('parameters', {}).get('Country', {}).get('value')
                if country_code and isinstance(country_code, str) and len(country_code) == 3:
                    name = f"{label} - {country_code}"
                else:
                    name = label  # Fallback to just the label if country code not found/invalid
            except Exception:
                name = label  # Fallback on error
        
        # Fall back to legacy name field in metadata if label not found
        if not name:
            name = metadata.get('name')
            
        # Final fallback to filename stem if no label or name was found
        if not name:
            name = file_path.stem
        
        return {
            'name': name,  # This is the potentially constructed user-friendly name
            'description': description,
            'is_baseline': is_baseline,
            'data': data
        }
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Error processing {file_path}: {e}")
        # Fallback if file reading fails
        return {
            'name': file_path.stem,
            'description': '',
            'is_baseline': False,
            'data': {}
        }


def print_header(title: str) -> None:
    """Print a formatted header."""
    width = 70
    print("\n" + "=" * width)
    print(f"{title.center(width)}")
    print("=" * width + "\n")


def print_section(title: str) -> None:
    """Print a section title."""
    print(f"\n--- {title} ---")


def get_user_choice(prompt: str, options: List[str], allow_multiple: bool = False) -> List[int]:
    """Display options and get user choice(s)."""
    print(f"\n{prompt}")
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    
    if allow_multiple:
        print("\nEnter comma-separated numbers (e.g., 1,3,4) or 'all' for all options")
    else:
        print("\nEnter a number")
    
    while True:
        try:
            user_input = input("> ").strip()
            
            if allow_multiple and user_input.lower() == 'all':
                return list(range(1, len(options) + 1))
            
            if allow_multiple:
                choices = [int(x.strip()) for x in user_input.split(',')]
                if all(1 <= choice <= len(options) for choice in choices):
                    return choices
            else:
                choice = int(user_input)
                if 1 <= choice <= len(options):
                    return [choice]
                
            print(f"Please enter valid number(s) between 1 and {len(options)}")
        except ValueError:
            print("Please enter valid number(s)")


def display_menu():
    """Display the main menu and get user choice."""
    print_header("Botech Model Upload Tool")
    
    options = [
        "Upload complete model (model + scenarios + resources + economic analyses)",
        "Upload model only",
        "Upload scenarios only (requires model)",
        "Upload resources only (requires model)",
        "Upload economic analyses only (requires model and scenarios)",
        "Exit"
    ]
    
    return get_user_choice("Select an option:", options)[0]


def upload_model(db_identifiers_path: Path, 
                api_base_url: str, admin_token: str, superuser_id: str) -> Optional[str]:
    """Upload the model to the API."""
    print_section("Uploading Model")
    
    model_file_path = Path("model.json")
    
    # Check if model.json exists
    if not model_file_path.exists():
        print(f"Error: model.json not found")
        return None
    
    # Extract model metadata
    model_metadata = extract_json_metadata(model_file_path)
    name = model_metadata['name']
    description = model_metadata['description']
    
    print(f"Uploading model: {name}")
    print(f"Description: {description}")
    
    # Upload model
    model_payload = {
        "name": name,
        "description": description,
        "modelData": model_metadata['data'],
        "isPublic": True,
        "version": "1.0.0"
    }
    
    # Determine which API endpoint to use based on superuser_id
    if superuser_id:
        # Use admin seed route if superuser ID is available
        admin_payload = model_payload.copy()
        admin_payload["userId"] = superuser_id
        model_response = call_api(
            "POST", 
            "/v1/admin/seed/models", 
            admin_payload, 
            api_base_url, 
            admin_token
        )
    else:
        # Use standard route without user ID
        model_response = call_api(
            "POST", 
            "/v1/models/", 
            model_payload, 
            api_base_url, 
            admin_token
        )
    
    # Extract model ID from the response (response logging removed)
    model_id = extract_id_from_response(model_response)
    
    if not model_id:
        print("Warning: Could not extract model ID")
        return None
    
    print(f"Model ID: {model_id}")
    # Record the model ID
    add_identifier(db_identifiers_path, "MODEL", name, model_id)
    
    return model_id


def upload_scenarios(db_identifiers_path: Path, model_id: str,
                    api_base_url: str, admin_token: str) -> List[str]:
    """Upload scenarios to the API."""
    print_section("Uploading Scenarios")
    
    scenarios_dir = Path("scenarios")
    scenario_ids = []
    
    if not scenarios_dir.exists() or not scenarios_dir.is_dir():
        print(f"No scenarios directory found at {scenarios_dir}")
        return scenario_ids
    
    print(f"Processing scenarios in {scenarios_dir}")
    
    # Process each scenario JSON file
    for scenario_file in scenarios_dir.glob("*.json"):
        print(f"Processing scenario: {scenario_file}")
        
        # Extract scenario metadata
        scenario_metadata = extract_json_metadata(scenario_file)
        scenario_name = scenario_metadata['name']
        scenario_description = scenario_metadata['description']
        is_baseline = scenario_metadata.get('is_baseline', False)
        
        print(f"Uploading scenario: {scenario_name} (Baseline: {is_baseline})")
        
        # Create scenario payload
        scenario_payload = {
            "name": scenario_name,
            "description": scenario_description,
            "scenarioData": scenario_metadata['data'],
            "isBaseline": is_baseline,
            "version": "1.0.0",
            "modelId": model_id
        }
        
        # Upload scenario
        scenario_response = call_api(
            "POST", 
            f"/v1/models/{model_id}/scenarios/", 
            scenario_payload, 
            api_base_url, 
            admin_token
        )
        
        # Extract scenario ID from the response (response logging removed)
        scenario_id = extract_id_from_response(scenario_response)
        
        if scenario_id:
            print(f"Scenario ID: {scenario_id}")
            # Record the scenario ID
            add_identifier(db_identifiers_path, "SCENARIO", scenario_name, scenario_id)
            # Add to the list
            scenario_ids.append(scenario_id)
    
    return scenario_ids


def upload_resources(db_identifiers_path: Path, model_id: str,
                     api_base_url: str, admin_token: str) -> List[str]:
    """Upload resources to the API."""
    print_section("Uploading Resources")
    
    resources_dir = Path("resources")
    resource_ids = []
    
    if not resources_dir.exists() or not resources_dir.is_dir():
        print(f"No resources directory found at {resources_dir}")
        return resource_ids
        
    if not any(resources_dir.glob("*.json")):
        print(f"No resource files found in {resources_dir}")
        return resource_ids
    
    print(f"Processing resources in {resources_dir}")
    
    # Process each resource JSON file
    for resource_file in resources_dir.glob("*.json"):
        print(f"Processing resource: {resource_file}")
        
        # Extract resource metadata
        resource_metadata = extract_json_metadata(resource_file)
        resource_name = resource_metadata['name']
        resource_description = resource_metadata['description']
        is_baseline = resource_metadata.get('is_baseline', False)
        
        print(f"Uploading resource: {resource_name} (Baseline: {is_baseline})")
        
        # Create resource payload
        resource_payload = {
            "name": resource_name,
            "description": resource_description,
            "resourceData": resource_metadata['data'],
            "isBaseline": is_baseline,
            "version": "1.0.0"
        }
        
        # Upload resource
        resource_response = call_api(
            "POST", 
            f"/v1/models/{model_id}/resources/", 
            resource_payload, 
            api_base_url, 
            admin_token
        )
        
        # Extract resource ID from the response (response logging removed)
        resource_id = extract_id_from_response(resource_response)
        
        if resource_id:
            print(f"Resource ID: {resource_id}")
            # Record the resource ID
            add_identifier(db_identifiers_path, "RESOURCE", resource_name, resource_id)
            # Add to the list
            resource_ids.append(resource_id)
    
    return resource_ids


def upload_economic_analyses(db_identifiers_path: Path, model_id: str,
                            api_base_url: str, admin_token: str, scenario_ids: List[str] = None) -> int:
    """Upload economic analyses to the API."""
    print_section("Uploading Economic Analyses")
    
    economic_analyses_path = Path("list_of_economic_analyses.json")
    uploaded_analyses_count = 0
    
    if not economic_analyses_path.exists():
        print(f"No economic analyses file found at {economic_analyses_path}")
        return uploaded_analyses_count
    
    print(f"Processing economic analyses from {economic_analyses_path}")
    
    try:
        # Read the economic analyses
        with open(economic_analyses_path, 'r') as f:
            economic_analyses = json.load(f)
        
        if not economic_analyses:
            print(f"No economic analyses found in {economic_analyses_path}, skipping...")
            return 0
        
        print(f"Found {len(economic_analyses)} economic analyses")
        
        # Get a map of scenario names to scenario IDs
        scenario_map = {}
        
        # Fetch all scenarios for this model using pagination
        page = 1
        per_page = 100  # Request more items per page to reduce API calls
        all_scenarios = []
        
        while True:
            scenarios_response = call_api(
                "GET",
                f"/v1/models/{model_id}/scenarios/?page={page}&limit={per_page}",
                None,
                api_base_url,
                admin_token
            )
            
            # Extract scenarios from the response
            if 'data' in scenarios_response and 'scenarios' in scenarios_response['data']:
                scenarios = scenarios_response['data']['scenarios']
                if not scenarios:
                    break  # No more scenarios to fetch
                
                all_scenarios.extend(scenarios)
                print(f"Fetched {len(scenarios)} scenarios from API (page {page})")
                
                # Check if we've reached the last page
                if len(scenarios) < per_page:
                    break
                
                # Move to next page
                page += 1
            else:
                print("Warning: Could not fetch scenarios from API")
                print("Could not fetch scenarios (response details omitted)")
                break
        
        # Create a mapping from scenario name to ID
        for scenario in all_scenarios:
            if 'name' in scenario and 'id' in scenario:
                scenario_map[scenario['name']] = scenario['id']
                print(f"Mapped scenario: {scenario['name']} (ID: {scenario['id']})")
        
        if not all_scenarios:
            print("Warning: No scenarios were fetched from API")
            return 0
            
        print(f"Total scenarios mapped: {len(scenario_map)}")
        
        # Process each economic analysis
        for analysis in economic_analyses:
            name = analysis.get('name', '')
            description = analysis.get('description', '')
            country_override = analysis.get('country_override', '')
            baseline_scenario_label = analysis.get('baseline_scenario_label', '')
            comparator_scenario_label = analysis.get('comparator_scenario_label', '')
            numerator_label = analysis.get('numerator_label', '')
            denominator_label = analysis.get('denominator_label', '')
            
            # Get scenario IDs from the mapping
            baseline_scenario_id = scenario_map.get(baseline_scenario_label)
            comparator_scenario_id = scenario_map.get(comparator_scenario_label)
            
            if not baseline_scenario_id:
                print(f"Warning: Could not find baseline scenario ID for '{baseline_scenario_label}', skipping analysis '{name}'...")
                continue
            
            if not comparator_scenario_id:
                print(f"Warning: Could not find comparator scenario ID for '{comparator_scenario_label}', skipping analysis '{name}'...")
                continue
            
            print(f"\nPosting economic analysis: {name}")
            print(f"  Baseline scenario: {baseline_scenario_label} (ID: {baseline_scenario_id})")
            print(f"  Comparator scenario: {comparator_scenario_label} (ID: {comparator_scenario_id})")
            print(f"  Numerator label: {numerator_label}")
            print(f"  Denominator label: {denominator_label}")
            
            # Create economic analysis payload
            analysis_payload = {
                "name": name,
                "description": description,
                "baselineScenarioId": baseline_scenario_id,
                "comparatorScenarioId": comparator_scenario_id,
                "numeratorLabel": numerator_label,
                "denominatorLabel": denominator_label,
                "status": "draft"
            }
            
            # Add optional country override if provided
            if country_override:
                analysis_payload["countryOverride"] = country_override
            
            # Upload economic analysis
            analysis_response = call_api(
                "POST", 
                f"/v1/models/{model_id}/economic-analyses/", 
                analysis_payload, 
                api_base_url, 
                admin_token
            )
            
            # Extract analysis ID from the response (response logging removed)
            analysis_id = extract_id_from_response(analysis_response)
            
            if analysis_id:
                print(f"Economic Analysis ID: {analysis_id}")
                # Record the analysis ID
                add_identifier(db_identifiers_path, "ANALYSIS", name, analysis_id)
                uploaded_analyses_count += 1
    
    except json.JSONDecodeError as e:
        print(f"Error parsing economic analyses JSON: {e}")
    except Exception as e:
        print(f"Error processing economic analyses: {e}")
    
    return uploaded_analyses_count


class Identifier(NamedTuple):
    """Data structure for database identifiers."""
    type: str  # MODEL, SCENARIO, RESOURCE, ANALYSIS
    name: str
    id: str
    timestamp: str = ""


def create_db_identifiers_file(db_identifiers_path: Path) -> None:
    """Create or initialize the DB identifiers CSV file."""
    with open(db_identifiers_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header row
        writer.writerow(['type', 'name', 'id', 'timestamp', 'notes'])
        # Write metadata row
        writer.writerow(['INFO', f'Created on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', '', '', ''])


def print_summary(db_identifiers_path: Path, model_name: Optional[str], model_id: Optional[str],
                 scenario_count: int, resource_count: int, analysis_count: int) -> None:
    """Print a summary of the upload results."""
    print_header("Upload Summary")
    
    print(f"Project data stored in: {db_identifiers_path}")
    
    if model_id:
        print(f"Model: {model_name} (ID: {model_id})")
    
    print(f"Scenarios uploaded: {scenario_count}")
    print(f"Resources uploaded: {resource_count}")
    print(f"Economic analyses uploaded: {analysis_count}")
    
    components = []
    if model_id:
        components.append("model")
    if scenario_count > 0:
        components.append("scenarios")
    if resource_count > 0:
        components.append("resources")
    if analysis_count > 0:
        components.append("economic analyses")
    
    if components:
        print(f"{', '.join(components)} processed successfully!")
    else:
        print("No components were processed.")
    
    # Print the contents of the DB identifiers file
    print("\n=== Database Identifiers ===")
    try:
        all_identifiers = get_identifiers(db_identifiers_path)
        
        if not all_identifiers:
            print("No identifiers found.")
            return
        
        # Print in a formatted table
        print(f"{'TYPE':<10} {'NAME':<30} {'ID':<36} {'TIMESTAMP':<20}")
        print("-" * 96)
        
        for identifier in all_identifiers:
            print(f"{identifier.type:<10} {identifier.name[:28]:<30} {identifier.id:<36} {identifier.timestamp:<20}")
    except Exception as e:
        print(f"Error displaying identifiers: {e}")
        # Fallback to raw display
        try:
            with open(db_identifiers_path, 'r') as f:
                print(f.read())
        except:
            print("Could not read identifiers file.")


def add_identifier(db_identifiers_path: Path, id_type: str, name: str, id_value: str) -> None:
    """Add a new identifier to the CSV file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(db_identifiers_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([id_type, name, id_value, timestamp, ''])


def get_identifiers(db_identifiers_path: Path, id_type: Optional[str] = None) -> List[Identifier]:
    """Get all identifiers or identifiers of a specific type from the CSV file."""
    if not db_identifiers_path.exists():
        return []
    
    identifiers = []
    
    try:
        with open(db_identifiers_path, 'r', newline='') as f:
            reader = csv.reader(f)
            # Skip header row
            next(reader, None)
            
            for row in reader:
                if len(row) >= 3:
                    row_type, name, id_value = row[0], row[1], row[2]
                    timestamp = row[3] if len(row) > 3 else ""
                    
                    if row_type != 'INFO' and (id_type is None or row_type == id_type):
                        identifiers.append(Identifier(row_type, name, id_value, timestamp))
    except Exception as e:
        print(f"Warning: Error reading identifiers: {e}")
    
    return identifiers


def get_existing_model_id() -> Optional[str]:
    """
    Try to find an existing model ID from the project.csv file.
    Returns the model ID if found, None otherwise.
    """
    db_identifiers_path = Path("project.csv")
    
    if not db_identifiers_path.exists():
        return None
    
    try:
        models = get_identifiers(db_identifiers_path, 'MODEL')
        if models:
            # Return the ID of the most recently added model
            return models[-1].id
    except Exception as e:
        print(f"Warning: Error finding model ID: {e}")
    
    return None


def main():
    """Main function to run the interactive model upload tool."""
    db_identifiers_path = Path("project.csv")
    
    # Load environment variables
    api_base_url, admin_token, superuser_id = load_environment_variables()
    
    # Initialize tracking variables
    model_id = None
    model_name = None
    scenario_ids = []
    resource_ids = []
    analysis_count = 0
    
    # Display the main menu
    choice = display_menu()
    
    # Create or clear the DB identifiers file if we're going to upload anything
    if choice < 6:  # Not exit
        create_db_identifiers_file(db_identifiers_path)
    
    # Process the user's choice
    if choice == 1:  # Upload complete model
        model_id = upload_model(db_identifiers_path, api_base_url, admin_token, superuser_id)
        if model_id:
            model_name = extract_json_metadata(Path("model.json"))['name']
            scenario_ids = upload_scenarios(db_identifiers_path, model_id, api_base_url, admin_token)
            resource_ids = upload_resources(db_identifiers_path, model_id, api_base_url, admin_token)
            analysis_count = upload_economic_analyses(db_identifiers_path, model_id, api_base_url, admin_token, scenario_ids)
    
    elif choice == 2:  # Upload model only
        model_id = upload_model(db_identifiers_path, api_base_url, admin_token, superuser_id)
        if model_id:
            model_name = extract_json_metadata(Path("model.json"))['name']
    
    elif choice == 3:  # Upload scenarios only
        # Try to find an existing model ID
        model_id = get_existing_model_id()
        
        if not model_id:
            print("No existing model ID found. You need to upload a model first.")
            print("You can:")
            print("1. Upload a model now")
            print("2. Enter a model ID manually")
            print("3. Return to the main menu")
            
            subchoice = get_user_choice("Select an option:", ["Upload a model now", "Enter a model ID manually", "Return to main menu"])[0]
            
            if subchoice == 1:
                model_id = upload_model(db_identifiers_path, api_base_url, admin_token, superuser_id)
                if model_id:
                    model_name = extract_json_metadata(Path("model.json"))['name']
            elif subchoice == 2:
                model_id = input("Enter the model ID: ").strip()
                model_name = input("Enter the model name: ").strip()
                add_identifier(db_identifiers_path, "MODEL", model_name, model_id)
        else:
            # Get model name from the existing ID
            models = get_identifiers(db_identifiers_path, 'MODEL')
            for model in models:
                if model.id == model_id:
                    model_name = model.name
                    break
            
            print(f"Found existing model ID: {model_id}")
            print(f"Model name: {model_name}")
        
        if model_id:
            scenario_ids = upload_scenarios(db_identifiers_path, model_id, api_base_url, admin_token)
    
    elif choice == 4:  # Upload resources only
        # Try to find an existing model ID
        model_id = get_existing_model_id()
        
        if not model_id:
            print("No existing model ID found. You need to upload a model first.")
            print("You can:")
            print("1. Upload a model now")
            print("2. Enter a model ID manually")
            print("3. Return to the main menu")
            
            subchoice = get_user_choice("Select an option:", ["Upload a model now", "Enter a model ID manually", "Return to main menu"])[0]
            
            if subchoice == 1:
                model_id = upload_model(db_identifiers_path, api_base_url, admin_token, superuser_id)
                if model_id:
                    model_name = extract_json_metadata(Path("model.json"))['name']
            elif subchoice == 2:
                model_id = input("Enter the model ID: ").strip()
                model_name = input("Enter the model name: ").strip()
                add_identifier(db_identifiers_path, "MODEL", model_name, model_id)
        else:
            # Get model name from the existing ID
            models = get_identifiers(db_identifiers_path, 'MODEL')
            for model in models:
                if model.id == model_id:
                    model_name = model.name
                    break
            
            print(f"Found existing model ID: {model_id}")
            print(f"Model name: {model_name}")
        
        if model_id:
            resource_ids = upload_resources(db_identifiers_path, model_id, api_base_url, admin_token)
    
    elif choice == 5:  # Upload economic analyses only
        # Try to find an existing model ID
        model_id = get_existing_model_id()
        
        if not model_id:
            print("No existing model ID found. You need to upload a model first.")
            print("You can:")
            print("1. Upload a model now")
            print("2. Enter a model ID manually")
            print("3. Return to the main menu")
            
            subchoice = get_user_choice("Select an option:", ["Upload a model now", "Enter a model ID manually", "Return to main menu"])[0]
            
            if subchoice == 1:
                model_id = upload_model(db_identifiers_path, api_base_url, admin_token, superuser_id)
                if model_id:
                    model_name = extract_json_metadata(Path("model.json"))['name']
            elif subchoice == 2:
                model_id = input("Enter the model ID: ").strip()
                model_name = input("Enter the model name: ").strip()
                add_identifier(db_identifiers_path, "MODEL", model_name, model_id)
        else:
            # Get model name from the existing ID
            models = get_identifiers(db_identifiers_path, 'MODEL')
            for model in models:
                if model.id == model_id:
                    model_name = model.name
                    break
            
            print(f"Found existing model ID: {model_id}")
            print(f"Model name: {model_name}")
        
        if model_id:
            # Check if we need to upload scenarios first
            if input("Do you need to upload scenarios first? (y/n): ").lower().startswith('y'):
                scenario_ids = upload_scenarios(db_identifiers_path, model_id, api_base_url, admin_token)
            
            analysis_count = upload_economic_analyses(db_identifiers_path, model_id, api_base_url, admin_token, scenario_ids)
    
    elif choice == 6:  # Exit
        print("Exiting...")
        return
    
    # Print summary if we did anything
    if choice < 6:
        print_summary(
            db_identifiers_path, 
            model_name, 
            model_id,
            len(scenario_ids),
            len(resource_ids),
            analysis_count
        )


if __name__ == "__main__":
    main()
