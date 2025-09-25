"""
Database connector factory for creating appropriate database connectors.

Creates the correct database connector based on the database type specified in configuration.
"""

import logging
from typing import Union

from .config import Config
from .database_base import DatabaseConnectorBase
from .database_sqlserver import SqlServerConnector
from .database_mysql import MySQLConnector
from .exceptions import DatabaseConnectionError


logger = logging.getLogger(__name__)


class DatabaseConnectorFactory:
    """Factory class for creating database connectors."""
    
    @staticmethod
    def create_connector(config: Config) -> DatabaseConnectorBase:
        """
        Create a database connector based on the configuration.
        
        Args:
            config: Configuration object with database type and connection details
            
        Returns:
            Appropriate database connector instance
            
        Raises:
            DatabaseConnectionError: If unsupported database type is specified
        """
        db_type = config.db_type.lower().strip()
        
        logger.info(f"Creating database connector for type: '{db_type}'")
        
        if db_type == "sqlserver" or db_type == "mssql":
            logger.info("Using SqlServerConnector")
            return SqlServerConnector(config)
        elif db_type == "mysql":
            logger.info("Using MySQLConnector")
            return MySQLConnector(config)
        else:
            supported_types = ["sqlserver", "mssql", "mysql"]
            logger.error(f"Database type '{db_type}' not recognized. Length: {len(db_type)}, ASCII: {[ord(c) for c in db_type]}")
            raise DatabaseConnectionError(
                f"Unsupported database type: {db_type}. "
                f"Supported types: {', '.join(supported_types)}"
            )
    
    @staticmethod
    def get_supported_database_types() -> list:
        """
        Get list of supported database types.
        
        Returns:
            List of supported database type strings
        """
        return ["sqlserver", "mssql", "mysql"]


# For backwards compatibility, create an alias to the factory method
def create_database_connector(config: Config) -> DatabaseConnectorBase:
    """
    Create a database connector based on the configuration.
    
    This is a convenience function that wraps the factory method.
    
    Args:
        config: Configuration object with database type and connection details
        
    Returns:
        Appropriate database connector instance
    """
    return DatabaseConnectorFactory.create_connector(config)
