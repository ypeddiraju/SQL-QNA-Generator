"""
Abstract base class for database connectors.

Defines the interface that all database connectors must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple, Optional
import logging

from .config import Config
from .exceptions import DatabaseConnectionError, SchemaDiscoveryError


logger = logging.getLogger(__name__)


class DatabaseConnectorBase(ABC):
    """Abstract base class for database connectors."""
    
    def __init__(self, config: Config):
        """Initialize database connector with configuration."""
        self.config = config
        
    @abstractmethod
    def test_connection(self) -> bool:
        """Test database connection and return True if successful."""
        pass
    
    @abstractmethod
    def get_all_tables(self) -> List[str]:
        """
        Retrieve all user tables from the database.
        
        Returns:
            List of table names
        """
        pass
    
    @abstractmethod
    def get_table_schemas(self, table_names: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve column information for specified tables.
        
        Args:
            table_names: List of table names to analyze
            
        Returns:
            Dictionary mapping table names to their column definitions
        """
        pass
    
    @abstractmethod
    def get_table_relationships(self, table_names: List[str]) -> List[Dict[str, Any]]:
        """
        Discover foreign key relationships between specified tables.
        
        Args:
            table_names: List of table names to analyze
            
        Returns:
            List of relationship definitions
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def _get_related_sample(self, cursor, primary_table: str, target_table: str, 
                          primary_rows: List[Dict], relationships: List[Dict]) -> List[Dict[str, Any]]:
        """Get sample data from target table related to primary table data."""
        pass
    
    @abstractmethod
    def _get_basic_sample(self, cursor, table_name: str, sample_size: int) -> List[Dict[str, Any]]:
        """Get basic sample from table when no relationship exists."""
        pass
    
    def _serialize_value(self, value: Any) -> Any:
        """Convert non-serializable types to strings."""
        if value is not None and not isinstance(value, (str, int, float, bool)):
            return str(value)
        return value
    
    def _serialize_row(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize all values in a row dictionary."""
        return {key: self._serialize_value(value) for key, value in row_dict.items()}
