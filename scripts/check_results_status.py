#!/usr/bin/env python3
"""
Check which validation results exist in tmp/ directory and identify duplicates.

This script compares the ULIDs in validation_results.csv with files in tmp/
to identify:
1. Which results have been fetched
2. Which results are missing
3. Any duplicate files for the same ULID/scenario combination
"""

import csv
import re
from pathlib import Path
from collections import defaultdict
import argparse


def load_validation_results(csv_path):
    """Load validation results from CSV file."""
    results = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'ulid': row['ulid'],
                'scenario': row['scenario'],
                'country': row['country'],
                'timestamp': row['timestamp']
            })
    return results


def parse_tmp_files(tmp_dir):
    """Parse tmp directory to extract file information."""
    tmp_path = Path(tmp_dir)
    if not tmp_path.exists():
        print(f"Error: tmp directory not found: {tmp_path}")
        return {}
    
    # Pattern: {ulid}_{scenario}_{event_type}_{timestamp}.json
    pattern = re.compile(r'^([0-9A-Z]{26})_([^_]+)_([^_]+)_(\d{8}_\d{6})\.json$')
    
    files_by_ulid_scenario = defaultdict(list)
    
    for file_path in tmp_path.glob('*.json'):
        match = pattern.match(file_path.name)
        if match:
            ulid, scenario, event_type, timestamp = match.groups()
            key = (ulid, scenario)
            files_by_ulid_scenario[key].append({
                'file': file_path.name,
                'ulid': ulid,
                'scenario': scenario,
                'event_type': event_type,
                'timestamp': timestamp,
                'path': file_path
            })
    
    return files_by_ulid_scenario


def check_status(validation_results, tmp_files, event_types=None):
    """Check status of validation results against tmp files."""
    if event_types is None:
        event_types = ['echo', 'edge', 'balance']
    
    status = {
        'exists': [],
        'missing': [],
        'duplicates': [],
        'partial': []  # Has some but not all event types
    }
    
    for result in validation_results:
        ulid = result['ulid']
        scenario = result['scenario']
        key = (ulid, scenario)
        
        if key in tmp_files:
            files = tmp_files[key]
            
            # Group by event type
            files_by_event = defaultdict(list)
            for file_info in files:
                files_by_event[file_info['event_type']].append(file_info)
            
            # Check for duplicates
            duplicates_found = []
            for event_type, event_files in files_by_event.items():
                if len(event_files) > 1:
                    duplicates_found.append({
                        'ulid': ulid,
                        'scenario': scenario,
                        'event_type': event_type,
                        'files': [f['file'] for f in event_files]
                    })
            
            if duplicates_found:
                status['duplicates'].extend(duplicates_found)
            
            # Check completeness
            existing_event_types = set(files_by_event.keys())
            expected_event_types = set(event_types)
            
            if existing_event_types == expected_event_types:
                status['exists'].append({
                    'ulid': ulid,
                    'scenario': scenario,
                    'country': result['country'],
                    'event_types': sorted(existing_event_types)
                })
            else:
                missing_types = expected_event_types - existing_event_types
                status['partial'].append({
                    'ulid': ulid,
                    'scenario': scenario,
                    'country': result['country'],
                    'has_types': sorted(existing_event_types),
                    'missing_types': sorted(missing_types)
                })
        else:
            status['missing'].append({
                'ulid': ulid,
                'scenario': scenario,
                'country': result['country']
            })
    
    return status


