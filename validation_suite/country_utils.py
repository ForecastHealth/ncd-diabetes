"""
Country-specific utilities for multi-country validation.

This module provides functions for loading country lists, creating
country-specific scenarios, and managing country-related operations.
"""

from typing import List, Dict, Any
from .scenario_utils import load_json_file, save_json_file


def load_countries_list(countries_path: str) -> List[Dict[str, str]]:
    """
    Load countries list from JSON file.
    
    Args:
        countries_path: Path to countries JSON file
        
    Returns:
        List of country dictionaries with 'name' and 'iso3' keys
        
    Raises:
        ValueError: If file cannot be loaded or has invalid format
    """
    try:
        countries_data = load_json_file(countries_path)
        countries = countries_data.get('countries', [])
        if not countries:
            raise ValueError("No countries found in countries file")
        
        # Validate country format
        for country in countries:
            if not isinstance(country, dict) or 'iso3' not in country:
                raise ValueError(f"Invalid country format: {country}")
        
        return countries
    except Exception as e:
        raise ValueError(f"Failed to load countries from {countries_path}: {e}")


def create_country_scenario(
    base_scenario_path: str, 
    country_iso3: str, 
    output_path: str
) -> bool:
    """
    Create a scenario file with updated country parameter.
    
    Args:
        base_scenario_path: Path to the base scenario file
        country_iso3: ISO3 country code to set
        output_path: Path where the modified scenario should be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        scenario_data = load_json_file(base_scenario_path)
        
        # Update the Country parameter
        if 'parameters' in scenario_data and 'Country' in scenario_data['parameters']:
            scenario_data['parameters']['Country']['value'] = country_iso3
        else:
            raise ValueError("Scenario file missing Country parameter")
        
        # Save the modified scenario
        save_json_file(scenario_data, output_path)
        return True
        
    except Exception as e:
        print(f"❌ Failed to create country scenario for {country_iso3}: {e}")
        return False


def validate_countries_file(countries_path: str) -> bool:
    """
    Validate that a countries file has the correct format.
    
    Args:
        countries_path: Path to countries JSON file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        countries = load_countries_list(countries_path)
        
        # Check each country has required fields
        for country in countries:
            if not all(key in country for key in ['name', 'iso3']):
                return False
            if not isinstance(country['iso3'], str) or len(country['iso3']) != 3:
                return False
        
        return True
    except Exception:
        return False


def get_country_display_list(countries: List[Dict[str, str]]) -> str:
    """
    Format countries list for display.
    
    Args:
        countries: List of country dictionaries
        
    Returns:
        str: Formatted string for display
    """
    lines = []
    for country in countries:
        name = country.get('name', 'Unknown')
        iso3 = country.get('iso3', 'XXX')
        lines.append(f"   • {name} ({iso3})")
    return '\n'.join(lines)