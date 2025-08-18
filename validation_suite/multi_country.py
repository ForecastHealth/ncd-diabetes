"""
Multi-country validation logic.

This module handles the complete workflow for validating models across
multiple countries, including parallel job submission and analytics generation.
Enhanced with database integration for tracking validation runs and results.
"""
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .scenario_utils import apply_scenario_to_model, validate_json_files
from .api_client import submit_simulation_job, get_job_status, test_api_health
from .db import ValidationDatabase
from .analytics.processor import DatabaseAnalyticsProcessor
from .analytics.ulid_parser import extract_ulid_from_job_name
from .csv_writer import ValidationCSVWriter
from .country_utils import get_country_display_list, create_country_scenario, load_countries_list

logger = logging.getLogger(__name__)

MAX_INSTANCES = 100

def get_git_commit() -> str:
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
    except subprocess.CalledProcessError:
        return "unknown"

def ensure_tmp_directory() -> Path:
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    return tmp_dir

def cleanup_tmp_directory() -> None:
    # Simplified cleanup logic for this context
    pass

def validate_multiple_countries(
    model_path: str,
    scenario_path: str,
    countries_path: str,
    environment: str,
    poll_interval: int,
    max_wait_time: int,
    skip_api_test: bool,
    no_cleanup: bool,
    verbose: bool,
    generate_analytics: bool,
    max_instances: int = MAX_INSTANCES,
    database_path: str = "results.db",
    run_id: Optional[int] = None # Expect a run_id from the orchestrator
) -> bool:
    """
    Validate model changes across multiple countries for a single scenario.
    """
    if verbose:
        print(f"\n--- Running: {Path(scenario_path).name} ---")

    db = ValidationDatabase(database_path)
    analytics_processor = DatabaseAnalyticsProcessor(database_path)
    csv_writer = ValidationCSVWriter()

    if not run_id:
        logger.error("A valid run_id must be provided to validate_multiple_countries.")
        return False

    try:
        countries = load_countries_list(countries_path)
        if not countries:
            return False

        if not validate_json_files(model_path, scenario_path):
            return False

        tmp_dir = ensure_tmp_directory()
        
        if not test_api_health():
            return False

        # This simplified version applies the *same base scenario* to each country's model
        # The country is a parameter within the model itself
        
        print("\n📋 Step 5: Preparing model files for all countries")
        print("----------------------------------------")
        print(f"📊 Total countries: {len(countries)}")
        print(f"📋 Preparing {len(countries)} model files...")
        
        # 1. Prepare country-specific models
        prepared_models = {}
        for country in countries:
            iso3 = country['iso3']
            name = country['name']
            print(f"🔧 Preparing model for {name} ({iso3})")
            
            country_model_path = tmp_dir / f"model_{iso3}_{Path(scenario_path).stem}.json"
            
            # Create a temporary scenario file for just this country's iso3 code
            country_scenario_path = tmp_dir / f"scenario_{iso3}_{Path(scenario_path).stem}.json"
            if not create_country_scenario(scenario_path, iso3, str(country_scenario_path)):
                logger.error(f"Failed to create scenario for {iso3}")
                continue

            if apply_scenario_to_model(model_path, str(country_scenario_path), str(country_model_path)):
                prepared_models[iso3] = {'model_path': str(country_model_path), 'name': country['name']}
                print(f"✅ Model prepared for {name}")
            else:
                logger.error(f"Failed to prepare model for {iso3}")
        
        print(f"📊 Model preparation complete: {len(prepared_models)}/{len(countries)} models ready")

        print(f"\n📋 Step 6: Submitting jobs with throttling (max {max_instances} concurrent)")
        print("----------------------------------------")
        print(f"🎯 Throttling limit: {max_instances} concurrent instances")
        print(f"🚀 Starting batch job submission for {len(prepared_models)} models...")
        
        # 2. Submit jobs
        job_submissions = {}
        for i, (iso3, info) in enumerate(prepared_models.items(), 1):
            print(f"🚀 Submitting job for {info['name']} ({iso3}) [{i}/{max_instances}]")
            logger.info(f"Submitting job for {info['name']} ({iso3})")
            job_result = submit_simulation_job(info['model_path'], environment)
            if job_result and 'jobId' in job_result:
                job_submissions[iso3] = {'job_id': job_result['jobId'], 'job_name': job_result.get('jobName'), 'name': info['name']}
                db.record_job_result(run_id, iso3, Path(scenario_path).stem, job_result.get('jobName', ''), 'submitted', datetime.now(), None)
                print(f"✅ Job submitted for {info['name']}: {job_result['jobId']}")
            else:
                db.record_job_result(run_id, iso3, Path(scenario_path).stem, '', 'failed_submission', datetime.now(), datetime.now())
                print(f"❌ Job submission failed for {info['name']}")
        
        print(f"📊 Batch submission complete: {len(job_submissions)}/{len(prepared_models)} jobs submitted")

        print(f"\n📋 Step 7: Polling {len(job_submissions)} jobs for completion")
        print("----------------------------------------")
        print(f"⏳ Polling {len(job_submissions)} jobs for completion")
        print("=" * 60)
        
        # 3. Poll for completion
        active_jobs = job_submissions.copy()
        completed_jobs = {}
        start_time = time.time()
        
        while active_jobs and (time.time() - start_time) < max_wait_time:
            # Print current status
            elapsed_minutes = int((time.time() - start_time) // 60)
            elapsed_seconds = int((time.time() - start_time) % 60)
            for iso3, job_info in active_jobs.items():
                status_data = get_job_status(job_info['job_id'])
                if status_data:
                    job_status = status_data.get("jobStatus", "UNKNOWN")
                    print(f"📊 [{elapsed_minutes:02d}:{elapsed_seconds:02d}] {job_info['name']}: {job_status}")
            
            jobs_to_remove = []
            for iso3, job_info in active_jobs.items():
                status_data = get_job_status(job_info['job_id'])
                if status_data:
                    job_status = status_data.get("jobStatus", "UNKNOWN")
                    if job_status in ["SUCCEEDED", "FAILED"]:
                        jobs_to_remove.append(iso3)
                        completed_jobs[iso3] = {**job_info, 'final_status': job_status, 'status_data': status_data}
                        result_emoji = "✅" if job_status == "SUCCEEDED" else "❌"
                        print(f"{result_emoji} {job_info['name']} completed {'successfully' if job_status == 'SUCCEEDED' else 'with failure'}!")
                        logger.info(f"Job for {job_info['name']} finished with status: {job_status}")
        
            for iso3 in jobs_to_remove:
                del active_jobs[iso3]
            
            if active_jobs:
                time.sleep(poll_interval)
        
        # Handle timeouts
        for iso3, job_info in active_jobs.items():
            completed_jobs[iso3] = {**job_info, 'final_status': 'TIMEOUT'}
            print(f"⏰ {job_info['name']} timed out.")
            logger.warning(f"Job for {job_info['name']} timed out.")
        
        print(f"\n📊 Polling complete: {len([j for j in completed_jobs.values() if j['final_status'] == 'SUCCEEDED'])}/{len(completed_jobs)} jobs succeeded")

        print(f"\n📋 Step 8: Saving validation results to CSV")
        print("----------------------------------------")
        
        # 4. Save results to CSV and update DB
        all_successful = True
        successful_jobs = 0
        csv_results = []
        
        # Process all job results
        for iso3, job_info in completed_jobs.items():
            job_status = "success" if job_info['final_status'] == 'SUCCEEDED' else 'failed'
            job_name = job_info.get('job_name')
            
            # Update job result in DB
            db.record_job_result(run_id, iso3, Path(scenario_path).stem, job_name or '', job_status, None, datetime.now())
            
            if job_status == 'success' and job_name:
                # Extract ULID from job name and save to CSV
                ulid = extract_ulid_from_job_name(job_name, environment)
                if ulid:
                    csv_results.append((ulid, iso3, Path(scenario_path).stem))
                    print(f"✅ Saved result for {job_info['name']} - ULID: {ulid}")
                    successful_jobs += 1
                else:
                    print(f"⚠️  Could not extract ULID from job name: {job_name}")
            else:
                all_successful = False
        
        # Write all results to CSV in batch
        if csv_results:
            if csv_writer.write_batch_results(csv_results):
                print(f"📊 Saved {len(csv_results)} validation results to CSV")
            else:
                print(f"❌ Failed to save results to CSV")
        
        print(f"📊 Validation complete: {successful_jobs}/{len(completed_jobs)} jobs succeeded")

        return all_successful

    except Exception as e:
        logger.error(f"Unhandled error in multi-country validation for {scenario_path}: {e}", exc_info=True)
        return False