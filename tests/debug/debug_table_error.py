#!/usr/bin/env python3
"""
Debug the exact source of the table error.
"""

import logging
import sys
import os
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_table_error():
    """Debug where the table error is coming from."""
    
    print("Debugging Table Error Source")
    print("=" * 50)
    
    # Load environment
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    
    print(f"DB_TYPE from .env: {os.getenv('DB_TYPE')}")
    
    # Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import Config
    config = Config()
    
    print(f"Config db_type: '{config.db_type}'")
    print(f"Config server: {config.db_server}")
    print(f"Config database: {config.db_database}")
    
    from src.database_connector import DatabaseConnector
    db_connector = DatabaseConnector(config)
    
    print(f"Connector type: {type(db_connector)}")
    print(f"Internal connector type: {type(db_connector._connector)}")
    
    # Test with the specific table that's failing
    problem_tables = ['alerting_rules']
    
    print(f"\nTesting schema discovery for: {problem_tables}")
    
    try:
        schemas = db_connector.get_table_schemas(problem_tables)
        print(f"Success: Got schemas for {len(schemas)} tables")
        print(f"Schemas: {list(schemas.keys())}")
    except Exception as e:
        print(f"Error type: {type(e)}")
        print(f"Error message: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_table_error()
