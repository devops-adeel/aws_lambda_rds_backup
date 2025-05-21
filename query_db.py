#!/usr/bin/env python
# -- coding: utf-8 --
"""
File:           query_db.py
Author:         Adeel Ahmad
Description:    Python script to query RDS instance details, like cluster membership.
"""

from __future__ import absolute_import, \
        division, print_function, unicode_literals

# __version__ has been moved to common/utils.py

import logging # Added
import os
import sys # Added
import boto3

from common.utils import query_db_cluster

# Logger Setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logging.getLogger().handlers: # Avoid adding multiple handlers
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

RDS = boto3.client('rds') # This RDS client is not used in this file anymore.
# INSTANCEID is now retrieved in __main__ block


if __name__ == "__main__":
    INSTANCEID = os.environ.get('DBINSTANCEID')
    if not INSTANCEID:
        logger.error("DBINSTANCEID environment variable not set. Exiting.")
        sys.exit(1) # Exit if environment variable is missing
    
    logger.info("Querying DB instance: %s for cluster information.", INSTANCEID)
    try:
        cluster_id = query_db_cluster(INSTANCEID) # query_db_cluster now uses its own RDS client
        if cluster_id:
            logger.info("DB Instance %s is part of cluster: %s", INSTANCEID, cluster_id)
        else:
            # The warning in common/utils.py would have already logged the specific error if one occurred there.
            # This info log is for the case where it's genuinely not in a cluster.
            logger.info("DB Instance %s is not part of a DB Cluster, or an error occurred during the query (check previous logs).", INSTANCEID)
    except Exception as e: # Catch any unexpected errors from query_db_cluster or other issues
        logger.error("An unexpected error occurred while querying instance %s: %s", INSTANCEID, e, exc_info=True)
        sys.exit(1) # Exit with error status

    # import doctest # doctest might not be relevant anymore
    # doctest.testmod()
