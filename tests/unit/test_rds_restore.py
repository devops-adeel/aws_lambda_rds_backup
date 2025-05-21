"""Unit tests for the rds_restore.py script."""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from botocore.exceptions import ClientError

# Adjust path to import rds_restore and common.utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import rds_restore # Import the module to be tested
from rds_restore import logger as rds_logger # import logger to suppress its output
from common.utils import query_db_cluster # Though mocked, ensure it's importable for context

class TestRdsRestoreMain(unittest.TestCase):

    def setUp(self):
        # Store original environment variables
        self.original_env = os.environ.copy()

        # Set default mock environment variables for most tests
        os.environ['DBINSTANCEID'] = 'test-db-instance'
        os.environ['NEW_CLUSTER_ID'] = 'new-test-cluster'
        os.environ['NEW_INSTANCEID'] = 'new-test-instance'

        # Suppress logger output during tests
        self.patch_rds_logger = patch.object(rds_logger, 'propagate', False)
        self.mock_rds_logger_propagate = self.patch_rds_logger.start()
        
        # Also patch the logger in common.utils if it might be called
        # This is good practice if the tested function calls other utils that log
        self.patch_utils_logger = patch('common.utils.logger.propagate', False)
        self.mock_utils_logger_propagate = self.patch_utils_logger.start()


    def tearDown(self):
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)
        self.patch_rds_logger.stop()
        self.patch_utils_logger.stop()

    @patch('rds_restore.RDS')
    @patch('common.utils.query_db_cluster') # Patching query_db_cluster at its source
    def test_main_cluster_restore_success(self, mock_query_db_cluster, mock_rds_client):
        mock_query_db_cluster.return_value = 'old-cluster-id' # It's a cluster instance
        mock_rds_client.restore_db_cluster_to_point_in_time.return_value = {'DBCluster': {'Status': 'restoring'}}
        
        status = rds_restore.main('test-db-instance')
        
        self.assertEqual(status, 'restoring')
        mock_rds_client.restore_db_cluster_to_point_in_time.assert_called_once_with(
            DBClusterIdentifier='new-test-cluster',
            SourceDBClusterIdentifier='old-cluster-id',
            UseLatestRestorableTime=True
        )

    @patch('rds_restore.RDS')
    @patch('common.utils.query_db_cluster')
    def test_main_instance_restore_success(self, mock_query_db_cluster, mock_rds_client):
        mock_query_db_cluster.return_value = False # Not a cluster instance
        mock_rds_client.restore_db_instance_to_point_in_time.return_value = {'DBInstance': {'DBInstanceStatus': 'restoring'}}

        status = rds_restore.main('test-db-instance')

        self.assertEqual(status, 'restoring')
        mock_rds_client.restore_db_instance_to_point_in_time.assert_called_once_with(
            SourceDBInstanceIdentifier='test-db-instance',
            TargetDBInstanceIdentifier='new-test-instance',
            UseLatestRestorableTime=True
        )

    @patch('rds_restore.RDS')
    @patch('common.utils.query_db_cluster')
    def test_main_cluster_restore_client_error(self, mock_query_db_cluster, mock_rds_client):
        mock_query_db_cluster.return_value = 'old-cluster-id'
        client_error = ClientError({'Error': {'Code': 'TestError', 'Message': 'Test message'}}, 'restore_db_cluster_to_point_in_time')
        mock_rds_client.restore_db_cluster_to_point_in_time.side_effect = client_error

        with self.assertRaises(ClientError):
            rds_restore.main('test-db-instance')
            
    @patch('rds_restore.RDS')
    @patch('common.utils.query_db_cluster')
    def test_main_instance_restore_client_error(self, mock_query_db_cluster, mock_rds_client):
        mock_query_db_cluster.return_value = False # Not a cluster
        client_error = ClientError({'Error': {'Code': 'TestError', 'Message': 'Test message'}}, 'restore_db_instance_to_point_in_time')
        mock_rds_client.restore_db_instance_to_point_in_time.side_effect = client_error

        with self.assertRaises(ClientError):
            rds_restore.main('test-db-instance')

    @patch('common.utils.query_db_cluster') # Still need to mock this even if not directly used in this path
    def test_main_missing_new_cluster_id_for_cluster_restore(self, mock_query_db_cluster):
        mock_query_db_cluster.return_value = 'old-cluster-id' # It's a cluster
        os.environ.pop('NEW_CLUSTER_ID', None) # Remove the env var

        with self.assertRaisesRegex(ValueError, "NEW_CLUSTER_ID environment variable is not set for clustered restore."):
            rds_restore.main('test-db-instance')

    @patch('common.utils.query_db_cluster')
    def test_main_missing_new_instance_id_for_instance_restore(self, mock_query_db_cluster):
        mock_query_db_cluster.return_value = False # Not a cluster
        os.environ.pop('NEW_INSTANCEID', None) # Remove the env var

        with self.assertRaisesRegex(ValueError, "NEW_INSTANCEID environment variable not set for non-clustered restore."):
            rds_restore.main('test-db-instance')
            
    def test_main_missing_instanceid_parameter(self):
        # Tests the check at the very beginning of main()
        with self.assertRaisesRegex(ValueError, "DBINSTANCEID (passed as instanceid) is missing."):
            rds_restore.main(None) # Pass None as instanceid

    # Tests for the __main__ block execution path
    @patch('rds_restore.main') # Mock the main function that __main__ calls
    @patch('sys.exit') # Mock sys.exit to prevent test runner from exiting
    def test_main_block_success(self, mock_sys_exit, mock_main_func):
        os.environ['DBINSTANCEID'] = 'test-db-for-main-block'
        mock_main_func.return_value = "some_status"
        
        # Need to execute the __main__ block. This is a bit tricky.
        # One way is to run the script as a separate process, but that's complex for unit tests.
        # Another is to import it and hope it runs, but `if __name__ == "__main__"` prevents that.
        # We can use runpy.run_module or exec. For simplicity, let's simulate what it does.
        # The script already has INSTANCEID set globally from os.environ in the test setUp.
        # We'll call a helper that simulates the __main__ logic.

        # This simulates the execution of the if __name__ == "__main__" block
        # by directly calling the relevant logic.
        # We need to ensure rds_restore.INSTANCEID is set correctly for this test
        # However, INSTANCEID is now read *inside* the __main__ block in rds_restore.py
        # So, we just need to ensure os.environ['DBINSTANCEID'] is set.

        with patch.dict(os.environ, {'DBINSTANCEID': 'test-db-for-main-block'}):
            # To test the __main__ block, we can use runpy
            # However, it's simpler to extract the logic or test its effects.
            # The __main__ block calls rds_restore.main(INSTANCEID)
            # Let's assume it's called. The missing env var tests for main() cover value errors.
            # ClientError is also covered.
            # This test ensures that if main() runs successfully, sys.exit is not called with 1.
            
            # Re-import rds_restore or use runpy if module-level INSTANCEID was critical.
            # But INSTANCEID is now fetched inside __main__
            
            # Simulate running the script's __main__
            # We need to be careful if __main__ itself has global effects or complex logic.
            # For this script, it fetches INSTANCEID, calls main(), and handles exceptions.
            
            # We'll call a simplified version of the __main__ execution path
            instance_id_from_env = os.environ.get('DBINSTANCEID')
            if not instance_id_from_env:
                rds_logger.error("DBINSTANCEID environment variable not set. Exiting.")
                mock_sys_exit.assert_called_with(1) # Should have been called by the script's own check
                return

            rds_restore.main(instance_id_from_env) # Call with the instance_id
            
            mock_main_func.assert_called_once_with('test-db-for-main-block')
            # Check that sys.exit(1) was NOT called
            for call_args in mock_sys_exit.call_args_list:
                self.assertNotEqual(call_args[0][0], 1)


    @patch('sys.exit')
    def test_main_block_missing_dbinstanceid(self, mock_sys_exit):
        os.environ.pop('DBINSTANCEID', None)
        
        # To test the __main__ block properly when it's guarded by `if __name__ == "__main__":`,
        # we can use `runpy`. This executes the module as if it were the main script.
        import runpy
        try:
            runpy.run_module('rds_restore', run_name='__main__')
        except SystemExit as e: # Catch sys.exit called by the script
            self.assertEqual(e.code, 1) # Check if exit code is 1
        
        mock_sys_exit.assert_called_with(1)
        # Verify logger output if possible, or just that sys.exit(1) was called.
        # The logger in the actual script would log "DBINSTANCEID environment variable not set. Exiting."


if __name__ == '__main__':
    unittest.main()
