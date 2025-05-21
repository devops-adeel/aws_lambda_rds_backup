"""Unit tests for the lambda_function.py module."""

import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys
from botocore.exceptions import ClientError
import datetime # Needed for NOW

# Adjust path to import lambda_function and common.utils
# This assumes the tests are run from the root of the repository.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
import lambda_function
from lambda_function import logger as lambda_logger # import logger to suppress its output

class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        # Basic mock event and context
        self.mock_event = {
            'StackId': 'stack-id',
            'RequestId': 'request-id',
            'LogicalResourceId': 'logical-id',
            'ResponseURL': 'http://example.com/cfnresponse',
            'PhysicalResourceId': 'physical-resource-id-from-event' # Added for more complete event
        }
        self.mock_context = MagicMock()
        self.mock_context.log_stream_name = 'log-stream'
        self.mock_context.aws_request_id = 'test-request-id'
        self.mock_context.memory_limit_in_mb = 128
        self.mock_context.get_remaining_time_in_millis = MagicMock(return_value=30000)

        # Store original environment variables and module-level variables from lambda_function
        self.original_env = os.environ.copy()
        self.original_dbinstanceid = lambda_function.DBINSTANCEID
        self.original_dbsnapshotid = lambda_function.DBSNAPSHOTID
        self.original_now = lambda_function.NOW

        # Set default mock environment variables for most tests
        os.environ['DBInstanceIdentifier'] = 'test-db'
        os.environ['DBSnapshotIdentifier'] = 'test-snapshot-prefix'
        lambda_function.DBINSTANCEID = 'test-db'
        lambda_function.DBSNAPSHOTID = 'test-snapshot-prefix'
        
        # Mock datetime.datetime.now() for consistent snapshot identifiers
        # Store the original datetime class
        self.original_datetime_class = datetime.datetime
        # Mock datetime.datetime.now()
        self.mock_datetime_now = MagicMock(wraps=datetime.datetime)
        self.mock_datetime_now.now.return_value = self.original_datetime_class(2023, 1, 1, 12, 0, 0) # Fixed date
        # This patching method is more robust for datetime.datetime.now
        self.patch_datetime = patch('datetime.datetime', self.mock_datetime_now) 
        self.patch_datetime.start()
        lambda_function.NOW = self.mock_datetime_now.now.return_value


        # Suppress logger output during tests
        self.patch_lambda_logger = patch.object(lambda_logger, 'propagate', False)
        self.mock_lambda_logger_propagate = self.patch_lambda_logger.start()


    def tearDown(self):
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

        # Restore original module-level variables in lambda_function
        lambda_function.DBINSTANCEID = self.original_dbinstanceid
        lambda_function.DBSNAPSHOTID = self.original_dbsnapshotid
        lambda_function.NOW = self.original_now
        
        # Stop datetime patch
        self.patch_datetime.stop()

        # Stop logger patch
        self.patch_lambda_logger.stop()

    @patch('lambda_function.send')
    @patch('lambda_function.RDS') # Patches the RDS client instance in lambda_function module
    @patch('common.utils.query_db_cluster') # Patches the function imported from common.utils
    def test_handler_cluster_snapshot_success(self, mock_common_query_db_cluster, mock_rds_client, mock_send):
        mock_common_query_db_cluster.return_value = 'actual-cluster-id' # Instance is in a cluster
        mock_rds_client.create_db_cluster_snapshot.return_value = {'DBClusterSnapshot': {'Status': 'available', 'DBClusterSnapshotIdentifier': 'test-snapshot-prefix2023-01-01'}}
        
        lambda_function.handler(self.mock_event, self.mock_context)
        
        expected_snapshot_id = 'test-snapshot-prefix' + lambda_function.NOW.strftime("%Y-%m-%d")
        mock_rds_client.create_db_cluster_snapshot.assert_called_once_with(
            DBClusterSnapshotIdentifier=expected_snapshot_id,
            DBClusterIdentifier='actual-cluster-id'
        )
        mock_send.assert_called_once_with(
            self.mock_event, self.mock_context, 
            lambda_function.SUCCESS, 
            reason="Cluster snapshot created successfully.",
            response_data={'DBClusterSnapshot': {'Status': 'available', 'DBClusterSnapshotIdentifier': 'test-snapshot-prefix2023-01-01'}}
        )

    @patch('lambda_function.send')
    @patch('lambda_function.RDS')
    @patch('common.utils.query_db_cluster')
    def test_handler_instance_snapshot_success(self, mock_common_query_db_cluster, mock_rds_client, mock_send):
        mock_common_query_db_cluster.return_value = False # Not a cluster
        mock_snapshot_response = {
            'DBSnapshot': {
                'DBSnapshotIdentifier': 'test-snapshot-prefix2023-01-01',
                'Status': 'available', 
                'SnapshotCreateTime': 'some-time', 
                'InstanceCreateTime': 'some-other-time'
            }
        }
        mock_rds_client.create_db_snapshot.return_value = mock_snapshot_response
        
        lambda_function.handler(self.mock_event, self.mock_context)
        
        expected_snapshot_id = 'test-snapshot-prefix' + lambda_function.NOW.strftime("%Y-%m-%d")
        mock_rds_client.create_db_snapshot.assert_called_once_with(
            DBSnapshotIdentifier=expected_snapshot_id,
            DBInstanceIdentifier='test-db'
        )
        # Expected data after popping
        expected_response_data = {'DBSnapshot': {'DBSnapshotIdentifier': 'test-snapshot-prefix2023-01-01', 'Status': 'available'}}
        mock_send.assert_called_once_with(
            self.mock_event, self.mock_context,
            lambda_function.SUCCESS,
            reason="Instance snapshot created successfully.",
            response_data=expected_response_data
        )

    @patch('lambda_function.send')
    @patch('lambda_function.RDS')
    @patch('common.utils.query_db_cluster')
    def test_handler_instance_snapshot_failure_clienterror(self, mock_common_query_db_cluster, mock_rds_client, mock_send):
        mock_common_query_db_cluster.return_value = False # Not a cluster
        client_error = ClientError({'Error': {'Code': 'TestError', 'Message': 'Test message'}}, 'create_db_snapshot')
        mock_rds_client.create_db_snapshot.side_effect = client_error
        
        lambda_function.handler(self.mock_event, self.mock_context)
        
        mock_send.assert_called_once_with(
            self.mock_event, self.mock_context,
            lambda_function.FAILED,
            reason=str(client_error),
            response_data={} 
        )

    @patch('lambda_function.send')
    @patch('lambda_function.RDS') # Still need to patch RDS even if not directly used, to avoid real calls
    @patch('common.utils.query_db_cluster')
    def test_handler_cluster_snapshot_failure_clienterror(self, mock_common_query_db_cluster, mock_rds_client, mock_send):
        mock_common_query_db_cluster.return_value = 'actual-cluster-id' # Instance is in a cluster
        client_error = ClientError({'Error': {'Code': 'TestError', 'Message': 'Test message'}}, 'create_db_cluster_snapshot')
        mock_rds_client.create_db_cluster_snapshot.side_effect = client_error
        
        lambda_function.handler(self.mock_event, self.mock_context)
        
        mock_send.assert_called_once_with(
            self.mock_event, self.mock_context,
            lambda_function.FAILED,
            reason=str(client_error),
            response_data={}
        )
    
    @patch('lambda_function.send')
    # No need to patch RDS or query_db_cluster as env var check is before them
    def test_handler_missing_dbinstanceid_env_var(self, mock_send):
        # Set one of the required env vars to None or empty for this test
        lambda_function.DBINSTANCEID = None 
        # DBSNAPSHOTID is still 'test-snapshot-prefix'
        
        lambda_function.handler(self.mock_event, self.mock_context)

        expected_reason = "Missing required environment variable(s): DBInstanceIdentifier and/or DBSnapshotIdentifier must be set."
        # The physical_resource_id should be what's in the event if present
        expected_physical_resource_id = self.mock_event.get('PhysicalResourceId', self.mock_context.log_stream_name)
        
        mock_send.assert_called_once_with(
            self.mock_event, self.mock_context,
            lambda_function.FAILED,
            reason=expected_reason,
            physical_resource_id=expected_physical_resource_id
        )

    @patch('lambda_function.send')
    def test_handler_missing_dbsnapshotid_env_var(self, mock_send):
        lambda_function.DBSNAPSHOTID = '' # Empty string
        # DBINSTANCEID is still 'test-db'

        lambda_function.handler(self.mock_event, self.mock_context)

        expected_reason = "Missing required environment variable(s): DBInstanceIdentifier and/or DBSnapshotIdentifier must be set."
        expected_physical_resource_id = self.mock_event.get('PhysicalResourceId', self.mock_context.log_stream_name)

        mock_send.assert_called_once_with(
            self.mock_event, self.mock_context,
            lambda_function.FAILED,
            reason=expected_reason,
            physical_resource_id=expected_physical_resource_id
        )


if __name__ == '__main__':
    unittest.main()
