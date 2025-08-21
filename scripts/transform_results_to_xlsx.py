#!/usr/bin/env python3
"""
Transform results CSV to Excel workbook with scenario-based worksheets.

Usage:
    python3 transform_results_to_xlsx.py --csv results/analytics_results_20250821_102932.csv
"""

import argparse
import csv
import pandas as pd
from pathlib import Path
from collections import defaultdict
import re


def load_csv_data(csv_path):
    """Load CSV data and organize by scenario."""
    data_by_scenario = defaultdict(list)
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scenario = row['scenario']
            data_by_scenario[scenario].append(row)
    
    return data_by_scenario


def extract_scenario_code(scenario_name):
    """Extract scenario code from scenario name (e.g., 'asthma_cr1' -> 'cr1')."""
    # Look for common patterns like cr1, t1, d1, etc.
    match = re.search(r'([a-z]+\d+[a-z]*)', scenario_name.lower())
    if match:
        return match.group(1)
    return scenario_name


def create_scenario_worksheet(writer, scenario_name, data, sheet_name):
    """Create a worksheet for a specific scenario."""
    df = pd.DataFrame(data)
    
    # Ensure proper data types
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df['cum_value'] = pd.to_numeric(df['cum_value'], errors='coerce')
    df['year'] = pd.to_datetime(df['year'])
    
    # Sort by country, metric, year for consistency
    df = df.sort_values(['country', 'metric', 'year'])
    
    # Write to Excel worksheet
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    return df


def create_total_worksheet(writer, scenario_name, data, sheet_name):
    """Create a total worksheet that sums all countries for a scenario."""
    df = pd.DataFrame(data)
    
    # Ensure proper data types
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df['cum_value'] = pd.to_numeric(df['cum_value'], errors='coerce')
    df['year'] = pd.to_datetime(df['year'])
    
    # Group by scenario, metric, year and sum the values
    total_df = df.groupby(['scenario', 'metric', 'year']).agg({
        'value': 'sum',
        'cum_value': 'sum'
    }).reset_index()
    
    # Add a country column to indicate this is totaled
    total_df['country'] = 'TOTAL'
    
    # Reorder columns to match original structure
    total_df = total_df[['country', 'scenario', 'metric', 'year', 'value', 'cum_value']]
    
    # Sort by metric, year
    total_df = total_df.sort_values(['metric', 'year'])
    
    # Write to Excel worksheet
    total_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    return total_df


def main():
    parser = argparse.ArgumentParser(description='Transform results CSV to Excel workbook')
    parser.add_argument('--csv', required=True,
                       help='Path to the results CSV file')
    parser.add_argument('--output', 
                       help='Output Excel file path (default: derived from input)')
    
    args = parser.parse_args()
    
    # Validate input file
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        return 1
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = csv_path.parent / f"{csv_path.stem}.xlsx"
    
    print(f"Loading data from: {csv_path}")
    
    # Load and organize data
    data_by_scenario = load_csv_data(csv_path)
    
    if not data_by_scenario:
        print("No data found in CSV file")
        return 1
    
    print(f"Found {len(data_by_scenario)} scenarios")
    
    # Create Excel workbook
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for scenario_name, scenario_data in sorted(data_by_scenario.items()):
            scenario_code = extract_scenario_code(scenario_name)
            
            print(f"Processing scenario: {scenario_name} -> {scenario_code}")
            
            # Create scenario worksheet
            scenario_sheet = scenario_code
            # Ensure sheet name is valid (max 31 chars, no special chars)
            scenario_sheet = re.sub(r'[^\w\-_\.]', '_', scenario_sheet)[:31]
            
            create_scenario_worksheet(writer, scenario_name, scenario_data, scenario_sheet)
            print(f"  ✓ Created worksheet: {scenario_sheet}")
            
            # Create total worksheet
            total_sheet = f"total_{scenario_code}"
            total_sheet = re.sub(r'[^\w\-_\.]', '_', total_sheet)[:31]
            
            create_total_worksheet(writer, scenario_name, scenario_data, total_sheet)
            print(f"  ✓ Created total worksheet: {total_sheet}")
    
    print(f"\n✓ Excel workbook created: {output_path}")
    print(f"✓ Total worksheets created: {len(data_by_scenario) * 2}")
    
    return 0


if __name__ == "__main__":
    exit(main())