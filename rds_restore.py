#!/usr/bin/env python
# -- coding: utf-8 --
"""
File:           rds_restore.py
Author:         Adeel Ahmad
Description:    Python Script to restore from RDS Backup
"""

from __future__ import absolute_import, division, print_function, unicode_literals

__version__ = "0.1"

import unittest
from datetime import datetime
from botocore.exceptions import ClientError
import boto3

RDS = boto3.client('rds')
DBINSTANCEID = 'pass'

def retrieve_latest_snapshot(instanceid):
    """
    Function to retrieve latest snapshot
    """

    try:
        snapshots = RDS.describe_db_snapshots(
            DBInstanceIdentifier=instanceid
            )
        newest = max(snapshots['DBSnapshots'].itervalues('SnapshotCreateTime'),
                     key=lambda latest: latest if isinstance(latest, datetime) else datetime.min)

        return newest

    except ClientError as error:
        print(error)

def main(instanceid):
    """
    Main function restore from latest snapshot.
    """
    try:
        newest = retrieve_latest_snapshot(instanceid)

        restore = RDS.restore_db_instance_from_db_snapshot(
            DBInstanceIdentifier=instanceid,
            DBSnapshotIdentifier=newest
            )
        return restore['DBInstance']['StatusInfos']['Status']
    except ClientError as error:
        print(error)

if __name__ == "__main__":
    main(instanceid)
    import doctest
    doctest.testmod()
    class MyTest(unittest.TestCase):
        """
        Class to initiate to test function
        """
        def test(self):
            """
            Test Function
            """
            self.assertEqual(main(instancid))
