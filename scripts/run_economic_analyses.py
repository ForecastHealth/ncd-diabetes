#!/usr/bin/env python3
"""
Script to run economic analyses for the NCD Asthma model.
This script reads the project.csv file to get the model ID and analysis IDs,
then runs the economic analyses using the API endpoint.

Usage:
    run_economic_analyses.py [-n NUM_ANALYSES]
    
Options:
    -n NUM_ANALYSES    Run only the first N analyses
"""

import csv
import requests
import sys
import time
import argparse
from typing import List, Optional, Tuple
from dotenv import load_dotenv
import os

def load_environment_variables() -> Tuple[str, str, str]:
    """
    Load environment variables from .env.local file.
    Returns a tuple of (api_base_url, admin_token, superuser_id)
    """
    # Load environment variables from .env.local into os.environ
    load_dotenv(".env.local")
    
    # Extract required variables from os.environ
    api_base_url = os.environ.get('API_BASE_URL')
    if not api_base_url:
        print("Error: API_BASE_URL not found in .env.local")
        sys.exit(1)
    
    admin_token = os.environ.get('ADMIN_TOKEN')
    if not admin_token:
        print("Warning: ADMIN_TOKEN not found in .env.local, using default")
        admin_token = "supersecret"
    else:
        print("Using ADMIN_TOKEN from .env.local")
    
    superuser_id = os.environ.get('SUPERUSER_ID')
    if not superuser_id:
        print("Warning: SUPERUSER_ID not found in .env.local, defaulting to user ID 1")
        superuser_id = "1"
    else:
        print(f"Using SUPERUSER_ID: {superuser_id}")
    
    return api_base_url, admin_token, superuser_id

def read_project_csv(filepath: str) -> Tuple[Optional[str], List[str]]:
    """
    Read project.csv to extract the model ID and analysis IDs.
    
    Args:
        filepath: Path to the project.csv file
        
    Returns:
        Tuple containing model ID and list of analysis IDs
    """
    model_id = None
    analysis_ids = []
    
    with open(filepath, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['type'] == 'MODEL':
                model_id = row['id']
            elif row['type'] == 'ANALYSIS':
                analysis_ids.append(row['id'])
    
    return model_id, analysis_ids

def run_economic_analysis(api_base_url:str, model_id: str, analysis_id: str, timeout: int = 180, max_retries: int = 3) -> dict:
    """
    Run an economic analysis using the API endpoint.
    
    Args:
        model_id: ID of the model
        analysis_id: ID of the economic analysis to run
        timeout: Request timeout in seconds (default: 180)
        max_retries: Maximum number of retry attempts for timeouts (default: 3)
        
    Returns:
        API response as a dictionary
    """
    url = f"{api_base_url}/v1/models/{model_id}/economic-analyses/{analysis_id}/run"
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                retry_delay = 2 ** attempt  # Exponential backoff
                print(f"Timeout occurred. Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print(f"Error running analysis {analysis_id}: Request timed out after {max_retries} attempts")
                return {"status": "error", "message": f"Request timed out after {max_retries} attempts"}
        except requests.exceptions.RequestException as e:
            print(f"Error running analysis {analysis_id}: {e}")
            return {"status": "error", "message": str(e)}

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run economic analyses for the NCD Asthma model")
    parser.add_argument('-n', type=int, help="Run only the first N analyses", dest="num_analyses")
    return parser.parse_args()

def main():
    """Main function to run all economic analyses."""
    args = parse_arguments()
    project_file = "project.csv"

    api_base_url, _, _ = load_environment_variables()
    
    print(f"Reading project file: {project_file}")
    model_id, analysis_ids = read_project_csv(project_file)
    
    if not model_id:
        print("Error: Model ID not found in project.csv")
        sys.exit(1)
    
    if not analysis_ids:
        print("Error: No analysis IDs found in project.csv")
        sys.exit(1)
    
    print(f"Found model ID: {model_id}")
    print(f"Found {len(analysis_ids)} analyses available")
    
    # Limit the number of analyses if -n argument was provided
    if args.num_analyses and args.num_analyses > 0:
        if args.num_analyses < len(analysis_ids):
            analysis_ids = analysis_ids[:args.num_analyses]
            print(f"Running first {args.num_analyses} analyses")
        else:
            print(f"Requested {args.num_analyses} analyses, but only {len(analysis_ids)} are available")
    
    print(f"Will run {len(analysis_ids)} analyses")
    results = []
    
    for idx, analysis_id in enumerate(analysis_ids, 1):
        print(f"Running analysis {idx}/{len(analysis_ids)}: {analysis_id}")
        
        start_time = time.time()
        response = run_economic_analysis(api_base_url, model_id, analysis_id)
        end_time = time.time()
        
        duration = end_time - start_time
        
        status = response.get("status", "unknown")
        print(f"Analysis completed with status: {status} in {duration:.2f} seconds")
        
        results.append({
            "analysis_id": analysis_id,
            "status": status,
            "duration": duration,
            "response": response
        })
    
    # Print summary
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\nSummary: {success_count}/{len(analysis_ids)} analyses completed successfully")

if __name__ == "__main__":
    main()
