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
import boto3

RDS = boto3.client('rds')

def retrieve_latest_snapshot():
    """
    Function to retrieve latest snapshot
    """
    response = {}

    try:
        snapshots = RDS.describe_db_snapshots(
            DBInstanceIdentifier=DBINSTANCEID,
            SnapshotType='manual',
            )
        max(snapshots['DBSnapshots'].itervalues('SnapshotCreateTime'),
            key=lambda latest: latest if isinstance(latest, datetime) else datetime.min)

    except Exception as error:
        print(error)

if __name__ == "__main__":
    main()
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
            self.assertEqual(main())
