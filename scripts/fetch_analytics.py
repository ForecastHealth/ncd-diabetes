#!/usr/bin/env python3
"""
Fetch analytics data from localhost:8000 API with concurrent requests.

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
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
import time


async def fetch_analytics_data(session, ulid, event_type="EDGE_VALUES_CALCULATED"):
    """Fetch analytics data for a given ULID and event type using async HTTP."""
    base_url = "http://localhost:8000/analytics/appendix_3"
    
    # Build URL with parameters
    url = f"{base_url}/{ulid}?group_by=element_label&group_by_date=timestamp%3Ayear&aggregations=value%3Asum&event_type={event_type}"
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data, None
            else:
                return None, f"HTTP Error {response.status}: {response.reason}"
    except aiohttp.ClientError as e:
        return None, f"Client Error: {str(e)}"
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


async def save_response(data, ulid, scenario, event_type, output_dir):
    """Save JSON response to file asynchronously."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if event_type == "EDGE_VALUES_CALCULATED":
        event_suffix = "edge"
    elif event_type == "BALANCE_SET":
        event_suffix = "balance"
    else:  # ECHO
        event_suffix = "echo"
    filename = f"{ulid}_{scenario}_{event_suffix}_{timestamp}.json"
    filepath = output_dir / filename
    
    # Use asyncio for file I/O to avoid blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _write_json_file, filepath, data)
    
    return filepath

def _write_json_file(filepath, data):
    """Helper function to write JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


async def process_request(session, semaphore, ulid_item, event_type, output_dir, request_num, total_requests):
    """Process a single request with semaphore for concurrency control."""
    async with semaphore:
        ulid = ulid_item['ulid']
        scenario = ulid_item['scenario']
        country = ulid_item['country']
        
        if event_type == "EDGE_VALUES_CALCULATED":
            event_name = "EDGE"
        elif event_type == "BALANCE_SET":
            event_name = "BALANCE"
        else:
            event_name = "ECHO"
        
        print(f"[{request_num}/{total_requests}] Fetching {ulid} ({country}, {scenario}, {event_name})... ", end='', flush=True)
        
        data, error = await fetch_analytics_data(session, ulid, event_type)
        
        if data:
            filepath = await save_response(data, ulid, scenario, event_type, output_dir)
            print(f"✓ Saved to {filepath.name}")
            return True
        else:
            print(f"✗ Failed: {error}")
            return False

async def main_async(args):
    """Main async function that handles concurrent requests."""
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
    print(f"Using {args.concurrency} concurrent connections...")
    print("-" * 60)
    
    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(args.concurrency)
    
    # Setup HTTP session with connection pooling
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(limit=args.concurrency, limit_per_host=args.concurrency)
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        # Create all tasks
        tasks = []
        request_num = 0
        
        for item in ulid_list:
            for event_type in event_types:
                request_num += 1
                task = process_request(session, semaphore, item, event_type, output_dir, request_num, total_requests)
                tasks.append(task)
        
        # Execute tasks in batches to respect API cleanup cycle
        start_time = time.time()
        batch_size = args.concurrency
        batch_delay = 6  # Wait 6 seconds between batches for API cleanup
        
        all_results = []
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(tasks) + batch_size - 1) // batch_size
            
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} requests)...")
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            all_results.extend(batch_results)
            
            # Wait between batches (except for the last one) to let API cleanup
            if i + batch_size < len(tasks):
                print(f"Waiting {batch_delay} seconds for API cleanup...")
                await asyncio.sleep(batch_delay)
        
        end_time = time.time()
        
        # Count results
        successful = sum(1 for result in all_results if result is True)
        failed = len(all_results) - successful
        
        # Summary
        print("-" * 60)
        print(f"Complete: {successful} successful, {failed} failed")
        print(f"Total time: {end_time - start_time:.2f} seconds")
        if successful > 0:
            print(f"Results saved in: {output_dir}/")
        
        return 0 if failed == 0 else 1

def main():
    parser = argparse.ArgumentParser(description='Fetch analytics data from localhost:3000 with concurrent requests')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ulids', nargs='+', 
                       help='List of ULIDs to fetch')
    group.add_argument('--csv', 
                       help='CSV file containing ULIDs')
    group.add_argument('--all', action='store_true',
                       help='Use all ULIDs from validation_results.csv')
    parser.add_argument('--output-dir', default='tmp',
                       help='Output directory for JSON files (default: tmp)')
    parser.add_argument('--concurrency', type=int, default=15,
                       help='Number of concurrent requests (default: 15)')
    parser.add_argument('--analytics-types', nargs='+', 
                       choices=['edge_values_calculated', 'balance_set', 'echo', 'all'],
                       default=['echo'],
                       help='Analytics types to fetch (default: echo only). Use "all" to fetch all types.')
    
    args = parser.parse_args()
    
    # Run the async main function
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    exit(main())
