"""
Analytics Database Processor
"""
import logging
from typing import Dict, Any, List, Optional

from ..db import ValidationDatabase
from .api_client import fetch_analytics_with_defaults
from .ulid_parser import extract_ulid_from_job_name, validate_ulid_format

logger = logging.getLogger(__name__)

class DatabaseAnalyticsProcessor:
    def __init__(self, db_path: str = "results.db"):
        self.db = ValidationDatabase(db_path)

    def fetch_analytics_for_ulid(self, ulid: str, environment: str = "standard") -> Optional[List[Dict]]:
        try:
            return fetch_analytics_with_defaults(environment=environment, ulid=ulid)
        except Exception as e:
            logger.error(f"Failed to fetch analytics for ULID {ulid}: {e}")
            return None

    def process_job_with_database(self, job_name: str, run_id: int, country: str, scenario: str, model_name: str, environment: str, **kwargs) -> Dict[str, Any]:
        result = {"success": False, "ulid": None, "data_records": 0, "error": None}
        
        try:
            ulid = extract_ulid_from_job_name(job_name, environment)
            if not ulid or not validate_ulid_format(ulid):
                result["error"] = f"Invalid ULID extracted from job name: {job_name}"
                return result
            result["ulid"] = ulid
            
            analytics_data = self.fetch_analytics_for_ulid(ulid, environment)
            if analytics_data is None:
                result["error"] = "Failed to fetch analytics data"
                return result
            
            result["data_records"] = len(analytics_data)
            
            self.db.store_metrics(run_id, country, scenario, ulid, analytics_data)
            logger.info(f"Stored {len(analytics_data)} metrics in DB for {country}/{scenario}")
            
            result["success"] = True
            return result
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Processing error for {job_name}: {e}", exc_info=True)
            return result