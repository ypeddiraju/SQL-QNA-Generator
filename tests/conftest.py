"""
Test configuration and fixtures.
"""

import pytest
import os
from unittest.mock import Mock

from src.config import Config


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock(spec=Config)
    config.openai_api_key = "test-api-key"
    config.openai_model = "gpt-4"
    config.db_server = "test-server"
    config.db_database = "test-database"
    config.db_username = "test-user"
    config.db_password = "test-password"
    config.db_driver = "ODBC Driver 17 for SQL Server"
    config.output_file = "test_output.json"
    config.sample_size = 5
    config.min_questions = 10
    config.target_join_percentage = 40
    config.log_level = "INFO"
    config.connection_string = "test-connection-string"
    return config


@pytest.fixture
def sample_schemas():
    """Sample table schemas for testing."""
    return {
        'Employees': [
            {'column_name': 'EmployeeID', 'data_type': 'int', 'is_nullable': False},
            {'column_name': 'FirstName', 'data_type': 'varchar', 'is_nullable': False},
            {'column_name': 'LastName', 'data_type': 'varchar', 'is_nullable': False},
            {'column_name': 'DepartmentID', 'data_type': 'int', 'is_nullable': True}
        ],
        'Departments': [
            {'column_name': 'DepartmentID', 'data_type': 'int', 'is_nullable': False},
            {'column_name': 'DepartmentName', 'data_type': 'varchar', 'is_nullable': False},
            {'column_name': 'Location', 'data_type': 'varchar', 'is_nullable': True}
        ]
    }


@pytest.fixture
def sample_relationships():
    """Sample foreign key relationships for testing."""
    return [
        {
            'fk_name': 'FK_Employees_Departments',
            'parent_table': 'Employees',
            'parent_column': 'DepartmentID',
            'referenced_table': 'Departments',
            'referenced_column': 'DepartmentID'
        }
    ]


@pytest.fixture
def sample_data():
    """Sample table data for testing."""
    return {
        'Employees': [
            {'EmployeeID': 1, 'FirstName': 'John', 'LastName': 'Smith', 'DepartmentID': 1},
            {'EmployeeID': 2, 'FirstName': 'Jane', 'LastName': 'Doe', 'DepartmentID': 2},
            {'EmployeeID': 3, 'FirstName': 'Bob', 'LastName': 'Johnson', 'DepartmentID': 1}
        ],
        'Departments': [
            {'DepartmentID': 1, 'DepartmentName': 'Engineering', 'Location': 'New York'},
            {'DepartmentID': 2, 'DepartmentName': 'Sales', 'Location': 'California'}
        ]
    }
