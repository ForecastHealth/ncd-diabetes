#!/usr/bin/env python3
"""
Script to compare latest model results with Appendix 3 reference data.
Runs compare_latest_results.py for null vs c1 and null vs c3, then compares
the outputs with the reference values from data/asthma_impact_a3.csv.
"""

import subprocess
import sys
import csv
from pathlib import Path
import re

def run_comparison(baseline, comparison):
    """
    Run compare_latest_results.py and capture the output.
    
    Args:
        baseline: Baseline scenario name
        comparison: Comparison scenario name
        
    Returns:
        Dict mapping country ISO3 to difference value
    """
    cmd = [
        sys.executable,
        "scripts/compare_latest_results.py",
        "--baseline", baseline,
        "--comparison", comparison
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout
        
        # Parse the output to extract country and difference values
        results = {}
        lines = output.strip().split('\n')
        
        # Skip header lines and find data
        data_started = False
        for line in lines:
            if line.startswith('-' * 40):
                if data_started:
                    break  # End of data section
                else:
                    data_started = True
                    continue
                    
            if data_started and '\t' in line:
                parts = line.split('\t')
                if len(parts) == 2:
                    country = parts[0].strip()
                    try:
                        value = float(parts[1].replace(',', ''))
                        results[country] = value
                    except ValueError:
                        continue
        
        return results
        
    except subprocess.CalledProcessError as e:
        print(f"Error running comparison: {e}")
        print(f"Error output: {e.stderr}")
        return {}

def load_appendix_3_data():
    """
    Load reference data from asthma_impact_a3.csv.
    
    Returns:
        Dict with structure: {country: {'CR1': value, 'CR3': value}}
    """
    csv_path = Path("data/asthma_impact_a3.csv")
    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        return {}
    
    data = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            iso3 = row['ISO3']
            if iso3:
                cr1_str = row['CR1'].replace(',', '')
                cr3_str = row['CR3'].replace(',', '')
                data[iso3] = {
                    'CR1': float(cr1_str) if cr1_str and cr1_str != '0' else 0,
                    'CR3': float(cr3_str) if cr3_str and cr3_str != '0' else 0
                }
    
    return data

def main():
    print("Comparing latest model results with Appendix 3 reference data")
    print("=" * 70)
    
    # Run comparisons
    print("\nRunning null vs asthma_cr1_scenario comparison...")
    c1_results = run_comparison("asthma_null_scenario", "asthma_cr1_scenario")
    
    print("\nRunning null vs asthma_cr3_scenario comparison...")
    c3_results = run_comparison("asthma_null_scenario", "asthma_cr3_scenario")
    
    # Load reference data
    print("\nLoading Appendix 3 reference data...")
    appendix_3_data = load_appendix_3_data()
    
    if not c1_results and not c3_results:
        print("Error: No results from model comparisons")
        return
        
    if not appendix_3_data:
        print("Error: No reference data loaded")
        return
    
    # Compare results
    print("\n" + "=" * 70)
    print("Comparison Results (Model/Reference Ratio)")
    print("=" * 70)
    print(f"{'Country':<10} {'CR1 Model':<15} {'CR1 Ref':<15} {'CR1 Ratio':<12} {'CR3 Model':<15} {'CR3 Ref':<15} {'CR3 Ratio':<12}")
    print("-" * 95)
    
    # Find common countries
    all_countries = set()
    all_countries.update(c1_results.keys())
    all_countries.update(c3_results.keys())
    all_countries.update(appendix_3_data.keys())
    
    total_c1_model = 0
    total_c1_ref = 0
    total_c3_model = 0
    total_c3_ref = 0
    c1_count = 0
    c3_count = 0
    
    for country in sorted(all_countries):
        c1_model = c1_results.get(country, 0)
        c3_model = c3_results.get(country, 0)
        
        ref_data = appendix_3_data.get(country, {})
        c1_ref = ref_data.get('CR1', 0)
        c3_ref = ref_data.get('CR3', 0)
        
        # Calculate ratios
        c1_ratio = c1_model / c1_ref if c1_ref != 0 else float('inf') if c1_model != 0 else 0
        c3_ratio = c3_model / c3_ref if c3_ref != 0 else float('inf') if c3_model != 0 else 0
        
        # Format output
        c1_model_str = f"{c1_model:,.0f}" if c1_model != 0 else "-"
        c3_model_str = f"{c3_model:,.0f}" if c3_model != 0 else "-"
        c1_ref_str = f"{c1_ref:,.0f}" if c1_ref != 0 else "-"
        c3_ref_str = f"{c3_ref:,.0f}" if c3_ref != 0 else "-"
        c1_ratio_str = f"{c1_ratio:.4f}" if c1_ratio not in [0, float('inf')] else "-"
        c3_ratio_str = f"{c3_ratio:.4f}" if c3_ratio not in [0, float('inf')] else "-"
        
        print(f"{country:<10} {c1_model_str:<15} {c1_ref_str:<15} {c1_ratio_str:<12} {c3_model_str:<15} {c3_ref_str:<15} {c3_ratio_str:<12}")
        
        # Update totals
        if c1_model != 0 and c1_ref != 0:
            total_c1_model += c1_model
            total_c1_ref += c1_ref
            c1_count += 1
            
        if c3_model != 0 and c3_ref != 0:
            total_c3_model += c3_model
            total_c3_ref += c3_ref
            c3_count += 1
    
    # Summary statistics
    print("-" * 95)
    print("\nSummary Statistics:")
    print("-" * 30)
    
    if c1_count > 0:
        overall_c1_ratio = total_c1_model / total_c1_ref
        print(f"CR1 - Countries compared: {c1_count}")
        print(f"CR1 - Total Model HYL: {total_c1_model:,.0f}")
        print(f"CR1 - Total Ref HYL: {total_c1_ref:,.0f}")
        print(f"CR1 - Overall Ratio: {overall_c1_ratio:.4f}")
    
    if c3_count > 0:
        overall_c3_ratio = total_c3_model / total_c3_ref
        print(f"\nCR3 - Countries compared: {c3_count}")
        print(f"CR3 - Total Model HYL: {total_c3_model:,.0f}")
        print(f"CR3 - Total Ref HYL: {total_c3_ref:,.0f}")
        print(f"CR3 - Overall Ratio: {overall_c3_ratio:.4f}")

if __name__ == "__main__":
    main()