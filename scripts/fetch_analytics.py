#!/usr/bin/env python3
"""
Fetch analytics data from analytics.forecasthealth.org API.

Usage:
    python3 fetch_analytics.py --ulids ULID1 ULID2 ULID3
    python3 fetch_analytics.py --csv validation_results.csv
    python3 fetch_analytics.py --all  # Use all ULIDs from validation_results.csv
    python3 fetch_analytics.py --ulids ULID1 --analytics-types edge_values_calculated balance_set
    python3 fetch_analytics.py --ulids ULID1 --analytics-types all
"""

import json
import csv
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
import time


def fetch_analytics_data(ulid, event_type="EDGE_VALUES_CALCULATED"):
    """Fetch analytics data for a given ULID and event type."""
    base_url = "https://analytics.forecasthealth.org/analytics/appendix_3"
    
    # Build URL with parameters
    url = f"{base_url}/{ulid}?group_by=element_label&group_by_date=timestamp%3Ayear&aggregations=value%3Asum&event_type={event_type}"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data, None
    except urllib.error.HTTPError as e:
        return None, f"HTTP Error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return None, f"URL Error: {e.reason}"
    except Exception as e:
        return None, f"Error: {str(e)}"


def load_ulids_from_csv(csv_path):
    """Load ULIDs and their associated scenarios from CSV file."""
    ulid_data = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'ulid' in row and 'scenario' in row:
                ulid_data.append({
                    'ulid': row['ulid'],
                    'scenario': row.get('scenario', 'unknown'),
                    'country': row.get('country', 'unknown')
                })
    return ulid_data


def save_response(data, ulid, scenario, event_type, output_dir):
    """Save JSON response to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if event_type == "EDGE_VALUES_CALCULATED":
        event_suffix = "edge"
    elif event_type == "BALANCE_SET":
        event_suffix = "balance"
    else:  # ECHO
        event_suffix = "echo"
    filename = f"{ulid}_{scenario}_{event_suffix}_{timestamp}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filepath


def main():
    parser = argparse.ArgumentParser(description='Fetch analytics data from forecasthealth.org')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ulids', nargs='+', 
                       help='List of ULIDs to fetch')
    group.add_argument('--csv', 
                       help='CSV file containing ULIDs')
    group.add_argument('--all', action='store_true',
                       help='Use all ULIDs from validation_results.csv')
    parser.add_argument('--output-dir', default='tmp',
                       help='Output directory for JSON files (default: tmp)')
    parser.add_argument('--delay', type=float, default=5.0,
                       help='Delay between requests in seconds (default: 5.0)')
    parser.add_argument('--analytics-types', nargs='+', 
                       choices=['edge_values_calculated', 'balance_set', 'echo', 'all'],
                       default=['echo'],
                       help='Analytics types to fetch (default: echo only). Use "all" to fetch all types.')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare ULID list
    ulid_list = []
    
    if args.ulids:
        # Direct ULID list - no scenario information
        for ulid in args.ulids:
            ulid_list.append({
                'ulid': ulid,
                'scenario': 'manual',
                'country': 'unknown'
            })
    elif args.csv or args.all:
        # Load from CSV
        csv_path = 'validation_results.csv' if args.all else args.csv
        csv_path = Path(csv_path)
        
        if not csv_path.exists():
            print(f"Error: CSV file not found: {csv_path}")
            return 1
        
        ulid_list = load_ulids_from_csv(csv_path)
        
        if not ulid_list:
            print(f"No ULIDs found in {csv_path}")
            return 1
    
    # Determine which analytics types to fetch
    if 'all' in args.analytics_types:
        event_types = ["EDGE_VALUES_CALCULATED", "BALANCE_SET", "ECHO"]
    else:
        type_mapping = {
            'edge_values_calculated': 'EDGE_VALUES_CALCULATED',
            'balance_set': 'BALANCE_SET', 
            'echo': 'ECHO'
        }
        event_types = [type_mapping[t] for t in args.analytics_types]
    
    total_requests = len(ulid_list) * len(event_types)
    print(f"Fetching data for {len(ulid_list)} ULIDs ({total_requests} total requests)...")
    print("-" * 60)
    
    successful = 0
    failed = 0
    request_num = 0
    
    for item in ulid_list:
        ulid = item['ulid']
        scenario = item['scenario']
        country = item['country']
        
        for event_type in event_types:
            request_num += 1
            if event_type == "EDGE_VALUES_CALCULATED":
                event_name = "EDGE"
            elif event_type == "BALANCE_SET":
                event_name = "BALANCE"
            else:
                event_name = "ECHO"
            print(f"[{request_num}/{total_requests}] Fetching {ulid} ({country}, {scenario}, {event_name})... ", end='', flush=True)
            
            data, error = fetch_analytics_data(ulid, event_type)
            
            if data:
                filepath = save_response(data, ulid, scenario, event_type, output_dir)
                print(f"✓ Saved to {filepath.name}")
                successful += 1
            else:
                print(f"✗ Failed: {error}")
                failed += 1
            
            # Add delay between requests (except for the last one)
            if request_num < total_requests and args.delay > 0:
                time.sleep(args.delay)
    
    # Summary
    print("-" * 60)
    print(f"Complete: {successful} successful, {failed} failed")
    if successful > 0:
        print(f"Results saved in: {output_dir}/")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())