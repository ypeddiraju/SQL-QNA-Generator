"""
Database connectivity module - factory wrapper for backwards compatibility.

This module provides a factory-based approach to create database connectors
for different database types (SQL Server, MySQL, etc.).
"""

import logging
from typing import Dict, List, Any, Tuple, Optional

from .config import Config
from .database_factory import create_database_connector, DatabaseConnectorFactory
from .database_base import DatabaseConnectorBase


logger = logging.getLogger(__name__)


class DatabaseConnector:
    """
    Legacy database connector class for backwards compatibility.
    
    This class wraps the factory-based connector creation and delegates
    all operations to the appropriate database-specific connector.
    """
    
    def __init__(self, config: Config):
        """Initialize database connector with configuration."""
        self.config = config
        self._connector = create_database_connector(config)
    
    def test_connection(self) -> bool:
        """Test database connection with retry logic and return True if successful."""
        return self._connector.test_connection()
    
    def get_all_tables(self) -> List[str]:
        """
        Retrieve all user tables from the database.
        
        Returns:
            List of table names
        """
        return self._connector.get_all_tables()
    
    def get_table_schemas(self, table_names: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve column information for specified tables.
        
        Args:
            table_names: List of table names to analyze
            
        Returns:
            Dictionary mapping table names to their column definitions
        """
        return self._connector.get_table_schemas(table_names)
    
    def get_table_relationships(self, table_names: List[str]) -> List[Dict[str, Any]]:
        """
        Discover foreign key relationships between specified tables.
        
        Args:
            table_names: List of table names to analyze
            
        Returns:
            List of relationship definitions
        """
        return self._connector.get_table_relationships(table_names)
    
    def get_relational_sample(self, primary_table: str, all_tables: List[str], sample_size: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform relational data sampling starting from primary table.
        
        Args:
            primary_table: The table to start sampling from
            all_tables: All tables to include in the sample
            sample_size: Number of rows to sample from primary table
            
        Returns:
            Dictionary mapping table names to their sample data
        """
        return self._connector.get_relational_sample(primary_table, all_tables, sample_size)
    
    def resolve_table_names(self, table_names: List[str]) -> List[str]:
        """
        Resolve unqualified table names to their fully qualified equivalents.
        
        Args:
            table_names: List of table names (qualified or unqualified)
            
        Returns:
            List of fully qualified table names
        """
        return self._connector.resolve_table_names(table_names)
