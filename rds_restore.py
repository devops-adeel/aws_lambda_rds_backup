#!/usr/bin/env python
# -- coding: utf-8 --
"""
File:           rds_restore.py
Author:         Adeel Ahmad
Description:    Python Script to restore from RDS Backup
"""

from __future__ import absolute_import, \
        division, print_function, unicode_literals

# __version__ has been moved to common/utils.py

import logging # Added
import os
import sys # Added
from botocore.exceptions import ClientError
import boto3

from common.utils import query_db_cluster

# Logger Setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logging.getLogger().handlers: # Avoid adding multiple handlers
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

RDS = boto3.client('rds')
# INSTANCEID is now retrieved in __main__ block

def main(instanceid):
    """
    Main function restore from latest snapshot.
    Requires DBINSTANCEID (passed as instanceid), and NEW_CLUSTER_ID or NEW_INSTANCEID.
    """
    if not instanceid: # Should be caught by __main__ but good for direct calls
        logger.error("DBINSTANCEID (passed as instanceid) is missing.")
        raise ValueError("DBINSTANCEID (passed as instanceid) is missing.")

    if query_db_cluster(instanceid):
        cluster_id = query_db_cluster(instanceid)
        new_cluster_id = os.environ.get('NEW_CLUSTER_ID')
        if not new_cluster_id:
            error_msg = "NEW_CLUSTER_ID environment variable is not set for clustered restore."
            logger.error(error_msg)
            raise ValueError(error_msg)
        try:
            logger.info("Attempting to restore cluster %s to new cluster %s", cluster_id, new_cluster_id)
            restore = RDS.restore_db_cluster_to_point_in_time(
                DBClusterIdentifier=new_cluster_id,
                SourceDBClusterIdentifier=cluster_id,
                UseLatestRestorableTime=True
                )
            logger.info("Successfully initiated restore for cluster %s to new cluster %s. Status: %s",
                        cluster_id, new_cluster_id, restore.get('DBCluster', {}).get('Status'))
            return restore.get('DBCluster', {}).get('Status')
        except ClientError as error:
            logger.error("Failed to restore cluster %s to %s: %s", cluster_id, new_cluster_id, error, exc_info=True)
            raise error # Re-raise after logging
    else:
        new_instanceid = os.environ.get('NEW_INSTANCEID')
        if not new_instanceid:
            error_msg = "NEW_INSTANCEID environment variable not set for non-clustered restore."
            logger.error(error_msg)
            raise ValueError(error_msg)
        try:
            logger.info("Attempting to restore instance %s to new instance %s", instanceid, new_instanceid)
            restore = RDS.restore_db_instance_to_point_in_time(
                SourceDBInstanceIdentifier=instanceid,
                TargetDBInstanceIdentifier=new_instanceid,
                UseLatestRestorableTime=True
                )
            logger.info("Successfully initiated restore for instance %s to new instance %s. Status: %s",
                        instanceid, new_instanceid, restore.get('DBInstance', {}).get('DBInstanceStatus'))
            return restore.get('DBInstance', {}).get('DBInstanceStatus')
        except ClientError as error:
            logger.error("Failed to restore instance %s to %s: %s", instanceid, new_instanceid, error, exc_info=True)
            raise error # Re-raise after logging


if __name__ == "__main__":
    INSTANCEID = os.environ.get('DBINSTANCEID')
    if not INSTANCEID:
        logger.error("DBINSTANCEID environment variable not set. Exiting.")
        sys.exit(1) # Exit if primary identifier is missing
    
    logger.info("Starting RDS restore process for instance: %s", INSTANCEID)
    try:
        status = main(INSTANCEID)
        logger.info("Restore process finished with status: %s", status)
    except ValueError as ve: # Catch specific ValueError for missing env vars in main
        logger.error("Configuration error: %s", ve)
        sys.exit(1)
    except ClientError:
        # Error is already logged in main() by the time it's re-raised.
        logger.error("RDS restore failed due to an AWS API ClientError. Check previous logs for details.")
        sys.exit(1)
    except Exception as e: # Catch any other unexpected errors
        logger.error("An unexpected error occurred during the restore process: %s", e, exc_info=True)
        sys.exit(1)

    # import doctest # doctest might not be as relevant with these changes
    # doctest.testmod()
