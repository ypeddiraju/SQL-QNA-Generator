#!/usr/bin/env python3
"""
Test API configuration loading to debug connection issues.
"""

import logging
import sys
import os
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_config():
    """Test how API loads configuration."""
    
    print("Testing API Configuration Loading")
    print("=" * 50)
    
    # Load environment (same as API does)
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    
    print(f"DB_TYPE from env: {os.getenv('DB_TYPE', 'NOT SET')}")
    print(f"MYSQL_DB_SERVER from env: {os.getenv('MYSQL_DB_SERVER', 'NOT SET')}")
    print(f"MYSQL_DB_DATABASE from env: {os.getenv('MYSQL_DB_DATABASE', 'NOT SET')}")
    
    # Test config loading (same as API)
    # Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import Config
    config = Config()
    
    print(f"\nLoaded Config:")
    print(f"  db_type: {config.db_type}")
    print(f"  db_server: {config.db_server}")
    print(f"  db_database: {config.db_database}")
    print(f"  db_port: {config.db_port}")
    print(f"  is_database_configured: {config.is_database_configured()}")
    
    # Test MySQL connection params
    if config.db_type == 'mysql':
        print(f"\nMySQL Connection Params:")
        params = config.mysql_connection_params
        for key, value in params.items():
            if key == 'password':
                print(f"  {key}: {'*' * len(str(value)) if value else 'NOT SET'}")
            else:
                print(f"  {key}: {value}")
    
    # Test database connector creation
    print(f"\nTesting Database Connector:")
    from src.database_connector import DatabaseConnector
    
    try:
        db_connector = DatabaseConnector(config)
        print(f"✅ Database connector created successfully")
        print(f"   Connector type: {type(db_connector).__name__}")
        
        # Test connection
        print(f"\nTesting connection...")
        result = db_connector.test_connection()
        print(f"Connection result: {result}")
        
        if result:
            print(f"\nTesting table discovery...")
            tables = db_connector.get_all_tables()
            print(f"Found {len(tables)} tables")
            if tables:
                print(f"First 5 tables: {tables[:5]}")
        
    except Exception as e:
        print(f"❌ Database connector failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_config()
