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
import cfnresponse
import boto3

RDS = boto3.client('rds')

def handler(event, context):
    """
    Handler to create RDS Backups
    """
    response = {}

    # There is nothing to do for a delete request
    if event['RequestType'] == 'Delete':
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response)
        return

    try:
        response = RDS.create_db_snapshot(
            DBSnapshotIdentifier=event['ResourceProperties']['DBSnapshotIdentifier'],
            DBInstanceIdentifier=event['ResourceProperties']['DBInstanceIdentifier']
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

