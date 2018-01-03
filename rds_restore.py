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
from botocore.exceptions import ClientError
import boto3

RDS = boto3.client('rds')
INSTANCEID = os.environ.get('DBINSTANCEID')


def retrieve_latest_snapshot(instanceid):
    """
    Function to retrieve latest snapshot
    """
    try:
        snapshots = RDS.describe_db_snapshots(
            DBInstanceIdentifier=instanceid
            )
        newest = sorted(snapshots['DBSnapshots'],
                        key=lambda latest: latest['SnapshotCreateTime'],
                        reverse=True)[0]['DBSnapshotIdentifier']
        return newest

    except ClientError as error:
        print(error)


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
        # print("Not part of a DB Cluster")
        return False


def main(instanceid):
    """
    Main function restore from latest snapshot.
    """
    try:
        snapshot_id = retrieve_latest_snapshot(instanceid)

        restore = RDS.restore_db_instance_from_db_snapshot(
            DBInstanceIdentifier=instanceid,
            DBSnapshotIdentifier=snapshot_id
            )
        # return restore['DBInstance']['StatusInfos']['Status']
        print(restore['DBInstance']['StatusInfos']['Status'])
    except ClientError as error:
        print(error)


if __name__ == "__main__":
    main(INSTANCEID)
    import doctest
    doctest.testmod()
