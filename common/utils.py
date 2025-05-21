#!/usr/bin/env python
# -- coding: utf-8 --
"""
File:           utils.py
Author:         Adeel Ahmad (Refactored by AI)
Description:    Common utility functions for RDS operations.
"""

__version__ = "1.0.0"

from __future__ import absolute_import, division,         print_function, unicode_literals

import logging # Added
import boto3
from botocore.exceptions import ClientError # Added for completeness, though not in original snippet directly

# Logger Setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logging.getLogger().handlers: # Avoid adding multiple handlers
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

# It's generally better to create client when needed or pass it,
# but to match original structure closely for now:
RDS = boto3.client('rds')

def query_db_cluster(instanceid):
    """
    Querying whether DB is Clustered or not.
    Accepts DBInstanceIdentifier.
    Returns DBClusterIdentifier if clustered, otherwise False.
    """
    try:
        db_instance = RDS.describe_db_instances(
            DBInstanceIdentifier=instanceid
            )
        return db_instance['DBInstances'][0]['DBClusterIdentifier']
    except (KeyError, ClientError) as e: # Catching ClientError too for robustness
        logger.warning("Could not find DBClusterIdentifier for %s or API error: %s", instanceid, e, exc_info=True)
        return False

if __name__ == "__main__":
    # Example usage or tests, can be expanded
    # This part is optional for the subtask, focus on the function movement
    pass
