#!/usr/bin/env python3
"""
Quick MySQL connection test using our configuration
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.config import Config
from src.database_mysql import MySQLConnector

def test_mysql_connection():
    """Test MySQL connection using our configuration system"""
    try:
        # Initialize config with MySQL type
        config = Config(db_type='mysql')
        
        print("MySQL Connection Test with Updated Configuration")
        print("=" * 50)
        print(f"DB Type: {config.db_type}")
        print(f"Host: {config.db_server}")
        print(f"Port: {config.db_port}")
        print(f"Database: {config.db_database}")
        print(f"User: {config.db_username}")
        print(f"Connection Timeout: {config.db_connection_timeout}")
        
        # Debug environment variables
        import os
        print("\nEnvironment variables:")
        print(f"MYSQL_DB_SERVER: {os.getenv('MYSQL_DB_SERVER')}")
        print(f"MYSQL_DB_DATABASE: {os.getenv('MYSQL_DB_DATABASE')}")
        print(f"MYSQL_DB_USERNAME: {os.getenv('MYSQL_DB_USERNAME')}")
        print(f"DB_TYPE: {os.getenv('DB_TYPE')}")
        print("=" * 50)
        
        # Create MySQL connector
        mysql_connector = MySQLConnector(config)
        
        print("Testing connection...")
        if mysql_connector.test_connection():
            print("✅ MySQL connection successful!")
            
            # Try to get table list
            print("\nTesting table discovery...")
            tables = mysql_connector.get_all_tables()
            print(f"Found {len(tables)} tables: {tables[:5]}...")  # Show first 5 tables
            
        else:
            print("❌ MySQL connection failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mysql_connection()
