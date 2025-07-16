#!/usr/bin/env python3
"""
Enhanced Multi-Country Validation Runner

This script orchestrates validation runs across all countries and scenarios,
with database integration for tracking results and incremental execution.
"""
import os
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from .db import ValidationDatabase
from .country_utils import load_countries_list
from .multi_country import validate_multiple_countries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedValidationRunner:
    """
    Enhanced validation runner with database integration and incremental execution.
    """
    def __init__(self, db_path: str = "results.db"):
        self.db = ValidationDatabase(db_path)
        self.db_path = db_path

    def get_git_commit(self) -> str:
        try:
            return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
        except subprocess.CalledProcessError:
            logger.warning("Could not get git commit hash")
            return "unknown"

    def discover_scenarios(self, scenario_templates_dir: str = "scenario-templates") -> List[str]:
        scenario_dir = Path(scenario_templates_dir)
        if not scenario_dir.exists():
            logger.error(f"Scenario templates directory not found: {scenario_dir}")
            return []
        scenarios = [str(f) for f in scenario_dir.glob("*.json")]
        logger.info(f"Discovered {len(scenarios)} scenario templates")
        return scenarios

    def load_countries(self, countries_file: str = "list_of_countries.json") -> List[Dict[str, str]]:
        try:
            countries = load_countries_list(countries_file)
            logger.info(f"Loaded {len(countries)} countries")
            return countries
        except Exception as e:
            logger.error(f"Failed to load countries: {e}")
            return []

    def generate_all_combinations(self, countries: List[Dict[str, str]], scenarios: List[str]) -> List[Tuple[str, str, str]]:
        combinations = []
        for country in countries:
            for scenario_path in scenarios:
                scenario_name = Path(scenario_path).stem
                combinations.append((country['iso3'], scenario_name, scenario_path))
        logger.info(f"Generated {len(combinations)} country/scenario combinations")
        return combinations

    def filter_combinations_needing_rerun(self, combinations: List[Tuple[str, str, str]], git_commit: str) -> List[Tuple[str, str, str]]:
        needed = [combo for combo in combinations if self.db.needs_rerun(combo[0], combo[1], git_commit)]
        logger.info(f"Found {len(needed)} combinations needing rerun")
        return needed

    def run_validation_for_scenario_group(self, model_path: str, scenario_path: str, countries_to_run: List[Dict[str, str]], environment: str, max_instances: int, **kwargs) -> bool:
        scenario_name = Path(scenario_path).stem
        logger.info(f"Running validation for scenario: {scenario_name} across {len(countries_to_run)} countries.")
        
        # Create a temporary file containing only the countries for this run
        temp_countries_path = f"temp_countries_{scenario_name}.json"
        with open(temp_countries_path, 'w') as f:
            json.dump({"countries": countries_to_run}, f)

        try:
            success = validate_multiple_countries(
                model_path=model_path,
                scenario_path=scenario_path,
                countries_path=temp_countries_path,
                environment=environment,
                poll_interval=3,
                max_wait_time=7200,
                skip_api_test=False,
                no_cleanup=False,
                verbose=True,
                generate_analytics=True,
                max_instances=max_instances,
                database_path=self.db_path,
                **kwargs
            )
        finally:
            if os.path.exists(temp_countries_path):
                os.remove(temp_countries_path)
        
        return success

    def run(self, model_path: str, countries_file: str, scenario_templates_dir: str, environment: str, max_instances: int, force_rerun: bool, specific_countries: Optional[List[str]], specific_scenarios: Optional[List[str]], **kwargs) -> Dict[str, Any]:
        logger.info("Starting enhanced validation run")
        git_commit = self.get_git_commit()
        logger.info(f"Current git commit: {git_commit}")

        all_scenarios = self.discover_scenarios(scenario_templates_dir)
        if not all_scenarios:
            return {"success": False, "error": "No scenarios found"}

        all_countries = self.load_countries(countries_file)
        if not all_countries:
            return {"success": False, "error": "No countries found"}

        # Filter based on specific requests
        scenarios_to_run = [s for s in all_scenarios if not specific_scenarios or Path(s).stem in specific_scenarios]
        countries_to_run = [c for c in all_countries if not specific_countries or c['iso3'] in specific_countries]
        
        logger.info(f"Targeting {len(scenarios_to_run)} scenarios and {len(countries_to_run)} countries.")

        # Group combinations by scenario for efficient processing
        scenario_groups = {}
        for scenario_path in scenarios_to_run:
            scenario_name = Path(scenario_path).stem
            combinations = self.generate_all_combinations(countries_to_run, [scenario_path])
            
            if not force_rerun:
                combinations = self.filter_combinations_needing_rerun(combinations, git_commit)
            
            if combinations:
                # Get the full country dicts for the combinations that need running
                iso3_to_run = {combo[0] for combo in combinations}
                countries_for_this_scenario = [c for c in countries_to_run if c['iso3'] in iso3_to_run]
                scenario_groups[scenario_name] = {
                    "scenario_path": scenario_path,
                    "countries": countries_for_this_scenario
                }

        if not scenario_groups:
            logger.info("All targeted combinations are up-to-date. Nothing to run.")
            return {"success": True, "message": "All combinations up to date"}

        total_jobs_to_run = sum(len(group['countries']) for group in scenario_groups.values())
        run_id = self.db.start_validation_run(git_commit, total_jobs_to_run)
        logger.info(f"Started validation run {run_id} with {total_jobs_to_run} jobs.")

        successful_runs = 0
        failed_runs = 0
        for scenario, group_info in scenario_groups.items():
            try:
                # Pass the run_id to the validation function
                kwargs_with_runid = {**kwargs, 'run_id': run_id}
                success = self.run_validation_for_scenario_group(
                    model_path, group_info["scenario_path"], group_info["countries"], environment, max_instances, **kwargs_with_runid
                )
                if success:
                    successful_runs +=1
                    logger.info(f"✅ Scenario group {scenario} completed successfully.")
                else:
                    failed_runs += 1
                    logger.error(f"❌ Scenario group {scenario} failed.")
            except Exception as e:
                failed_runs += 1
                logger.error(f"❌ Unhandled exception processing scenario {scenario}: {e}", exc_info=True)
        
        # This is tricky because job status is now recorded inside `validate_multiple_countries`. 
        # We will refetch counts from the DB for the final summary.
        with self.db.get_connection() as conn:
            res = conn.execute("SELECT successful_jobs, failed_jobs FROM validation_runs WHERE run_id = ?", (run_id,)).fetchone()
            final_successful, final_failed = res[0], res[1]

        final_status = "completed" if final_failed == 0 else "failed"
        self.db.update_run_status(run_id, final_status, final_successful, final_failed)

        return {
            "success": final_failed == 0,
            "run_id": run_id,
            "total_jobs": total_jobs_to_run,
            "successful_jobs": final_successful,
            "failed_jobs": final_failed
        }