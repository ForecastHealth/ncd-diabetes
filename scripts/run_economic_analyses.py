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
import threading
import json
from typing import List, Optional, Tuple
from dotenv import load_dotenv
import os

# Check if sseclient is available, provide helpful error if it's not
try:
    import sseclient
except ImportError:
    print("Error: sseclient-py package is required for SSE monitoring.")
    print("Please install it using: pip install sseclient-py")
    sys.exit(1)

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

def monitor_sse_status(api_base_url: str, model_id: str, analysis_id: str):
    """
    Connects to the SSE status endpoint for an analysis and prints updates.
    Intended to be run in a separate thread.
    """
    sse_url = f"{api_base_url}/v1/models/{model_id}/economic-analyses/{analysis_id}/status"
    print(f"[SSE Monitor - {analysis_id}] Connecting to {sse_url}")
    
    headers = {'Accept': 'text/event-stream'}
    try:
        # Use requests with stream=True to get the response object
        response = requests.get(sse_url, stream=True, headers=headers, timeout=30)
        response.raise_for_status()  # Check for initial connection errors (like 404)

        client = sseclient.SSEClient(response)
        
        print(f"[SSE Monitor - {analysis_id}] Connection established. Waiting for events...")
        
        for event in client.events():
            # Heartbeats might be comments (event.event is None or 'message', event.data is empty)
            if not event.data:
                continue  # Skip empty events/comments often used as keep-alives

            event_type = event.event if event.event else "message"  # Default to 'message' if no event type specified

            # Try parsing data as JSON, default to raw string if fails
            try:
                data_payload = json.loads(event.data)
            except json.JSONDecodeError:
                data_payload = event.data  # Use as string if not JSON

            print(f"[SSE - {analysis_id}] Type: {event_type}, Data: {data_payload}")

            # Check for termination events to exit the thread cleanly
            if event_type == 'statusUpdate':
                status = data_payload.get('status')
                if status in ['COMPLETED_ANALYSIS', 'ERROR']:
                    print(f"[SSE Monitor - {analysis_id}] Received final status: {status}. Closing SSE connection.")
                    break  # Exit the loop

    except requests.exceptions.RequestException as e:
        print(f"[SSE Monitor - {analysis_id}] Error connecting or streaming: {e}")
    except Exception as e:
        print(f"[SSE Monitor - {analysis_id}] Unexpected error during SSE monitoring: {e}")
    finally:
        # Ensure the response is closed if the loop finishes or an error occurs
        if 'response' in locals() and response:
            response.close()
        print(f"[SSE Monitor - {analysis_id}] Monitoring thread finished.")


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
        print(f"\n--------------------------------------------------")
        print(f"Processing Analysis {idx}/{len(analysis_ids)}: {analysis_id}")
        print(f"--------------------------------------------------")

        # Start SSE Monitor Thread
        print(f"[Main - {analysis_id}] Starting SSE monitor thread...")
        sse_thread = threading.Thread(
            target=monitor_sse_status,
            args=(api_base_url, model_id, analysis_id),
            daemon=True  # Set as daemon so it exits if the main program exits
        )
        sse_thread.start()
        
        # Give the SSE connection a moment to establish
        time.sleep(0.5)
        
        # Run the economic analysis (blocking call)
        print(f"[Main - {analysis_id}] Initiating POST request to run analysis...")
        start_time = time.time()
        response = run_economic_analysis(api_base_url, model_id, analysis_id)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Report POST Completion
        status = response.get("status", "unknown")
        message = response.get("message", "")
        
        # If successful response has nested data, extract it
        if status == "success" and "data" in response and "results" in response["data"]:
            post_result_summary = response["data"]["results"].get("resultData", {}).get("notes", "No notes")
            print(f"[POST - {analysis_id}] Request completed. Status: {status}, Duration: {duration:.2f}s. Summary: {post_result_summary}")
        else:
            print(f"[POST - {analysis_id}] Request completed. Status: {status}, Duration: {duration:.2f}s. Message: {message}")
        
        results.append({
            "analysis_id": analysis_id,
            "status": status,
            "duration": duration,
            "response": response
        })
        
        # Optional: Wait briefly for the SSE thread to potentially print final messages
        # The thread should exit on its own based on 'COMPLETED_ANALYSIS' or 'ERROR' events
        time.sleep(1)
    
    # Print summary
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\nSummary: {success_count}/{len(analysis_ids)} analyses completed successfully")

if __name__ == "__main__":
    main()
