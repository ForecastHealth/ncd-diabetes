"""
Remote API client for model validation testing.

This module handles communication with the forecast-health-api including
job submission, status polling, and health checks.
"""

import json
import time
import requests
from typing import Dict, Any, Optional

from .scenario_utils import load_json_file


# Configuration
API_BASE_URL = "https://microapi.forecasthealth.org"


def test_api_health() -> bool:
    """Test if the API is running and accessible."""
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ Remote API is accessible")
            return True
        else:
            print(f"❌ Remote API returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to remote API. Check your internet connection.")
        return False
    except requests.exceptions.Timeout:
        print("❌ Connection to remote API timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error checking API health: {e}")
        return False


def submit_simulation_job(config_path: str, environment: str) -> Optional[Dict[str, Any]]:
    """Submit a simulation job to the API."""
    url = f"{API_BASE_URL}/run/{environment}"
    
    config = load_json_file(config_path)
    
    print(f"🚀 Submitting job to: {url}")
    print(f"📋 Environment: {environment}")
    print(f"📊 Config size: {len(json.dumps(config))} characters")
    
    try:
        response = requests.post(
            url,
            json=config,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Job submitted successfully!")
            print(f"   Job ID: {result.get('jobId')}")
            print(f"   Job Name: {result.get('jobName')}")
            print(f"   Config S3 Path: {result.get('config_s3_path')}")
            return result
        else:
            print(f"❌ Job submission failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 60 seconds")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get the status of a submitted job."""
    url = f"{API_BASE_URL}/status/{job_id}"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Status check failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Status check timed out after 30 seconds")
        return None
    except Exception as e:
        print(f"❌ Unexpected error checking status: {e}")
        return None


def poll_job_completion(job_id: str, poll_interval: int = 3, max_wait_time: int = 3600) -> Optional[Dict[str, Any]]:
    """Poll job status until completion or timeout."""
    print(f"\n⏳ Polling job status (Job ID: {job_id})")
    print(f"   Poll interval: {poll_interval} seconds")
    print(f"   Max wait time: {max_wait_time} seconds")
    print("=" * 60)
    
    start_time = time.time()
    
    while True:
        elapsed_time = time.time() - start_time
        
        if elapsed_time > max_wait_time:
            print(f"\n⏰ Timeout: Job did not complete within {max_wait_time} seconds")
            return None
        
        status_data = get_job_status(job_id)
        
        if status_data is None:
            print(f"\n❌ Error checking job status")
            return None
        
        job_status = status_data.get("jobStatus", "UNKNOWN")
        elapsed_minutes = int(elapsed_time // 60)
        elapsed_seconds = int(elapsed_time % 60)
        
        print(f"📊 [{elapsed_minutes:02d}:{elapsed_seconds:02d}] Job Status: {job_status}")
        
        # Terminal states
        if job_status == "SUCCEEDED":
            print(f"\n🎉 Job completed successfully!")
            print(f"   Total time: {elapsed_minutes} minutes, {elapsed_seconds} seconds")
            print(f"   Job ID: {status_data.get('jobId')}")
            print(f"   Job Name: {status_data.get('jobName')}")
            if status_data.get('resultsPath'):
                print(f"   Results: {status_data['resultsPath']}")
            return status_data
        
        elif job_status == "FAILED":
            print(f"\n❌ Job failed!")
            print(f"   Total time: {elapsed_minutes} minutes, {elapsed_seconds} seconds")
            print(f"   Exit code: {status_data.get('exitCode', 'N/A')}")
            if status_data.get('statusReason'):
                print(f"   Reason: {status_data['statusReason']}")
            if status_data.get('logStreamName'):
                print(f"   Logs: {status_data['logStreamName']}")
            return status_data
        
        # Non-terminal states - continue polling
        elif job_status in ["SUBMITTED", "PENDING", "RUNNABLE", "STARTING", "RUNNING"]:
            # Show additional info for running jobs
            if job_status == "RUNNING" and status_data.get('startedAt'):
                started_at = status_data['startedAt']
                # Handle both seconds and milliseconds timestamps
                if started_at > 1e10:  # If timestamp is in milliseconds
                    started_at = started_at / 1000.0
                run_time = time.time() - started_at
                run_minutes = int(run_time // 60)
                run_seconds = int(run_time % 60)
                print(f"   Running for: {run_minutes} minutes, {run_seconds} seconds")
            
            print(f"   Waiting {poll_interval} seconds before next check...")
            time.sleep(poll_interval)
        
        else:
            print(f"\n⚠️  Unknown job status: {job_status}")
            print(f"   This may indicate a new status type or API change")
            return status_data


def submit_and_poll_job(config_path: str, environment: str, poll_interval: int = 3, max_wait_time: int = 3600) -> Optional[Dict[str, Any]]:
    """Submit job and poll for completion.
    
    Returns:
        Dict containing job information if successful, None if failed
    """
    # Submit job
    result = submit_simulation_job(config_path, environment)
    if result is None or "jobId" not in result:
        return None
    
    job_id = result['jobId']
    
    # Poll for completion
    final_status = poll_job_completion(job_id, poll_interval, max_wait_time)
    
    if final_status is None:
        print(f"\n⚠️  Polling stopped due to timeout or error")
        print(f"   Job may still be running - check manually with:")
        print(f"   curl {API_BASE_URL}/status/{job_id}")
        return None
    elif final_status.get('jobStatus') == 'FAILED':
        return None
    elif final_status.get('jobStatus') == 'SUCCEEDED':
        return final_status
    else:
        print(f"\n⚠️  Job ended with unexpected status: {final_status.get('jobStatus')}")
        return None