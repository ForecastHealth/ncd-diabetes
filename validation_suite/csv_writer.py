"""
CSV Writer for Validation Results

This module provides a simple CSV writer to record validation results
with ULID, timestamp, country, and scenario information.
"""
import csv
import os
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ValidationCSVWriter:
    def __init__(self, csv_path: str = "validation_results.csv"):
        self.csv_path = csv_path
        self._ensure_csv_exists()
    
    def _ensure_csv_exists(self):
        """Create the CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ulid', 'timestamp', 'country', 'scenario'])
            logger.info(f"Created new CSV file: {self.csv_path}")
    
    def write_validation_result(self, ulid: str, country: str, scenario: str) -> bool:
        """
        Write a validation result to the CSV file.
        
        Args:
            ulid: The ULID from the validation job
            country: ISO3 country code
            scenario: Scenario name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            timestamp = datetime.now().isoformat()
            
            with open(self.csv_path, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([ulid, timestamp, country, scenario])
            
            logger.info(f"Saved result to CSV: ULID={ulid}, Country={country}, Scenario={scenario}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write to CSV: {e}")
            return False
    
    def write_batch_results(self, results: list) -> bool:
        """
        Write multiple validation results to the CSV file.
        
        Args:
            results: List of tuples (ulid, country, scenario)
            
        Returns:
            True if all successful, False otherwise
        """
        try:
            timestamp = datetime.now().isoformat()
            
            with open(self.csv_path, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for ulid, country, scenario in results:
                    writer.writerow([ulid, timestamp, country, scenario])
            
            logger.info(f"Saved {len(results)} results to CSV")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write batch to CSV: {e}")
            return False