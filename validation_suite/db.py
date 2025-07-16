"""
Multi-Country Multi-Scenario Database System

This module provides SQLite database management for tracking validation runs,
job results, and analytics metrics across multiple countries and scenarios.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import contextlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationDatabase:
    """
    SQLite database manager for validation results and analytics.
    
    Handles schema creation, data operations, and querying for the
    multi-country multi-scenario validation system.
    """
    
    def __init__(self, db_path: str = "results.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.setup_schema()
    
    @contextlib.contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def setup_schema(self) -> None:
        """
        Create database schema with tables and indexes.
        
        Creates tables for validation runs, job results, and metrics
        with appropriate foreign key relationships and indexes.
        """
        schema_sql = """
        -- Track batch executions
        CREATE TABLE IF NOT EXISTS validation_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            git_commit TEXT NOT NULL,
            status TEXT NOT NULL,  -- 'running', 'completed', 'failed'
            total_jobs INTEGER,
            successful_jobs INTEGER,
            failed_jobs INTEGER
        );

        -- Store individual job results
        CREATE TABLE IF NOT EXISTS job_results (
            run_id INTEGER,
            country TEXT NOT NULL,
            scenario TEXT NOT NULL,
            ulid TEXT NOT NULL,
            job_status TEXT NOT NULL,  -- 'success', 'failed', 'timeout'
            submitted_at DATETIME,
            completed_at DATETIME,
            FOREIGN KEY (run_id) REFERENCES validation_runs(run_id),
            PRIMARY KEY (run_id, country, scenario)
        );

        -- Store the actual analytics metrics
        CREATE TABLE IF NOT EXISTS metrics (
            run_id INTEGER,
            country TEXT NOT NULL,
            scenario TEXT NOT NULL,
            ulid TEXT NOT NULL,
            element_label TEXT NOT NULL,
            timestamp_year INTEGER NOT NULL,
            value REAL NOT NULL,
            FOREIGN KEY (run_id) REFERENCES validation_runs(run_id),
            PRIMARY KEY (run_id, country, scenario, element_label, timestamp_year)
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_metrics_country_scenario ON metrics(country, scenario);
        CREATE INDEX IF NOT EXISTS idx_metrics_element ON metrics(element_label);
        CREATE INDEX IF NOT EXISTS idx_metrics_year ON metrics(timestamp_year);
        CREATE INDEX IF NOT EXISTS idx_job_results_status ON job_results(job_status);
        CREATE INDEX IF NOT EXISTS idx_validation_runs_commit ON validation_runs(git_commit);
        CREATE INDEX IF NOT EXISTS idx_validation_runs_timestamp ON validation_runs(timestamp);
        """
        
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()
        
        logger.info(f"Database schema initialized: {self.db_path}")
    
    def start_validation_run(self, git_commit: str, total_jobs: int) -> int:
        """
        Start a new validation run.
        
        Args:
            git_commit: Current git commit hash
            total_jobs: Total number of jobs to be submitted
            
        Returns:
            int: New run_id
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO validation_runs (git_commit, status, total_jobs, successful_jobs, failed_jobs)
                VALUES (?, 'running', ?, 0, 0)
                """,
                (git_commit, total_jobs)
            )
            conn.commit()
            run_id = cursor.lastrowid
        
        logger.info(f"Started validation run {run_id} with {total_jobs} jobs (commit: {git_commit[:8]})")
        return run_id
    
    def update_run_status(self, run_id: int, status: str, successful_jobs: int, failed_jobs: int) -> None:
        """
        Update validation run status and job counts.
        
        Args:
            run_id: Run identifier
            status: New status ('running', 'completed', 'failed')
            successful_jobs: Number of successful jobs
            failed_jobs: Number of failed jobs
        """
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE validation_runs 
                SET status = ?, successful_jobs = ?, failed_jobs = ?
                WHERE run_id = ?
                """,
                (status, successful_jobs, failed_jobs, run_id)
            )
            conn.commit()
        
        logger.info(f"Updated run {run_id}: {status} ({successful_jobs} success, {failed_jobs} failed)")
    
    def record_job_result(
        self, 
        run_id: int, 
        country: str, 
        scenario: str, 
        ulid: str, 
        job_status: str,
        submitted_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ) -> None:
        """
        Record individual job result.
        
        Args:
            run_id: Run identifier
            country: Country ISO3 code
            scenario: Scenario name
            ulid: Job ULID
            job_status: Job status ('success', 'failed', 'timeout')
            submitted_at: Job submission time
            completed_at: Job completion time
        """
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO job_results 
                (run_id, country, scenario, ulid, job_status, submitted_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, country, scenario, ulid, job_status, submitted_at, completed_at)
            )
            conn.commit()
        
        logger.debug(f"Recorded job result: {country}/{scenario} -> {job_status}")
    
    def store_metrics(self, run_id: int, country: str, scenario: str, ulid: str, metrics_data: List[Dict]) -> None:
        """
        Store analytics metrics for a job.
        
        Args:
            run_id: Run identifier
            country: Country ISO3 code
            scenario: Scenario name
            ulid: Job ULID
            metrics_data: List of metric dictionaries with keys:
                         'element_label', 'timestamp_year', 'value'
        """
        if not metrics_data:
            logger.warning(f"No metrics data provided for {country}/{scenario}")
            return
        
        # Prepare batch insert data
        insert_data = []
        for metric in metrics_data:
            insert_data.append((
                run_id,
                country,
                scenario,
                ulid,
                metric['element_label'],
                int(metric['timestamp_year']),
                float(metric['value'])
            ))
        
        with self.get_connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO metrics 
                (run_id, country, scenario, ulid, element_label, timestamp_year, value)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                insert_data
            )
            conn.commit()
        
        logger.info(f"Stored {len(metrics_data)} metrics for {country}/{scenario}")
    
    def parse_csv_to_metrics(self, csv_content: str) -> List[Dict]:
        """
        Parse CSV analytics data into normalized metrics format.
        
        Args:
            csv_content: CSV content string
            
        Returns:
            List of metric dictionaries
        """
        metrics = []
        lines = csv_content.strip().split('\n')
        
        # Skip header if present
        if lines and lines[0].startswith('element_label'):
            lines = lines[1:]
        
        for line in lines:
            if not line.strip():
                continue
                
            try:
                parts = line.split(',')
                if len(parts) >= 3:
                    metrics.append({
                        'element_label': parts[0].strip(),
                        'timestamp_year': int(parts[1].strip()),
                        'value': float(parts[2].strip())
                    })
            except (ValueError, IndexError) as e:
                logger.warning(f"Skipping invalid CSV line: {line} ({e})")
                continue
        
        return metrics
    
    def get_failed_jobs(self, run_id: int) -> List[Tuple[str, str]]:
        """
        Get list of failed jobs for a run.
        
        Args:
            run_id: Run identifier
            
        Returns:
            List of (country, scenario) tuples
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT country, scenario 
                FROM job_results 
                WHERE run_id = ? AND job_status != 'success'
                ORDER BY country, scenario
                """,
                (run_id,)
            )
            return cursor.fetchall()
    
    def needs_rerun(self, country: str, scenario: str, current_git_commit: str) -> bool:
        """
        Check if a country/scenario combination needs to be rerun.
        
        Args:
            country: Country ISO3 code
            scenario: Scenario name
            current_git_commit: Current git commit hash
            
        Returns:
            bool: True if rerun is needed
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT jr.job_status, vr.git_commit
                FROM job_results jr
                JOIN validation_runs vr ON jr.run_id = vr.run_id
                WHERE jr.country = ? AND jr.scenario = ?
                ORDER BY vr.timestamp DESC
                LIMIT 1
                """,
                (country, scenario)
            )
            result = cursor.fetchone()
        
        if not result:
            return True  # Never run before
        
        job_status, git_commit = result
        
        # Rerun if job failed or git commit changed
        return job_status != 'success' or git_commit != current_git_commit
    
    def get_latest_run_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get summary of the latest validation run.
        
        Returns:
            Dictionary with run summary or None if no runs
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM validation_runs 
                ORDER BY timestamp DESC 
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return dict(row)
    
    def get_run_jobs(self, run_id: int) -> List[Dict[str, Any]]:
        """
        Get all jobs for a specific run.
        
        Args:
            run_id: Run identifier
            
        Returns:
            List of job dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM job_results 
                WHERE run_id = ? 
                ORDER BY country, scenario
                """,
                (run_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_metrics_for_run(self, run_id: int, country: str = None, scenario: str = None) -> List[Dict[str, Any]]:
        """
        Get metrics for a specific run, optionally filtered by country/scenario.
        
        Args:
            run_id: Run identifier
            country: Optional country filter
            scenario: Optional scenario filter
            
        Returns:
            List of metric dictionaries
        """
        query = "SELECT * FROM metrics WHERE run_id = ?"
        params = [run_id]
        
        if country:
            query += " AND country = ?"
            params.append(country)
        
        if scenario:
            query += " AND scenario = ?"
            params.append(scenario)
        
        query += " ORDER BY country, scenario, element_label, timestamp_year"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def export_run_csv(self, run_id: int, output_path: str) -> bool:
        """
        Export run metrics to CSV file.
        
        Args:
            run_id: Run identifier
            output_path: Output CSV file path
            
        Returns:
            bool: True if successful
        """
        try:
            metrics = self.get_metrics_for_run(run_id)
            
            if not metrics:
                logger.warning(f"No metrics found for run {run_id}")
                return False
            
            with open(output_path, 'w') as f:
                f.write("country,scenario,element_label,timestamp_year,value\n")
                for metric in metrics:
                    f.write(f"{metric['country']},{metric['scenario']},{metric['element_label']},{metric['timestamp_year']},{metric['value']}\n")
            
            logger.info(f"Exported {len(metrics)} metrics to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return False
    
    def cleanup_old_runs(self, keep_runs: int = 10) -> int:
        """
        Clean up old validation runs, keeping only the most recent.
        
        Args:
            keep_runs: Number of recent runs to keep
            
        Returns:
            int: Number of runs deleted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get run IDs to delete
            cursor.execute(
                """
                SELECT run_id FROM validation_runs 
                ORDER BY timestamp DESC 
                LIMIT -1 OFFSET ?
                """,
                (keep_runs,)
            )
            old_run_ids = [row[0] for row in cursor.fetchall()]
            
            if not old_run_ids:
                return 0
            
            # Delete metrics first (foreign key constraint)
            cursor.execute(
                f"DELETE FROM metrics WHERE run_id IN ({','.join(['?'] * len(old_run_ids))})",
                old_run_ids
            )
            
            # Delete job results
            cursor.execute(
                f"DELETE FROM job_results WHERE run_id IN ({','.join(['?'] * len(old_run_ids))})",
                old_run_ids
            )
            
            # Delete validation runs
            cursor.execute(
                f"DELETE FROM validation_runs WHERE run_id IN ({','.join(['?'] * len(old_run_ids))})",
                old_run_ids
            )
            
            conn.commit()
            
            logger.info(f"Cleaned up {len(old_run_ids)} old validation runs")
            return len(old_run_ids)