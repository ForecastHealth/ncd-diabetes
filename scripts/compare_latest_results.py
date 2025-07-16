#!/usr/bin/env python3
"""
Script to compare results between two scenarios by calculating comparison minus baseline.
Shows the difference in DALYs values for each country where both scenarios have results.
"""

import sqlite3
import sys
import argparse
from pathlib import Path

def get_scenario_results(db_path, scenario):
    """
    Get the most recent run results for a specific scenario across all countries.
    
    Args:
        db_path: Path to the SQLite database
        scenario: Name of the scenario to retrieve
        
    Returns:
        Dict mapping country to total DALYs: {country: total_dalys}
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query to get the most recent run for each country for the specified scenario
    query = """
    WITH latest_runs AS (
        SELECT 
            country,
            scenario,
            MAX(run_id) as latest_run_id
        FROM metrics 
        WHERE element_label = 'Healthy Years Lived'
            AND scenario = ?
        GROUP BY country, scenario
    )
    SELECT 
        m.country,
        SUM(m.value) as HYL
    FROM metrics m
    JOIN latest_runs lr ON m.country = lr.country 
                        AND m.scenario = lr.scenario 
                        AND m.run_id = lr.latest_run_id
    WHERE m.element_label = 'Healthy Years Lived'
        AND m.scenario = ?
    GROUP BY m.country
    ORDER BY m.country
    """
    
    cursor.execute(query, (scenario, scenario))
    results = cursor.fetchall()
    conn.close()
    
    return {country: dalys for country, dalys in results}

def compare_scenarios(db_path, baseline_scenario, comparison_scenario):
    """
    Compare two scenarios by calculating comparison minus baseline.
    
    Args:
        db_path: Path to the SQLite database
        baseline_scenario: Name of the baseline scenario
        comparison_scenario: Name of the comparison scenario
        
    Returns:
        List of tuples: (country, difference)
    """
    baseline_results = get_scenario_results(db_path, baseline_scenario)
    comparison_results = get_scenario_results(db_path, comparison_scenario)
    
    # Find countries that exist in both scenarios
    common_countries = set(baseline_results.keys()) & set(comparison_results.keys())
    
    if not common_countries:
        return []
    
    # Calculate differences
    differences = []
    for country in sorted(common_countries):
        baseline_dalys = baseline_results[country]
        comparison_dalys = comparison_results[country]
        difference = comparison_dalys - baseline_dalys
        differences.append((country, difference))
    
    return differences

def main():
    parser = argparse.ArgumentParser(
        description="Compare DALYs results between two scenarios (comparison minus baseline)"
    )
    parser.add_argument(
        "--baseline", 
        required=True, 
        help="Name of the baseline scenario"
    )
    parser.add_argument(
        "--comparison", 
        required=True, 
        help="Name of the comparison scenario"
    )
    parser.add_argument(
        "--db", 
        default="results.db", 
        help="Path to the SQLite database (default: results.db)"
    )
    
    args = parser.parse_args()
    
    # Check if database exists
    if not Path(args.db).exists():
        print(f"Database {args.db} not found", file=sys.stderr)
        sys.exit(1)
    
    try:
        differences = compare_scenarios(args.db, args.baseline, args.comparison)
        
        if not differences:
            print(f"No common countries found with results for both scenarios:")
            print(f"  Baseline: {args.baseline}")
            print(f"  Comparison: {args.comparison}")
            return
        
        # Print header
        print(f"Comparison: {args.comparison} minus {args.baseline}")
        print("Country\tDifference in Healthy Years Lived")
        print("-" * 50)
        
        # Print results
        for country, difference in differences:
            print(f"{country}\t{difference:,.2f}")
        
        # Print summary statistics
        print("-" * 50)
        total_difference = sum(diff for _, diff in differences)
        avg_difference = total_difference / len(differences)
        print(f"Total difference: {total_difference:,.2f}")
        print(f"Average difference: {avg_difference:,.2f}")
        print(f"Countries compared: {len(differences)}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()