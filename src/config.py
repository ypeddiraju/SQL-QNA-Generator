"""
Configuration management for GenAI SQL Test Data Generator.
"""

import os
from typing import Optional


class Config:
    """Application configuration loaded from environment variables or direct parameters."""
    
    def __init__(self, 
                 # Database configuration
                 db_server: Optional[str] = None,
                 db_database: Optional[str] = None, 
                 db_username: Optional[str] = None,
                 db_password: Optional[str] = None,
                 db_driver: Optional[str] = None,
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
        
        # Database configuration (parameters override environment)
        self.db_server = db_server or self._get_env_var("DB_SERVER", required=False)
        self.db_database = db_database or self._get_env_var("DB_DATABASE", required=False)
        self.db_username = db_username or self._get_env_var("DB_USERNAME", required=False)
        self.db_password = db_password or self._get_env_var("DB_PASSWORD", required=False)
        self.db_driver = db_driver or os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
        
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
        self.db_port = os.getenv("DB_PORT", "1433")  # Default SQL Server port
    
    def _get_env_var(self, var_name: str, required: bool = True) -> str:
        """Get environment variable or raise error if required."""
        value = os.getenv(var_name)
        if required and not value:
            raise ValueError(f"Required environment variable {var_name} is not set")
        return value or ""
    
    @property
    def connection_string(self) -> str:
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
            "driver": self.db_driver
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
    
    def get_openai_config(self) -> dict:
        """Get OpenAI configuration info (without exposing API key)."""
        return {
            "model": self.openai_model,
            "api_key_configured": self.is_openai_configured(),
            "api_key_preview": f"{self.openai_api_key[:10]}..." if len(self.openai_api_key) > 10 else "Not configured"
        }
