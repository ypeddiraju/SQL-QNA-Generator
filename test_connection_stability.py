#!/usr/bin/env python3
"""
Test MySQL connection stability during discovery operations.
"""

import logging
import os
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Load environment
    load_dotenv()
    os.environ['DB_TYPE'] = 'mysql'
    
    from src.config import Config
    from src.database_connector import DatabaseConnector
    
    try:
        # Initialize
        config = Config()
        logger.info(f"Using database type: {config.db_type}")
        logger.info(f"Connection params: {config.mysql_connection_params}")
        
        db_connector = DatabaseConnector(config)
        logger.info("Testing connection stability during discovery...")
        
        # Test 1: Basic connection
        logger.info("1. Testing basic connection...")
        if not db_connector.test_connection():
            logger.error("Connection test failed")
            return False
        logger.info("✅ Connection successful")
        
        # Test 2: Table discovery (the problematic operation)
        logger.info("2. Testing table discovery...")
        tables = db_connector.get_all_tables()
        logger.info(f"✅ Found {len(tables)} tables")
        
        # Test 3: Multiple discovery attempts to test connection stability
        for i in range(3):
            logger.info(f"3.{i+1}. Testing repeated discovery (attempt {i+1})...")
            tables_again = db_connector.get_all_tables()
            if len(tables_again) == len(tables):
                logger.info(f"✅ Consistent results: {len(tables_again)} tables")
            else:
                logger.warning(f"⚠️  Inconsistent results: {len(tables_again)} vs {len(tables)} tables")
        
        # Test 4: Schema discovery on subset
        test_tables = tables[:3]  # Test with first 3 tables
        logger.info(f"4. Testing schema discovery on {len(test_tables)} tables...")
        schemas = db_connector.get_table_schemas(test_tables)
        logger.info(f"✅ Got schemas for {len(schemas)} tables")
        
        logger.info("🎉 All connection stability tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Connection stability test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
