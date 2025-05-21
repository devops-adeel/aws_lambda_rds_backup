# AWS RDS Management Utilities

## Description

This project provides a suite of Python scripts designed to help manage AWS Relational Database Service (RDS) instances. It includes an AWS Lambda function for automated RDS backups, a command-line script for restoring RDS instances or clusters to a point in time, and a command-line script to query RDS instance details such as cluster membership.

## Features

*   **Automated RDS Backups:** An AWS Lambda function (`lambda_function.py`) that can be deployed to create snapshots of RDS instances or clusters.
*   **Point-in-Time Restore:** A script (`rds_restore.py`) to restore RDS instances or clusters to their latest restorable time, creating a new instance or cluster.
*   **Cluster Status Query:** A utility script (`query_db.py`) to quickly check if an RDS instance is part of a DB cluster.
*   **Error Handling:** Improved error handling across all scripts.
*   **Logging:** Comprehensive logging for better traceability and debugging.
*   **Testing:** Unit tests for core functionalities.
*   **Centralized Configuration:** Utilizes environment variables for flexible configuration.
*   **Shared Utilities:** Common functions are refactored into `common/utils.py`.

## Prerequisites

*   Python 3.x (Developed and tested with Python 3.10+)
*   `pipenv` for managing Python dependencies.
*   AWS CLI configured with appropriate credentials and default region.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    ```
2.  **Navigate to the project directory:**
    ```bash
    cd <repository_name>
    ```
3.  **Install dependencies using pipenv:**
    ```bash
    pipenv install
    ```
4.  **Activate the virtual environment (optional but recommended):**
    ```bash
    pipenv shell
    ```
    Alternatively, prefix commands with `pipenv run`.

## Configuration (Environment Variables)

The scripts rely on the following environment variables for configuration:

*   **`DBINSTANCEID`**:
    *   **Used by**: `lambda_function.py`, `rds_restore.py`, `query_db.py`
    *   **Description**: The DBInstanceIdentifier of the target AWS RDS instance.
*   **`DBSNAPSHOTID`**:
    *   **Used by**: `lambda_function.py`
    *   **Description**: A prefix for the snapshot identifier. The Lambda function appends the current date (YYYY-MM-DD) to this prefix to create unique snapshot names (e.g., `myprefix-2023-10-27`).
*   **`NEW_CLUSTER_ID`**:
    *   **Used by**: `rds_restore.py`
    *   **Description**: The desired DBClusterIdentifier for the new cluster when restoring a clustered RDS instance. Required if the source `DBINSTANCEID` is part of a cluster.
*   **`NEW_INSTANCEID`**:
    *   **Used by**: `rds_restore.py`
    *   **Description**: The desired DBInstanceIdentifier for the new instance when restoring a non-clustered (standalone) RDS instance. Required if the source `DBINSTANCEID` is not part of a cluster.

## Usage

### `lambda_function.py` (RDS Backup Lambda)

*   **Purpose**: Designed to be deployed as an AWS Lambda function. It creates a snapshot of the specified RDS instance or cluster.
*   **Deployment**: Typically packaged and deployed via AWS CloudFormation, AWS SAM, or manually through the AWS Lambda console. It's often triggered on a schedule (e.g., daily via Amazon EventBridge).
*   **Configuration**:
    *   Set the `DBINSTANCEID` and `DBSNAPSHOTID` environment variables within the Lambda function's configuration.
*   **Required IAM Permissions (for the Lambda execution role):**
    *   `rds:DescribeDBInstances`
    *   `rds:CreateDBSnapshot` (for non-cluster instances)
    *   `rds:CreateDBClusterSnapshot` (for cluster instances)
    *   `logs:CreateLogGroup`
    *   `logs:CreateLogStream`
    *   `logs:PutLogEvents`

### `rds_restore.py` (Restore Script)

*   **Purpose**: Restores the RDS instance specified by `DBINSTANCEID` to its latest restorable point in time, creating a new instance or cluster.
*   **Command**:
    ```bash
    python rds_restore.py
    ```
    (or `pipenv run python rds_restore.py` if not in `pipenv shell`)
*   **Configuration (Environment Variables)**:
    *   `DBINSTANCEID`: The source instance/cluster to restore from.
    *   If `DBINSTANCEID` is part of a cluster:
        *   `NEW_CLUSTER_ID`: The name for the new cluster to be created.
    *   If `DBINSTANCEID` is a standalone instance:
        *   `NEW_INSTANCEID`: The name for the new instance to be created.
*   **Required IAM Permissions (for the user/role running the script):**
    *   `rds:DescribeDBInstances`
    *   `rds:RestoreDBInstanceToPointInTime` (for non-cluster instances)
    *   `rds:RestoreDBClusterToPointInTime` (for cluster instances)

### `query_db.py` (Query Script)

*   **Purpose**: Checks if the RDS instance specified by `DBINSTANCEID` is part of a DB cluster.
*   **Command**:
    ```bash
    python query_db.py
    ```
    (or `pipenv run python query_db.py` if not in `pipenv shell`)
*   **Configuration (Environment Variables)**:
    *   `DBINSTANCEID`: The instance to query.
*   **Required IAM Permissions (for the user/role running the script):**
    *   `rds:DescribeDBInstances`

## Running Tests

To run the unit tests:

1.  Ensure you are in the root directory of the project.
2.  If you haven't already, set up your Python path to include the project root for imports to work correctly:
    ```bash
    # For Linux/macOS
    export PYTHONPATH=$PWD 
    # For Windows (PowerShell)
    # $env:PYTHONPATH = ".;" + $env:PYTHONPATH 
    ```
    (This might be needed if you are running tests outside of an IDE that handles paths automatically).
3.  Run the tests using the `unittest` module:
    ```bash
    python -m unittest discover tests
    ```
    Or, if you prefer, from within the `tests` directory:
    ```bash
    python -m unittest discover
    ```

## Contributing

Please refer to `CONTRIBUTING.md` for details on how to contribute to this project. (Note: `CONTRIBUTING.md` not created in this exercise).

## License

This project is licensed under the terms of the MIT License. Please see the `LICENSE` file for more details. (Note: `LICENSE` file not created in this exercise).
