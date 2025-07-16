"""
Analytics API client for fetching simulation results data.

This module provides functionality to fetch analytics data from the
forecast health analytics API.
"""

import json
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path


# Configuration
ANALYTICS_BASE_URL = "https://analytics.forecasthealth.org"

# Default Query Configuration - MODIFY THESE TO CHANGE ANALYTICS QUERIES
DEFAULT_ANALYTICS_QUERY = {
    "event_type": "ECHO",
    "group_by": ["element_label"],
    "group_by_date": "timestamp:year", 
    "aggregations": "value:last",
    "filters": {
        "element_label": "Healthy Years Lived"
    }
}


def fetch_analytics_data(
    environment: str, 
    ulid: str,
    event_type: str = "*",
    group_by: List[str] = None,
    group_by_date: str = "timestamp:year",
    aggregations: str = "value:last",
    timeout: int = 30,
    filters: Dict[str, Any] = None,
    agg_col: str = None,
    agg_func: str = "count"
) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch analytics data from the analytics API with complete parameter support.
    
    Args:
        environment: The environment name (e.g., 'standard')
        ulid: The ULID identifier for the simulation
        event_type: Event type filter (default: '*' for all)
        group_by: List of fields to group by (default: ['element_label'])
        group_by_date: Date grouping specification (default: 'timestamp:year')
        aggregations: Aggregation specification (default: 'value:last')
        timeout: Request timeout in seconds
        filters: Dictionary of additional filter parameters with operators
        agg_col: Legacy single aggregation column
        agg_func: Legacy single aggregation function (default: 'count')
        
    Filter Format:
        filters = {
            "column_name": "exact_value",  # Exact match
            "column_name__eq": "value",    # Exact match
            "column_name__neq": "value",   # Not equal
            "column_name__gt": 100,        # Greater than
            "column_name__gte": 50,        # Greater than or equal
            "column_name__lt": 200,        # Less than
            "column_name__lte": 150,       # Less than or equal
            "column_name__in": ["A", "B"], # Multiple values (list or comma-separated string)
            "column_name__contains": "substring",  # Contains substring
            "timestamp__gte": "2020-01-01",        # Date filters
        }
        
    Returns:
        List[Dict]: Analytics data as JSON array, None if error
    """
    if group_by is None:
        group_by = ["element_label"]
    if filters is None:
        filters = {}
    
    # Build query parameters
    params = {
        "event_type": event_type,
        "group_by_date": group_by_date,
        "aggregations": aggregations
    }
    
    # Add legacy aggregation parameters if specified
    if agg_col:
        params["agg_col"] = agg_col
        params["agg_func"] = agg_func
    
    # Add filter parameters
    for key, value in filters.items():
        if key.endswith("__in") and isinstance(value, list):
            # Convert list to comma-separated string for __in filters
            params[key] = ",".join(str(v) for v in value)
        else:
            params[key] = value
    
    # Add multiple group_by parameters
    for field in group_by:
        if "group_by" not in params:
            params["group_by"] = field
        else:
            # Handle multiple group_by params - convert to list
            if isinstance(params["group_by"], str):
                params["group_by"] = [params["group_by"]]
            params["group_by"].append(field)
    
    url = f"{ANALYTICS_BASE_URL}/analytics/{environment}/{ulid}"
    
    print(f"🔍 Fetching analytics data from: {url}")
    print(f"📊 Environment: {environment}")
    print(f"🆔 ULID: {ulid}")
    print(f"📋 Parameters: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully fetched {len(data)} records")
            return data
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to analytics API. Check your internet connection.")
        return None
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after {timeout} seconds")
        return None
    except json.JSONDecodeError:
        print("❌ Invalid JSON response from analytics API")
        return None
    except Exception as e:
        print(f"❌ Unexpected error fetching analytics data: {e}")
        return None


def save_analytics_json(data: List[Dict[str, Any]], output_path: str) -> bool:
    """
    Save analytics data to JSON file.
    
    Args:
        data: Analytics data to save
        output_path: Path to save the JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Analytics data saved to: {output_path}")
        print(f"📊 Records saved: {len(data)}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving analytics JSON: {e}")
        return False


def build_filter_params(**kwargs) -> Dict[str, Any]:
    """
    Build filter parameters dictionary with operator support.
    
    Examples:
        # Exact matches
        build_filter_params(event_type="BALANCE_SET", status="active")
        
        # Comparison operators
        build_filter_params(value__gt=100, timestamp__gte="2020-01-01")
        
        # Multiple values
        build_filter_params(category__in=["A", "B", "C"])
        
        # Text searches
        build_filter_params(name__contains="test")
        
    Returns:
        Dict[str, Any]: Filter parameters ready for fetch_analytics_data
    """
    return kwargs


def fetch_analytics_with_defaults(
    environment: str,
    ulid: str,
    **overrides
) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch analytics data using the default query configuration.
    
    This function uses the DEFAULT_ANALYTICS_QUERY configuration but allows
    overriding any parameters. This is the primary function used by the
    validation system.
    
    Args:
        environment: The environment name (e.g., 'standard')
        ulid: The ULID identifier for the simulation
        **overrides: Override any default parameters
        
    Examples:
        # Use all defaults
        fetch_analytics_with_defaults("standard", "01ABC123")
        
        # Override specific parameters
        fetch_analytics_with_defaults("standard", "01ABC123", 
                                    event_type="BALANCE_SET",
                                    aggregations="value:sum")
        
    Returns:
        List[Dict]: Analytics data as JSON array, None if error
    """
    # Start with defaults and apply overrides
    params = DEFAULT_ANALYTICS_QUERY.copy()
    params.update(overrides)
    
    return fetch_analytics_data(
        environment=environment,
        ulid=ulid,
        event_type=params["event_type"],
        group_by=params["group_by"],
        group_by_date=params["group_by_date"],
        aggregations=params["aggregations"],
        filters=params["filters"]
    )


def fetch_analytics_with_filters(
    environment: str,
    ulid: str,
    **filter_kwargs
) -> Optional[List[Dict[str, Any]]]:
    """
    Convenience function to fetch analytics data with filters using keyword arguments.
    
    Args:
        environment: The environment name
        ulid: The ULID identifier
        **filter_kwargs: Filter parameters using column__operator syntax
        
    Examples:
        # Basic filtering
        fetch_analytics_with_filters("standard", "01ABC123", event_type="BALANCE_SET")
        
        # Advanced filtering
        fetch_analytics_with_filters(
            "standard", "01ABC123",
            event_type="* -> cost",
            value__gt=100,
            timestamp__gte="2020-01-01",
            element_label__in=["Population", "Deaths"]
        )
        
    Returns:
        List[Dict]: Analytics data as JSON array, None if error
    """
    filters = build_filter_params(**filter_kwargs)
    return fetch_analytics_data(environment=environment, ulid=ulid, filters=filters)


def fetch_and_save_analytics(
    environment: str,
    ulid: str, 
    output_path: str,
    **kwargs
) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch analytics data and save to JSON file.
    
    Args:
        environment: The environment name
        ulid: The ULID identifier
        output_path: Path to save the JSON file
        **kwargs: Additional parameters for fetch_analytics_data
        
    Returns:
        List[Dict]: The fetched data, None if error
    """
    data = fetch_analytics_data(environment, ulid, **kwargs)
    
    if data is not None:
        if save_analytics_json(data, output_path):
            return data
        else:
            return None
    
    return None
