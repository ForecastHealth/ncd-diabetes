#!/usr/bin/env python3
"""
Validate Changes CLI - Main entry point for the enhanced validation system.
"""
import sys
import argparse
import logging
import json
from .runner import EnhancedValidationRunner
from .db import ValidationDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Unified Validation and Query CLI")
    # Add arguments...
    parser.add_argument("--countries", nargs="+", help="Specific countries to run (ISO3 codes)")
    parser.add_argument("--scenarios", nargs="+", help="Specific scenarios to run (stem names)")
    parser.add_argument("--force", action="store_true", help="Force re-run all combinations")
    parser.add_argument("--environment", default="standard", help="API environment")
    parser.add_argument("--max-instances", type=int, default=100, help="Maximum concurrent instances")
    parser.add_argument("--model", default="model.json", help="Path to model file")
    parser.add_argument("--countries-file", default="countries/list_of_countries.json", help="Path to countries JSON file")
    parser.add_argument("--scenarios-dir", default="scenario-templates", help="Directory with scenario templates")
    parser.add_argument("--database", default="results.db", help="Path to validation database")
    parser.add_argument("--status", action="store_true", help="Show recent run status")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    runner = EnhancedValidationRunner(args.database)

    if args.status:
        db = ValidationDatabase(args.database)
        summary = db.get_latest_run_summary()
        if not summary:
            print("No validation runs found.")
            return
        print(json.dumps(summary, indent=2))
        if summary.get('failed_jobs', 0) > 0:
            print("\nFailed jobs:")
            failed = db.get_failed_jobs(summary['run_id'])
            for country, scenario in failed:
                print(f" - {country}/{scenario}")
        return

    # Default action: run validation
    runner.run(
        model_path=args.model,
        countries_file=args.countries_file,
        scenario_templates_dir=args.scenarios_dir,
        environment=args.environment,
        max_instances=args.max_instances,
        force_rerun=args.force,
        specific_countries=args.countries,
        specific_scenarios=args.scenarios
    )

if __name__ == "__main__":
    main()