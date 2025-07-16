#!/usr/bin/env python3
"""
Quick script to output the most recent run results for each country-scenario combination.
Sums DALYs values for each combination.
"""

import sqlite3
import sys
from pathlib import Path

def get_latest_results(db_path="results.db"):
    """
    Get the most recent run results for each country-scenario combination.
    
    Args:
        db_path: Path to the SQLite database
        
    Returns:
        List of tuples: (country, scenario, total_dalys)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query to get the most recent run for each country-scenario combination
    # and sum the DALYs values
    query = """
    WITH latest_runs AS (
        SELECT 
            country,
            scenario,
            MAX(run_id) as latest_run_id
        FROM metrics 
        WHERE element_label = 'Healthy Years Lived'
        GROUP BY country, scenario
    )
    SELECT 
        m.country,
        m.scenario,
        SUM(m.value) as HYL
    FROM metrics m
    JOIN latest_runs lr ON m.country = lr.country 
                        AND m.scenario = lr.scenario 
                        AND m.run_id = lr.latest_run_id
    WHERE m.element_label = 'Healthy Years Lived'
    GROUP BY m.country, m.scenario
    ORDER BY m.country, m.scenario
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    return results

def main():
    # Default to results.db in current directory
    db_path = "results.db"
    
    # Allow override from command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # Check if database exists
    if not Path(db_path).exists():
        print(f"Database {db_path} not found", file=sys.stderr)
        sys.exit(1)
    
    try:
        results = get_latest_results(db_path)
        
        if not results:
            print("No DALYs results found in database")
            return
        
        # Print header
        print("Country\tScenario\tTotal DALYs")
        print("-" * 50)
        
        # Print results
        for country, scenario, total_dalys in results:
            print(f"{country}\t{scenario}\t{total_dalys:,.2f}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
