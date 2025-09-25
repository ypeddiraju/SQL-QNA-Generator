"""
Database connectivity module for MySQL integration.

Handles schema discovery, relationship detection, and relational data sampling.
"""

import logging
import pymysql
from pymysql import Error as MySQLError
from typing import Dict, List, Any, Tuple, Optional
import time

from .config import Config
from .exceptions import DatabaseConnectionError, SchemaDiscoveryError
from .database_base import DatabaseConnectorBase


logger = logging.getLogger(__name__)


class MySQLConnector(DatabaseConnectorBase):
    """Handles MySQL database connections and operations."""
    
    def __init__(self, config: Config):
        """Initialize database connector with configuration."""
        super().__init__(config)
        self.connection_params = config.mysql_connection_params
    
    def _create_connection(self):
        """Create a database connection with proper configuration."""
        try:
            conn = pymysql.connect(**self.connection_params)
            # Set session-level timeouts for this connection
            cursor = conn.cursor()
            cursor.execute("SET SESSION wait_timeout = 3600")  # 1 hour
            cursor.execute("SET SESSION interactive_timeout = 3600")  # 1 hour
            cursor.execute("SET SESSION net_read_timeout = 300")  # 5 minutes for reads
            cursor.execute("SET SESSION net_write_timeout = 300")  # 5 minutes for writes
            cursor.close()
            return conn
        except Exception as e:
            logger.error(f"Failed to create MySQL connection: {e}")
            raise
            
    def _ensure_connection_alive(self, conn):
        """Ensure the connection is alive and refresh if needed."""
        try:
            # Ping the connection to check if it's alive
            conn.ping(reconnect=True)
            return conn
        except Exception as e:
            logger.warning(f"Connection ping failed: {e}, creating new connection")
            try:
                conn.close()
            except:
                pass
            return self._create_connection()
        
    def test_connection(self) -> bool:
        """Test database connection with retry logic and return True if successful."""
        last_error = None
        
        for attempt in range(self.config.db_retry_count):
            try:
                logger.info(f"Testing MySQL database connection (attempt {attempt + 1}/{self.config.db_retry_count})")
                logger.info(f"Connecting to {self.config.db_server}:{self.config.db_port}/{self.config.db_database}")
                
                # Create connection with explicit timeout
                conn = self._create_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    logger.info("MySQL database connection test successful")
                    return True
                except Exception as query_error:
                    conn.close()
                    raise query_error
                    
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
        Retrieve all user tables from the database with retry logic.
        
        Returns:
            List of table names
        """
        last_error = None
        
        for attempt in range(self.config.db_retry_count):
            try:
                logger.info(f"Discovering tables (attempt {attempt + 1}/{self.config.db_retry_count})")
                
                conn = self._create_connection()
                try:
                    # Ensure connection is alive before starting query
                    conn = self._ensure_connection_alive(conn)
                    cursor = conn.cursor()
                    
                    query = """
                    SELECT TABLE_NAME
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    AND TABLE_SCHEMA = %s
                    AND TABLE_NAME NOT LIKE 'mysql_%%'
                    AND TABLE_NAME NOT LIKE 'performance_schema_%%'
                    AND TABLE_NAME NOT LIKE 'information_schema_%%'
                    AND TABLE_NAME NOT LIKE 'sys_%%'
                    ORDER BY TABLE_NAME
                    """
                    
                    cursor.execute(query, (self.config.db_database,))
                    tables = [row[0] for row in cursor.fetchall()]
                    cursor.close()
                    conn.close()
                    
                    logger.info(f"Found {len(tables)} user tables")
                    return tables
                    
                except Exception as query_error:
                    try:
                        conn.close()
                    except:
                        pass
                    raise query_error
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Table discovery attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.db_retry_count - 1:
                    logger.info(f"Retrying in {self.config.db_retry_interval} seconds...")
                    time.sleep(self.config.db_retry_interval)
        
        # All attempts failed
        logger.error(f"All {self.config.db_retry_count} table discovery attempts failed")
        raise SchemaDiscoveryError(f"Failed to discover tables: {last_error}")
    
    def _validate_table_exists(self, table_name: str, cursor) -> bool:
        """Check if a table exists and is accessible."""
        try:
            check_query = """
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = %s 
            AND TABLE_SCHEMA = %s 
            AND TABLE_TYPE = 'BASE TABLE'
            """
            cursor.execute(check_query, (table_name, self.config.db_database))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            logger.warning(f"Error checking table existence for '{table_name}': {e}")
            return False
    
    def get_table_schemas(self, table_names: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve column information for specified tables.
        
        Args:
            table_names: List of table names to analyze
            
        Returns:
            Dictionary mapping table names to their column definitions
        """
        schemas = {}
        skipped_tables = []
        
        conn = None
        try:
            conn = self._create_connection()
            cursor = conn.cursor()
            
            for table_name in table_names:
                logger.debug(f"Discovering schema for table: {table_name}")
                
                # First, validate that the table exists
                if not self._validate_table_exists(table_name, cursor):
                    logger.warning(f"Table '{table_name}' does not exist or is not accessible - skipping")
                    skipped_tables.append(table_name)
                    continue
                
                # Query INFORMATION_SCHEMA for column information
                query = """
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE,
                    COLUMN_KEY,
                    EXTRA
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = %s 
                AND TABLE_SCHEMA = %s
                ORDER BY ORDINAL_POSITION
                """
                
                cursor.execute(query, (table_name, self.config.db_database))
                columns = []
                
                for row in cursor.fetchall():
                    column_info = {
                        'column_name': row[0],
                        'data_type': row[1],
                        'is_nullable': row[2] == 'YES',
                        'default_value': row[3],
                        'max_length': row[4],
                        'precision': row[5],
                        'scale': row[6],
                        'column_key': row[7],
                        'extra': row[8]
                    }
                    columns.append(column_info)
                
                if not columns:
                    logger.warning(f"Table '{table_name}' has no accessible columns - skipping")
                    skipped_tables.append(table_name)
                    continue  # Skip this table instead of failing completely
                
                schemas[table_name] = columns
                logger.info(f"Discovered {len(columns)} columns for table '{table_name}'")
            
            cursor.close()
            
            # Ensure we have at least some tables with schemas
            if not schemas:
                if skipped_tables:
                    raise SchemaDiscoveryError(
                        f"No accessible tables found. Skipped tables: {skipped_tables}. "
                        f"Check table names, permissions, and database connection."
                    )
                else:
                    raise SchemaDiscoveryError(f"No accessible tables found among the requested tables: {table_names}")
            
            if skipped_tables:
                logger.warning(f"Skipped {len(skipped_tables)} inaccessible tables: {skipped_tables}")
            
            logger.info(f"Successfully discovered schemas for {len(schemas)} out of {len(table_names)} requested tables")
            return schemas
                
        except MySQLError as e:
            logger.error(f"Database error during schema discovery: {e}")
            raise SchemaDiscoveryError(f"Failed to discover table schemas: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def get_table_relationships(self, table_names: List[str]) -> List[Dict[str, Any]]:
        """
        Discover foreign key relationships between specified tables.
        Only includes relationships between tables that actually exist and are accessible.
        
        Args:
            table_names: List of table names to analyze
            
        Returns:
            List of relationship definitions
        """
        relationships = []
        
        # Filter table names to only include existing tables
        existing_tables = []
        if not table_names:
            logger.warning("No tables provided for relationship discovery")
            return relationships
        
        conn = None
        try:
            conn = self._create_connection()
            cursor = conn.cursor()
            
            # First, filter to only existing tables
            for table_name in table_names:
                if self._validate_table_exists(table_name, cursor):
                    existing_tables.append(table_name)
                else:
                    logger.warning(f"Table '{table_name}' does not exist - excluding from relationship discovery")
            
            if not existing_tables:
                logger.warning("No existing tables found for relationship discovery")
                return relationships
            
            # Query for foreign key relationships using INFORMATION_SCHEMA
            placeholders = ','.join(['%s'] * len(existing_tables))
            query = f"""
            SELECT 
                kcu.CONSTRAINT_NAME as FK_NAME,
                kcu.TABLE_NAME as PARENT_TABLE,
                kcu.COLUMN_NAME as PARENT_COLUMN,
                kcu.REFERENCED_TABLE_NAME as REFERENCED_TABLE,
                kcu.REFERENCED_COLUMN_NAME as REFERENCED_COLUMN
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            WHERE kcu.REFERENCED_TABLE_SCHEMA = %s
            AND kcu.TABLE_SCHEMA = %s
            AND (kcu.TABLE_NAME IN ({placeholders}) OR kcu.REFERENCED_TABLE_NAME IN ({placeholders}))
            AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            """
            
            params = [self.config.db_database, self.config.db_database] + existing_tables + existing_tables
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                # Only include relationships where both tables are in our existing tables list
                parent_table, referenced_table = row[1], row[3]
                if parent_table in existing_tables and referenced_table in existing_tables:
                    relationship = {
                        'fk_name': row[0],
                        'parent_table': parent_table,
                        'parent_column': row[2],
                        'referenced_table': referenced_table,
                        'referenced_column': row[4]
                    }
                    relationships.append(relationship)
            
            cursor.close()
            logger.info(f"Discovered {len(relationships)} foreign key relationships")
            return relationships
                
        except MySQLError as e:
            logger.error(f"Database error during relationship discovery: {e}")
            raise SchemaDiscoveryError(f"Failed to discover table relationships: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
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
        
        conn = None
        try:
            conn = self._create_connection()
            cursor = conn.cursor()
            
            # First, get sample from primary table
            logger.debug(f"Sampling {sample_size} rows from primary table: {primary_table}")
            
            primary_query = f"SELECT * FROM `{primary_table}` LIMIT %s"
            cursor.execute(primary_query, (sample_size,))
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch sample data
            primary_rows = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                # Convert any non-serializable types to strings
                row_dict = self._serialize_row(row_dict)
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
            
            cursor.close()
            return sample_data
                
        except MySQLError as e:
            logger.error(f"Database error during relational sampling: {e}")
            raise SchemaDiscoveryError(f"Failed to perform relational sampling: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
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
                placeholders = ','.join(['%s' for _ in fk_values])
                query = f"SELECT * FROM `{target_table}` WHERE `{referenced_column}` IN ({placeholders})"
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
                placeholders = ','.join(['%s' for _ in pk_values])
                query = f"SELECT * FROM `{target_table}` WHERE `{foreign_key_column}` IN ({placeholders})"
                cursor.execute(query, list(pk_values))
            
            # Process results
            columns = [desc[0] for desc in cursor.description]
            related_rows = []
            
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                # Convert any non-serializable types to strings
                row_dict = self._serialize_row(row_dict)
                related_rows.append(row_dict)
            
            return related_rows
            
        except Exception as e:
            logger.warning(f"Error getting related sample for {target_table}: {e}")
            return []
    
    def _get_basic_sample(self, cursor, table_name: str, sample_size: int) -> List[Dict[str, Any]]:
        """Get basic sample from table when no relationship exists."""
        try:
            query = f"SELECT * FROM `{table_name}` LIMIT %s"
            cursor.execute(query, (sample_size,))
            
            columns = [desc[0] for desc in cursor.description]
            rows = []
            
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                # Convert any non-serializable types to strings
                row_dict = self._serialize_row(row_dict)
                rows.append(row_dict)
            
            return rows
            
        except Exception as e:
            logger.warning(f"Error getting basic sample for {table_name}: {e}")
            return []
