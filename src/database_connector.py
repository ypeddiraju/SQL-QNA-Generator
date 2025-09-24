"""
Database connectivity module for SQL Server integration.

Handles schema discovery, relationship detection, and relational data sampling.
"""

import logging
import pyodbc
from typing import Dict, List, Any, Tuple, Optional

from .config import Config
from .exceptions import DatabaseConnectionError, SchemaDiscoveryError


logger = logging.getLogger(__name__)


class DatabaseConnector:
    """Handles SQL Server database connections and operations."""
    
    def __init__(self, config: Config):
        """Initialize database connector with configuration."""
        self.config = config
        self.connection_string = config.connection_string
        # Enable connection pooling for better resource management
        pyodbc.pooling = True
    
    def _create_connection(self):
        """Create a database connection with proper configuration."""
        return pyodbc.connect(
            self.connection_string,
            timeout=self.config.db_login_timeout
        )
        
    def test_connection(self) -> bool:
        """Test database connection with retry logic and return True if successful."""
        import time
        
        last_error = None
        
        for attempt in range(self.config.db_retry_count):
            try:
                logger.info(f"Testing database connection (attempt {attempt + 1}/{self.config.db_retry_count})")
                
                with self._create_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    
                logger.info("Database connection test successful")
                return True
                
            except Exception as e:
                last_error = e
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.db_retry_count - 1:
                    logger.info(f"Retrying in {self.config.db_retry_interval} seconds...")
                    time.sleep(self.config.db_retry_interval)
        
        # All attempts failed
        logger.error(f"All {self.config.db_retry_count} connection attempts failed")
        raise DatabaseConnectionError(f"Failed to connect to database: {last_error}")
    
    def get_all_tables(self) -> List[str]:
        """
        Retrieve all user tables from the database.
        
        Returns:
            List of table names
        """
        try:
            with self._create_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_SCHEMA != 'sys'
                AND TABLE_NAME NOT LIKE 'sys%'
                AND TABLE_NAME NOT LIKE 'MSreplication%'
                ORDER BY TABLE_NAME
                """
                
                cursor.execute(query)
                tables = [row.TABLE_NAME for row in cursor.fetchall()]
                logger.info(f"Found {len(tables)} user tables")
                return tables
                
        except Exception as e:
            logger.error(f"Failed to retrieve table list: {e}")
            raise SchemaDiscoveryError(f"Failed to discover tables: {e}")
    
    def get_table_schemas(self, table_names: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve column information for specified tables.
        
        Args:
            table_names: List of table names to analyze
            
        Returns:
            Dictionary mapping table names to their column definitions
        """
        schemas = {}
        
        try:
            with self._create_connection() as conn:
                cursor = conn.cursor()
                
                for table_name in table_names:
                    logger.debug(f"Discovering schema for table: {table_name}")
                    
                    # Query INFORMATION_SCHEMA for column information
                    query = """
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE,
                        COLUMN_DEFAULT,
                        CHARACTER_MAXIMUM_LENGTH,
                        NUMERIC_PRECISION,
                        NUMERIC_SCALE
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                    """
                    
                    cursor.execute(query, table_name)
                    columns = []
                    
                    for row in cursor.fetchall():
                        column_info = {
                            'column_name': row.COLUMN_NAME,
                            'data_type': row.DATA_TYPE,
                            'is_nullable': row.IS_NULLABLE == 'YES',
                            'default_value': row.COLUMN_DEFAULT,
                            'max_length': row.CHARACTER_MAXIMUM_LENGTH,
                            'precision': row.NUMERIC_PRECISION,
                            'scale': row.NUMERIC_SCALE
                        }
                        columns.append(column_info)
                    
                    if not columns:
                        raise SchemaDiscoveryError(f"Table '{table_name}' not found or has no columns")
                    
                    schemas[table_name] = columns
                    logger.info(f"Discovered {len(columns)} columns for table '{table_name}'")
                
                return schemas
                
        except pyodbc.Error as e:
            logger.error(f"Database error during schema discovery: {e}")
            raise SchemaDiscoveryError(f"Failed to discover table schemas: {e}")
    
    def get_table_relationships(self, table_names: List[str]) -> List[Dict[str, Any]]:
        """
        Discover foreign key relationships between specified tables.
        
        Args:
            table_names: List of table names to analyze
            
        Returns:
            List of relationship definitions
        """
        relationships = []
        
        try:
            with self._create_connection() as conn:
                cursor = conn.cursor()
                
                # Query for foreign key relationships
                query = """
                SELECT 
                    fk.name AS FK_NAME,
                    tp.name AS PARENT_TABLE,
                    cp.name AS PARENT_COLUMN,
                    tr.name AS REFERENCED_TABLE,
                    cr.name AS REFERENCED_COLUMN
                FROM sys.foreign_keys fk
                INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
                INNER JOIN sys.tables tp ON fkc.parent_object_id = tp.object_id
                INNER JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
                INNER JOIN sys.tables tr ON fkc.referenced_object_id = tr.object_id
                INNER JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
                WHERE tp.name IN ({placeholders}) OR tr.name IN ({placeholders})
                """.format(placeholders=','.join(['?'] * len(table_names)))
                
                cursor.execute(query, table_names + table_names)
                
                for row in cursor.fetchall():
                    # Only include relationships where both tables are in our target list
                    if row.PARENT_TABLE in table_names and row.REFERENCED_TABLE in table_names:
                        relationship = {
                            'fk_name': row.FK_NAME,
                            'parent_table': row.PARENT_TABLE,
                            'parent_column': row.PARENT_COLUMN,
                            'referenced_table': row.REFERENCED_TABLE,
                            'referenced_column': row.REFERENCED_COLUMN
                        }
                        relationships.append(relationship)
                
                logger.info(f"Discovered {len(relationships)} foreign key relationships")
                return relationships
                
        except pyodbc.Error as e:
            logger.error(f"Database error during relationship discovery: {e}")
            raise SchemaDiscoveryError(f"Failed to discover table relationships: {e}")
    
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
        sample_data = {}
        
        try:
            with self._create_connection() as conn:
                cursor = conn.cursor()
                
                # First, get sample from primary table
                logger.debug(f"Sampling {sample_size} rows from primary table: {primary_table}")
                
                primary_query = f"SELECT TOP {sample_size} * FROM [{primary_table}]"
                cursor.execute(primary_query)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                
                # Fetch sample data
                primary_rows = []
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    # Convert any non-serializable types to strings
                    for key, value in row_dict.items():
                        if value is not None and not isinstance(value, (str, int, float, bool)):
                            row_dict[key] = str(value)
                    primary_rows.append(row_dict)
                
                sample_data[primary_table] = primary_rows
                logger.info(f"Collected {len(primary_rows)} rows from primary table '{primary_table}'")
                
                # Get relationships to determine how to fetch related data
                relationships = self.get_table_relationships(all_tables)
                
                # For each other table, get related data based on foreign keys
                for table_name in all_tables:
                    if table_name == primary_table:
                        continue
                    
                    # Find relationship between primary table and this table
                    related_data = self._get_related_sample(cursor, primary_table, table_name, primary_rows, relationships)
                    
                    if related_data:
                        sample_data[table_name] = related_data
                        logger.info(f"Collected {len(related_data)} related rows from table '{table_name}'")
                    else:
                        # If no direct relationship, get a basic sample
                        logger.warning(f"No direct relationship found for '{table_name}', getting basic sample")
                        basic_sample = self._get_basic_sample(cursor, table_name, sample_size)
                        sample_data[table_name] = basic_sample
                        logger.info(f"Collected {len(basic_sample)} basic sample rows from table '{table_name}'")
                
                return sample_data
                
        except pyodbc.Error as e:
            logger.error(f"Database error during relational sampling: {e}")
            raise SchemaDiscoveryError(f"Failed to perform relational sampling: {e}")
    
    def _get_related_sample(self, cursor, primary_table: str, target_table: str, 
                          primary_rows: List[Dict], relationships: List[Dict]) -> List[Dict[str, Any]]:
        """Get sample data from target table related to primary table data."""
        
        # Find foreign key relationship
        fk_relationship = None
        for rel in relationships:
            if ((rel['parent_table'] == primary_table and rel['referenced_table'] == target_table) or
                (rel['parent_table'] == target_table and rel['referenced_table'] == primary_table)):
                fk_relationship = rel
                break
        
        if not fk_relationship:
            return []
        
        try:
            # Determine the direction of the relationship
            if fk_relationship['parent_table'] == primary_table:
                # Primary table references target table
                foreign_key_column = fk_relationship['parent_column']
                referenced_column = fk_relationship['referenced_column']
                
                # Get unique foreign key values from primary sample
                fk_values = set()
                for row in primary_rows:
                    if foreign_key_column in row and row[foreign_key_column] is not None:
                        fk_values.add(row[foreign_key_column])
                
                if not fk_values:
                    return []
                
                # Query target table for these values
                placeholders = ','.join(['?' for _ in fk_values])
                query = f"SELECT * FROM [{target_table}] WHERE [{referenced_column}] IN ({placeholders})"
                cursor.execute(query, list(fk_values))
                
            else:
                # Target table references primary table
                foreign_key_column = fk_relationship['parent_column']
                referenced_column = fk_relationship['referenced_column']
                
                # Get primary key values from primary sample
                pk_values = set()
                for row in primary_rows:
                    if referenced_column in row and row[referenced_column] is not None:
                        pk_values.add(row[referenced_column])
                
                if not pk_values:
                    return []
                
                # Query target table for these values
                placeholders = ','.join(['?' for _ in pk_values])
                query = f"SELECT * FROM [{target_table}] WHERE [{foreign_key_column}] IN ({placeholders})"
                cursor.execute(query, list(pk_values))
            
            # Process results
            columns = [desc[0] for desc in cursor.description]
            related_rows = []
            
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                # Convert any non-serializable types to strings
                for key, value in row_dict.items():
                    if value is not None and not isinstance(value, (str, int, float, bool)):
                        row_dict[key] = str(value)
                related_rows.append(row_dict)
            
            return related_rows
            
        except Exception as e:
            logger.warning(f"Error getting related sample for {target_table}: {e}")
            return []
    
    def _get_basic_sample(self, cursor, table_name: str, sample_size: int) -> List[Dict[str, Any]]:
        """Get basic sample from table when no relationship exists."""
        try:
            query = f"SELECT TOP {sample_size} * FROM [{table_name}]"
            cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            rows = []
            
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                # Convert any non-serializable types to strings
                for key, value in row_dict.items():
                    if value is not None and not isinstance(value, (str, int, float, bool)):
                        row_dict[key] = str(value)
                rows.append(row_dict)
            
            return rows
            
        except Exception as e:
            logger.warning(f"Error getting basic sample for {table_name}: {e}")
            return []
