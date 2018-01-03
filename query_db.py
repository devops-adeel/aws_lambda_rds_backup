#!/usr/bin/env python
# -- coding: utf-8 --
"""
File:           rds_restore.py
Author:         Adeel Ahmad
Description:    Python Script to restore from RDS Backup
"""

from __future__ import absolute_import, \
        division, print_function, unicode_literals

__version__ = "0.1"

import os
import boto3

RDS = boto3.client('rds')
INSTANCEID = os.environ.get('DBINSTANCEID')


def query_db_cluster(instanceid):
    """
    Querying whether DB is Clustered or not
    """
    try:
        db_instance = RDS.describe_db_instances(
            DBInstanceIdentifier=instanceid
            )
        return db_instance['DBInstances'][0]['DBClusterIdentifier']

    except KeyError:
        print("Not part of a DB Cluster")


if __name__ == "__main__":
    query_db_cluster(INSTANCEID)
    import doctest
    doctest.testmod()