def print_summary(status, event_types):
    """Print a summary of the status check."""
    total = len(status['exists']) + len(status['missing']) + len(status['partial'])
    
    print("=" * 80)
    print("VALIDATION RESULTS STATUS SUMMARY")
    print("=" * 80)
    print(f"Expected event types: {', '.join(event_types)}")
    print(f"Total validation results: {total}")
    print()
    
    # Complete results
    print(f"✓ Complete results: {len(status['exists'])}")
    if status['exists'] and len(status['exists']) <= 10:
        for item in status['exists'][:10]:
            print(f"  - {item['ulid']} ({item['country']}, {item['scenario']})")
        if len(status['exists']) > 10:
            print(f"  ... and {len(status['exists']) - 10} more")
    
    # Partial results
    print(f"⚠ Partial results: {len(status['partial'])}")
    if status['partial']:
        for item in status['partial'][:5]:
            print(f"  - {item['ulid']} ({item['country']}, {item['scenario']}) - has: {', '.join(item['has_types'])}, missing: {', '.join(item['missing_types'])}")
        if len(status['partial']) > 5:
            print(f"  ... and {len(status['partial']) - 5} more")
    
    # Missing results
    print(f"✗ Missing results: {len(status['missing'])}")
    if status['missing']:
        for item in status['missing'][:5]:
            print(f"  - {item['ulid']} ({item['country']}, {item['scenario']})")
        if len(status['missing']) > 5:
            print(f"  ... and {len(status['missing']) - 5} more")
    
    # Duplicates
    print(f"⚠ Duplicate files: {len(status['duplicates'])}")
    if status['duplicates']:
        for dup in status['duplicates'][:5]:
            print(f"  - {dup['ulid']} ({dup['scenario']}, {dup['event_type']}): {len(dup['files'])} files")
            for file in dup['files']:
                print(f"    * {file}")
        if len(status['duplicates']) > 5:
            print(f"  ... and {len(status['duplicates']) - 5} more")
    
    print()
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Check validation results status in tmp directory')
    parser.add_argument('--csv', default='validation_results.csv',
                       help='Path to validation results CSV file (default: validation_results.csv)')
    parser.add_argument('--tmp-dir', default='tmp',
                       help='Path to tmp directory (default: tmp)')
    parser.add_argument('--event-types', nargs='+', 
                       choices=['echo', 'edge', 'balance'],
                       default=['echo', 'edge', 'balance'],
                       help='Event types to check for (default: all)')
    parser.add_argument('--show-missing', action='store_true',
                       help='Show detailed list of missing results')
    parser.add_argument('--show-duplicates', action='store_true',
                       help='Show detailed list of duplicate files')
    parser.add_argument('--show-partial', action='store_true',
                       help='Show detailed list of partial results')
    
    args = parser.parse_args()
    
    # Load validation results
    try:
        validation_results = load_validation_results(args.csv)
        print(f"Loaded {len(validation_results)} validation results from {args.csv}")
    except FileNotFoundError:
        print(f"Error: Could not find {args.csv}")
        return 1
    except Exception as e:
        print(f"Error loading {args.csv}: {e}")
        return 1
    
    # Parse tmp files
    tmp_files = parse_tmp_files(args.tmp_dir)
    total_files = sum(len(files) for files in tmp_files.values())
    print(f"Found {total_files} files in {args.tmp_dir} for {len(tmp_files)} ULID/scenario combinations")
    print()
    
    # Check status
    status = check_status(validation_results, tmp_files, args.event_types)
    
    # Print summary
    print_summary(status, args.event_types)
    
    # Show detailed lists if requested
    if args.show_missing and status['missing']:
        print("DETAILED MISSING RESULTS:")
        print("-" * 40)
        for item in status['missing']:
            print(f"{item['ulid']} | {item['country']} | {item['scenario']}")
        print()
    
    if args.show_duplicates and status['duplicates']:
        print("DETAILED DUPLICATE FILES:")
        print("-" * 40)
        for dup in status['duplicates']:
            print(f"{dup['ulid']} ({dup['scenario']}, {dup['event_type']}):")
            for file in dup['files']:
                print(f"  - {file}")
        print()
    
    if args.show_partial and status['partial']:
        print("DETAILED PARTIAL RESULTS:")
        print("-" * 40)
        for item in status['partial']:
            print(f"{item['ulid']} | {item['country']} | {item['scenario']}")
            print(f"  Has: {', '.join(item['has_types'])}")
            print(f"  Missing: {', '.join(item['missing_types'])}")
        print()
    
    return 0


if __name__ == "__main__":
    exit(main())