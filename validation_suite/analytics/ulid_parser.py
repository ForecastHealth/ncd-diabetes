"""
ULID parsing utilities for extracting identifiers from job names.

This module provides functionality to extract ULIDs from job names
following the pattern: botech-sim-{environment}-{ULID}
"""

import re
from typing import Optional


def extract_ulid_from_job_name(job_name: str, environment: str = None) -> Optional[str]:
    """
    Extract ULID from a job name.
    
    Expected format: botech-sim-{environment}-{ULID}
    Examples: 
        - botech-sim-standard-01JY6Z5TZPYS4PWF91B1WKDDX5
        - botech-sim-appendix_3-01JZS6RHM5YA77NM6N20ZAB706
        - botech-sim-default-01JY6Z5TZPYS4PWF91B1WKDDX5
    
    Args:
        job_name: The job name containing the ULID
        environment: The environment name (e.g., "standard", "appendix_3"). 
                    If None, will match any environment.
        
    Returns:
        str: The extracted ULID if found, None otherwise
    """
    if not job_name:
        return None
    
    # ULID pattern: 26 characters, Crockford's Base32 alphabet
    # Starts with timestamp (10 chars) + randomness (16 chars)
    if environment:
        # Match specific environment
        ulid_pattern = rf'botech-sim-{re.escape(environment)}-([0123456789ABCDEFGHJKMNPQRSTVWXYZ]{{26}})$'
    else:
        # Match any environment
        ulid_pattern = r'botech-sim-[^-]+-([0123456789ABCDEFGHJKMNPQRSTVWXYZ]{26})$'
    
    match = re.search(ulid_pattern, job_name)
    if match:
        return match.group(1)
    
    return None


def validate_ulid_format(ulid: str) -> bool:
    """
    Validate that a string matches ULID format.
    
    Args:
        ulid: String to validate as ULID
        
    Returns:
        bool: True if valid ULID format, False otherwise
    """
    if not ulid or len(ulid) != 26:
        return False
    
    # Crockford's Base32 alphabet (excludes I, L, O, U)
    valid_chars = set('0123456789ABCDEFGHJKMNPQRSTVWXYZ')
    return all(char in valid_chars for char in ulid.upper())


def parse_ulid_timestamp(ulid: str) -> Optional[int]:
    """
    Extract timestamp from ULID (first 10 characters).
    
    Args:
        ulid: Valid ULID string
        
    Returns:
        int: Unix timestamp in milliseconds, None if invalid
    """
    if not validate_ulid_format(ulid):
        return None
    
    # First 10 characters represent timestamp in Crockford's Base32
    timestamp_part = ulid[:10]
    
    try:
        # Convert from Crockford's Base32 to integer
        timestamp = 0
        base32_chars = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
        
        for char in timestamp_part:
            timestamp = timestamp * 32 + base32_chars.index(char.upper())
        
        return timestamp
    except (ValueError, IndexError):
        return None
