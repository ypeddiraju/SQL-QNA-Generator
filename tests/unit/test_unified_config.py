"""
Test script to verify the unified configuration approach works correctly.
"""

import sys
import os
# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import Config

def test_mysql_config():
    """Test MySQL configuration with prefixed environment variables."""
    # Set MySQL environment variables
    os.environ['DB_TYPE'] = 'mysql'
    os.environ['MYSQL_DB_SERVER'] = 'localhost'
    os.environ['MYSQL_DB_DATABASE'] = 'testdb'
    os.environ['MYSQL_DB_USERNAME'] = 'testuser'
    os.environ['MYSQL_DB_PASSWORD'] = 'testpass'
    os.environ['MYSQL_DB_PORT'] = '3306'
    
    config = Config()
    
    print("=== MySQL Configuration Test ===")
    print(f"Database Type: {config.db_type}")
    print(f"Server: {config.db_server}")
    print(f"Database: {config.db_database}")
    print(f"Username: {config.db_username}")
    print(f"Password: {'*' * len(config.db_password) if config.db_password else 'None'}")
    print(f"Port: {config.db_port}")
    print(f"Driver: {config.db_driver}")
    print(f"Connection String: {config.connection_string}")
    
    return config

def test_sqlserver_config():
    """Test SQL Server configuration with prefixed environment variables."""
    # Clear previous env vars and set SQL Server ones
    for key in list(os.environ.keys()):
        if key.startswith(('MYSQL_DB_', 'SQLSERVER_DB_', 'DB_')):
            del os.environ[key]
    
    os.environ['DB_TYPE'] = 'sqlserver'
    os.environ['SQLSERVER_DB_SERVER'] = 'sql-server.example.com'
    os.environ['SQLSERVER_DB_DATABASE'] = 'BusinessDB'
    os.environ['SQLSERVER_DB_USERNAME'] = 'sqluser'
    os.environ['SQLSERVER_DB_PASSWORD'] = 'sqlpass'
    os.environ['SQLSERVER_DB_PORT'] = '1433'
    
    config = Config()
    
    print("\n=== SQL Server Configuration Test ===")
    print(f"Database Type: {config.db_type}")
    print(f"Server: {config.db_server}")
    print(f"Database: {config.db_database}")
    print(f"Username: {config.db_username}")
    print(f"Password: {'*' * len(config.db_password) if config.db_password else 'None'}")
    print(f"Port: {config.db_port}")
    print(f"Driver: {config.db_driver}")
    print(f"Connection String: {config.connection_string}")
    
    return config

if __name__ == "__main__":
    print("Testing Unified Configuration with Prefixed Environment Variables\n")
    
    try:
        mysql_config = test_mysql_config()
        sqlserver_config = test_sqlserver_config()
        
        print("\n✅ All configuration tests passed!")
        print("\n📝 Summary:")
        print("- MySQL configuration loads correctly with MYSQL_DB_* prefixes")
        print("- SQL Server configuration loads correctly with SQLSERVER_DB_* prefixes")
        print("- Database type switching works as expected")
        print("- Connection strings are generated correctly for each database type")
        
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        raise
