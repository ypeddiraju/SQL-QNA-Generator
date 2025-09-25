"""
Configuration management for GenAI SQL Test Data Generator.
"""

import os
from typing import Optional, Dict, Any


class ConnectionManager:
    """Manages active database connections and their states."""
    
    def __init__(self):
        self._active_connections: Dict[str, Dict[str, Any]] = {}
        self._current_connection_id: Optional[str] = None
    
    def add_connection(self, connection_id: str, config: 'Config', connector: Any) -> None:
        """Add an active connection."""
        self._active_connections[connection_id] = {
            'config': config,
            'connector': connector,
            'created_at': os.getenv('TIMESTAMP', 'unknown'),
            'db_type': config.db_type,
            'server': config.db_server,
            'database': config.db_database
        }
        self._current_connection_id = connection_id
    
    def get_active_connection(self) -> Optional[Dict[str, Any]]:
        """Get the currently active connection."""
        if self._current_connection_id and self._current_connection_id in self._active_connections:
            return self._active_connections[self._current_connection_id]
        return None
    
    def get_active_config(self) -> Optional['Config']:
        """Get the config for the currently active connection."""
        connection = self.get_active_connection()
        return connection['config'] if connection else None
    
    def get_active_connector(self) -> Optional[Any]:
        """Get the connector for the currently active connection."""
        connection = self.get_active_connection()
        return connection['connector'] if connection else None
    
    def remove_connection(self, connection_id: str) -> bool:
        """Remove a connection."""
        if connection_id in self._active_connections:
            del self._active_connections[connection_id]
            if self._current_connection_id == connection_id:
                self._current_connection_id = None
            return True
        return False
    
    def clear_all_connections(self) -> None:
        """Clear all connections."""
        self._active_connections.clear()
        self._current_connection_id = None
    
    def list_connections(self) -> Dict[str, Dict[str, Any]]:
        """List all active connections."""
        return self._active_connections.copy()
    
    def has_active_connection(self) -> bool:
        """Check if there's an active connection."""
        return self.get_active_connection() is not None
    
    def get_connection_info(self) -> Optional[Dict[str, str]]:
        """Get info about the current active connection."""
        connection = self.get_active_connection()
        if connection:
            return {
                'id': self._current_connection_id,
                'db_type': connection['db_type'],
                'server': connection['server'],
                'database': connection['database'],
                'status': 'active'
            }
        return None


# Global connection manager instance
connection_manager = ConnectionManager()


