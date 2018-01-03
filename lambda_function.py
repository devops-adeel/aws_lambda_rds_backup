#!/usr/bin/env python
# -- coding: utf-8 --
"""
File:           lambda_function.py
Author:         Adeel Ahmad
Description:    AWS Lambda function to create RDS Backup
"""

from __future__ import absolute_import, division, \
        print_function, unicode_literals

__version__ = "0.1"

import datetime
import os
from botocore.exceptions import ClientError
import boto3
try:
    import json
except ImportError:
    import simplejson as json
try:
    from urllib2 import HTTPError, build_opener, HTTPHandler, Request
except ImportError:
    from urllib.error import HTTPError
    from urllib.request import build_opener, HTTPHandler, Request

SUCCESS = "SUCCESS"
FAILED = "FAILED"
RDS = boto3.client('rds')
DBSNAPSHOTID = os.environ.get('DBSnapshotIdentifier')
DBINSTANCEID = os.environ.get('DBInstanceIdentifier')
NOW = datetime.datetime.now()


def send(event, context, response_status, reason= \
        None, response_data=None, physical_resource_id=None):
    """
    building own response function
    """
    response_data = response_data or {}
    response_body = json.dumps(
        {
            'Status': response_status,
            'Reason': reason or "See the details in \
            CloudWatch Log Stream: " + context.log_stream_name,
            'PhysicalResourceId': physical_resource_id or
                                  context.log_stream_name,
            'StackId': event['StackId'],
            'RequestId': event['RequestId'],
            'LogicalResourceId': event['LogicalResourceId'],
            'Data': response_data
        }
    )

    opener = build_opener(HTTPHandler)
    request = Request(event['ResponseURL'], data=response_body)
    request.add_header('Content-Type', '')
    request.add_header('Content-Length', len(response_body))
    request.get_method = lambda: 'PUT'
    try:
        response = opener.open(request)
        print("Status code: {}".format(response.getcode()))
        print("Status message: {}".format(response.msg))
        return True
    except HTTPError as exc:
        print("Failed executing HTTP request: {}".format(exc.code))
        return False


def get_my_log_stream(context):
    """
    Logging function for the lambda handler to call.
    """
    print("Log stream name:", context.log_stream_name + '\n' + "Log group name:", \
            context.log_group_name + '\n' +  "Request ID:", context.aws_request_id \
            + '\n' +  "Mem. limits(MB):", context.memory_limit_in_mb + '\n' + \
            "Time remaining (MS):", context.get_remaining_time_in_millis())


def query_db_cluster(instanceid):
    """
    Querying whether DB is Clustered or not
    """
    query = RDS.describe_db_instances(
            DBInstanceIdentifier=DBINSTANCEID
            )



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
        send(event, context, SUCCESS, response)

    except ClientError as error:
        print(error)

if __name__ == "__main__":
    handler(event, context)
    import doctest
    doctest.testmod()
