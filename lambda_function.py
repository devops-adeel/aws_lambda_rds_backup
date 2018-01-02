#!/usr/bin/env python
# -- coding: utf-8 --
"""
File:           lambda_function.py
Author:         Adeel Ahmad
Description:    AWS Lambda function to create RDS Backup
"""

from __future__ import absolute_import, division, print_function, unicode_literals

__version__ = "0.1"

import unittest
import datetime
import os
import cfnresponse
import boto3

RDS = boto3.client('rds')
DBSNAPSHOTID = os.environ.get('DBSnapshotIdentifier')
DBINSTANCEID = os.environ.get('DBInstanceIdentifier')
NOW = datetime.datetime.now()

def handler(event, context):
    """
    Handler to create RDS Backups
    """
    response = {}

    try:
        response = RDS.create_db_snapshot(
            DBSnapshotIdentifier=str(DBSNAPSHOTID) + NOW.strftime("%Y-%m-%d"),
            DBInstanceIdentifier=DBINSTANCEID
            )
        response['DBSnapshot'].pop('SnapshotCreateTime')
        response['DBSnapshot'].pop('InstanceCreateTime')
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response)

    except Exception as error:
        print(error)

if __name__ == "__main__":
    handler(event, context)
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
            self.assertEqual(handler(event, context),)