class Config:
    """Application configuration loaded from environment variables or direct parameters."""
    
    def __init__(self, 
                 # Database configuration
                 db_server: Optional[str] = None,
                 db_database: Optional[str] = None, 
                 db_username: Optional[str] = None,
                 db_password: Optional[str] = None,
                 db_driver: Optional[str] = None,
                 db_type: Optional[str] = None,
                 # OpenAI configuration  
                 openai_api_key: Optional[str] = None,
                 openai_model: Optional[str] = None,
                 # Other configuration
                 output_file: Optional[str] = None,
                 sample_size: Optional[int] = None,
                 min_questions: Optional[int] = None,
                 target_join_percentage: Optional[int] = None,
                 difficulty_level: Optional[str] = None):
        """Initialize configuration from parameters or environment variables."""
        
        # Database type first to determine which credentials to use
        self.db_type = (db_type or os.getenv("DB_TYPE", "sqlserver")).lower().strip()
        
        # Database configuration (parameters override environment)
        # Use prefixed environment variables based on database type
        if self.db_type == "mysql":
            self.db_server = db_server or self._get_env_var("MYSQL_DB_SERVER", required=False) or self._get_env_var("DB_SERVER", required=False)
            self.db_database = db_database or self._get_env_var("MYSQL_DB_DATABASE", required=False) or self._get_env_var("DB_DATABASE", required=False)
            self.db_username = db_username or self._get_env_var("MYSQL_DB_USERNAME", required=False) or self._get_env_var("DB_USERNAME", required=False)
            self.db_password = db_password or self._get_env_var("MYSQL_DB_PASSWORD", required=False) or self._get_env_var("DB_PASSWORD", required=False)
            self.db_driver = db_driver or os.getenv("MYSQL_DB_DRIVER") or os.getenv("DB_DRIVER", "mysql+pymysql")
        else:
            # SQL Server (sqlserver or mssql)
            self.db_server = db_server or self._get_env_var("SQLSERVER_DB_SERVER", required=False) or self._get_env_var("DB_SERVER", required=False)
            self.db_database = db_database or self._get_env_var("SQLSERVER_DB_DATABASE", required=False) or self._get_env_var("DB_DATABASE", required=False)
            self.db_username = db_username or self._get_env_var("SQLSERVER_DB_USERNAME", required=False) or self._get_env_var("DB_USERNAME", required=False)
            self.db_password = db_password or self._get_env_var("SQLSERVER_DB_PASSWORD", required=False) or self._get_env_var("DB_PASSWORD", required=False)
            self.db_driver = db_driver or os.getenv("SQLSERVER_DB_DRIVER") or os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
        
        # OpenAI configuration (parameters override environment)
        self.openai_api_key = openai_api_key or self._get_env_var("OPENAI_API_KEY", required=False)
        self.openai_model = openai_model or os.getenv("OPENAI_MODEL", "gpt-4")
        
        # Other configuration (parameters override environment)
        self.output_file = output_file or os.getenv("OUTPUT_FILE", "qna_dataset.json")
        self.sample_size = sample_size or int(os.getenv("SAMPLE_SIZE", "10"))
        self.min_questions = min_questions or int(os.getenv("MIN_QUESTIONS", "25"))
        self.target_join_percentage = target_join_percentage or int(os.getenv("TARGET_JOIN_PERCENTAGE", "40"))
        self.difficulty_level = difficulty_level or os.getenv("DIFFICULTY_LEVEL", "mixed")
        self.max_tables = int(os.getenv("MAX_TABLES", "12"))  # Maximum tables for Q&A generation
        
        # Configuration that comes only from environment
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Database timeout configuration
        self.db_connection_timeout = int(os.getenv("DB_CONNECTION_TIMEOUT", "60"))
        self.db_command_timeout = int(os.getenv("DB_COMMAND_TIMEOUT", "120")) 
        self.db_login_timeout = int(os.getenv("DB_LOGIN_TIMEOUT", "60"))
        self.db_retry_count = int(os.getenv("DB_RETRY_COUNT", "3"))
        self.db_retry_interval = int(os.getenv("DB_RETRY_INTERVAL", "10"))
        
        # Set default port based on database type
        if self.db_type == "mysql":
            self.db_port = os.getenv("MYSQL_DB_PORT") or os.getenv("DB_PORT", "3306")  # Default MySQL port
        else:
            self.db_port = os.getenv("SQLSERVER_DB_PORT") or os.getenv("DB_PORT", "1433")  # Default SQL Server port
    
    def _get_env_var(self, var_name: str, required: bool = True) -> str:
        """Get environment variable or raise error if required."""
        value = os.getenv(var_name)
        if required and not value:
            raise ValueError(f"Required environment variable {var_name} is not set")
        return value or ""
    
    @property
    def connection_string(self) -> str:
        """Generate database connection string based on database type."""
        if self.db_type == "mysql":
            return self._mysql_connection_string()
        else:
            return self._sqlserver_connection_string()
    
    def _sqlserver_connection_string(self) -> str:
        """Generate SQL Server connection string with configurable timeouts."""
        return (
            f"DRIVER={{{self.db_driver}}};"
            f"SERVER={self.db_server},{self.db_port};"  # Include port explicitly
            f"DATABASE={self.db_database};"
            f"UID={self.db_username};"
            f"PWD={self.db_password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout={self.db_connection_timeout};"
            f"Command Timeout={self.db_command_timeout};"
            f"Login Timeout={self.db_login_timeout};"
            f"ConnectRetryCount={self.db_retry_count};"
            f"ConnectRetryInterval={self.db_retry_interval};"
            f"MultipleActiveResultSets=true;"  # Allow multiple active result sets
            f"ApplicationIntent=ReadWrite;"    # Specify application intent
        )
    
    def _mysql_connection_string(self) -> str:
        """Generate MySQL connection parameters dictionary."""
        # For MySQL, we'll return a connection info dict as a string 
        # This will be parsed by the MySQL connector
        return f"mysql://{self.db_username}:{self.db_password}@{self.db_server}:{self.db_port}/{self.db_database}"
    
    @property 
    def mysql_connection_params(self) -> dict:
        """Get MySQL connection parameters as dictionary."""
        return {
            'host': self.db_server,
            'port': int(self.db_port),
            'user': self.db_username,
            'password': self.db_password,
            'database': self.db_database,
            'charset': 'utf8mb4',
            'autocommit': True,
            'connect_timeout': max(30, self.db_connection_timeout),  # Ensure at least 30 seconds
            'read_timeout': max(300, self.db_command_timeout),       # Ensure at least 5 minutes for discovery
            'write_timeout': max(300, self.db_command_timeout),      # Ensure at least 5 minutes
            'ssl_disabled': True,  # Disable SSL to avoid SSL issues with cloud databases
            'use_unicode': True,
            'sql_mode': 'TRADITIONAL',
            # Connection keep-alive and timeout settings
            'init_command': 'SET SESSION wait_timeout=3600, interactive_timeout=3600, net_read_timeout=600',
            'defer_connect': False,
            'local_infile': False,
        }
        
    @property
    def tcp_connection_string(self) -> str:
        """Alternative connection string using TCP/IP explicitly."""
        return (
            f"DRIVER={{{self.db_driver}}};"
            f"SERVER=tcp:{self.db_server},{self.db_port};"  # Force TCP protocol
            f"DATABASE={self.db_database};"
            f"UID={self.db_username};"
            f"PWD={self.db_password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout={self.db_connection_timeout};"
            f"Login Timeout={self.db_login_timeout};"
        )
    
    def get_database_config(self) -> dict:
        """Get current database configuration as dictionary."""
        return {
            "server": self.db_server,
            "database": self.db_database,
            "username": self.db_username,
            "password": "***" if self.db_password else "",  # Mask password for security
            "driver": self.db_driver,
            "type": self.db_type,
            "port": self.db_port
        }
    
    def is_database_configured(self) -> bool:
        """Check if database configuration is complete."""
        return all([self.db_server, self.db_database, self.db_username, self.db_password])
    
    def is_openai_configured(self) -> bool:
        """Check if OpenAI configuration is complete."""
        return bool(self.openai_api_key)
    
    def update_database_config(self, config_dict: dict) -> None:
        """Update database configuration from dictionary."""
        if "server" in config_dict and config_dict["server"]:
            self.db_server = config_dict["server"]
        if "database" in config_dict and config_dict["database"]:
            self.db_database = config_dict["database"] 
        if "username" in config_dict and config_dict["username"]:
            self.db_username = config_dict["username"]
        if "password" in config_dict and config_dict["password"] and config_dict["password"] != "***":
            self.db_password = config_dict["password"]
        if "driver" in config_dict and config_dict["driver"]:
            self.db_driver = config_dict["driver"]
        if "type" in config_dict and config_dict["type"]:
            self.db_type = config_dict["type"].lower()
        if "port" in config_dict and config_dict["port"]:
            self.db_port = str(config_dict["port"])
    
    def get_openai_config(self) -> dict:
        """Get OpenAI configuration info (without exposing API key)."""
        return {
            "model": self.openai_model,
            "api_key_configured": self.is_openai_configured(),
            "api_key_preview": f"{self.openai_api_key[:10]}..." if len(self.openai_api_key) > 10 else "Not configured"
        }
    
    def start_connection(self) -> tuple[bool, str]:
        """Start a database connection and register it with connection manager."""
        try:
            from src.database_connector import DatabaseConnector
            
            # Test the connection first
            db_connector = DatabaseConnector(self)
            if not db_connector.test_connection():
                return False, "Connection test failed"
            
            # Generate connection ID
            import time
            connection_id = f"{self.db_type}_{int(time.time())}"
            
            # Register with connection manager
            connection_manager.add_connection(connection_id, self, db_connector)
            
            return True, f"Connection started successfully: {connection_id}"
            
        except Exception as e:
            return False, f"Failed to start connection: {str(e)}"
    
    def stop_active_connection(self) -> tuple[bool, str]:
        """Stop the currently active connection."""
        if not connection_manager.has_active_connection():
            return False, "No active connection to stop"
        
        connection_info = connection_manager.get_connection_info()
        if connection_info:
            connection_manager.remove_connection(connection_info['id'])
            return True, f"Connection {connection_info['id']} stopped successfully"
        
        return False, "Failed to stop connection"
    
    @staticmethod
    def get_active_connection_info() -> Optional[Dict[str, str]]:
        """Get information about the currently active connection."""
        return connection_manager.get_connection_info()
    
    @staticmethod
    def has_active_connection() -> bool:
        """Check if there's an active database connection."""
        return connection_manager.has_active_connection()
    
    @staticmethod
    def get_active_connector():
        """Get the active database connector."""
        return connection_manager.get_active_connector()
    
    @staticmethod
    def get_active_config():
        """Get the active database configuration."""
        return connection_manager.get_active_config()
