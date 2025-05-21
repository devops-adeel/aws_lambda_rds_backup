#!/usr/bin/env python
# -- coding: utf-8 --
"""
File:           lambda_function.py
Author:         Adeel Ahmad
Description:    AWS Lambda function to create RDS Backup
"""

from __future__ import absolute_import, division, \
        print_function, unicode_literals

# __version__ has been moved to common/utils.py

import datetime
import logging # Added
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

from common.utils import query_db_cluster

# Lambda specific logging setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

SUCCESS = "SUCCESS"
FAILED = "FAILED"
RDS = boto3.client('rds')
DBSNAPSHOTID = os.environ.get('DBSnapshotIdentifier') # Expected to be a prefix for the snapshot identifier
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
    request.add_header('Content-Type', 'application/json; charset=utf-8') # Changed Content-Type
    request.add_header('Content-Length', len(response_body))
    request.get_method = lambda: 'PUT'
    try:
        response = opener.open(request)
        logger.info("Status code: %s", response.getcode())
        logger.info("Status message: %s", response.msg)
        return True
    except HTTPError as exc:
        logger.error("Failed executing HTTP request to %s: %s", request.full_url, exc.code, exc_info=True)
        return False


def handler(event, context):
    """
    Handler to create RDS Backups
    """
    logger.info("Received event: %s", json.dumps(event, indent=2))
    logger.info("Log stream name: %s", context.log_stream_name)
    logger.info("Log group name: %s", context.log_group_name)
    logger.info("Request ID: %s", context.aws_request_id)
    logger.info("Mem. limits(MB): %s", context.memory_limit_in_mb)
    logger.info("Time remaining (MS): %s", context.get_remaining_time_in_millis())

    # Environment variable validation
    # These are already read globally, but we check them here in the handler's context
    if not DBINSTANCEID or not DBSNAPSHOTID:
        error_msg = "Missing required environment variable(s): DBInstanceIdentifier and/or DBSnapshotIdentifier must be set."
        logger.error(error_msg)
        # Attempt to get PhysicalResourceId for the send function, default if not found
        physical_resource_id = event.get('PhysicalResourceId', context.log_stream_name)
        send(event, context, FAILED, reason=error_msg, physical_resource_id=physical_resource_id)
        return
    
    response = {}
    if query_db_cluster(DBINSTANCEID):
        cluster_id = query_db_cluster(DBINSTANCEID) # Re-querying, but ensures it's fresh if global was stale. Could optimize.
        try:
            logger.info("Attempting to create cluster snapshot for %s", cluster_id)
            # DBSNAPSHOTID (from env var) is used as a prefix for the snapshot identifier.
            snapshot_identifier = str(DBSNAPSHOTID) + NOW.strftime("%Y-%m-%d")
            response = RDS.create_db_cluster_snapshot(
                DBClusterSnapshotIdentifier=snapshot_identifier,
                DBClusterIdentifier=cluster_id
                )
            logger.info("Successfully created cluster snapshot: %s", response.get('DBClusterSnapshot', {}).get('DBClusterSnapshotIdentifier'))
            send(event, context, SUCCESS, reason="Cluster snapshot created successfully.", response_data=response)
        except ClientError as error:
            logger.error("Failed to create cluster snapshot for %s: %s", cluster_id, error, exc_info=True)
            send(event, context, FAILED, reason=str(error), response_data={})
    else:
        try:
            logger.info("Attempting to create instance snapshot for %s", DBINSTANCEID)
            # DBSNAPSHOTID (from env var) is used as a prefix for the snapshot identifier.
            snapshot_identifier = str(DBSNAPSHOTID) + NOW.strftime("%Y-%m-%d")
            response = RDS.create_db_snapshot(
                DBSnapshotIdentifier=snapshot_identifier,
                DBInstanceIdentifier=DBINSTANCEID
                )
            logger.info("Successfully created instance snapshot: %s", response.get('DBSnapshot', {}).get('DBSnapshotIdentifier'))
            
            if 'DBSnapshot' in response:
                # Removing timestamp fields as they might cause issues with CloudFormation Custom Resource response handling
                # or are not required by the stack for the custom resource to correctly complete.
                response['DBSnapshot'].pop('SnapshotCreateTime', None) 
                response['DBSnapshot'].pop('InstanceCreateTime', None) 
            send(event, context, SUCCESS, reason="Instance snapshot created successfully.", response_data=response)
        except ClientError as error:
            logger.error("Failed to create instance snapshot for %s: %s", DBINSTANCEID, error, exc_info=True)
            send(event, context, FAILED, reason=str(error), response_data={})


if __name__ == "__main__":
    # This block is for local testing and needs a mock event and context.
    # For now, it's unlikely to be run directly without modification.
    # import doctest
    # doctest.testmod()
    logger.info("Running in __main__ for local testing (requires mock event/context).")
    # Example mock event and context (very basic)
    mock_event = {
      "RequestType": "Create",
      "ResponseURL": "http://pre-signed-S3-url-for-response",
      "StackId": "arn:aws:cloudformation:us-west-2:123456789012:stack/MyStack/guid",
      "RequestId": "unique id for this create request",
      "LogicalResourceId": "MyRDSBackupLambda",
      "ResourceType": "Custom::RDSSnapshot",
      "ResourceProperties": {
        "DBInstanceIdentifier": os.environ.get("DBInstanceIdentifier", "mydbinstance"),
        "DBSnapshotIdentifier": os.environ.get("DBSnapshotIdentifier", "mydbsnapshot")
      }
    }
    class MockContext:
        def __init__(self):
            self.log_stream_name = "local_testing_log_stream"
            self.log_group_name = "local_testing_log_group"
            self.aws_request_id = "local_testing_request_id"
            self.memory_limit_in_mb = 128
        
        def get_remaining_time_in_millis(self):
            return 30000 # 30 seconds

    # Set environment variables if not already set for local testing
    os.environ.setdefault('DBInstanceIdentifier', 'your-db-instance-id')
    os.environ.setdefault('DBSnapshotIdentifier', 'your-snapshot-id-prefix')
    
    # Potentially mock boto3 calls if you don't want to hit AWS during local test
    # handler(mock_event, MockContext())
    pass
