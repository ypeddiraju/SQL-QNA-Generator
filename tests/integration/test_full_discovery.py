#!/usr/bin/env python3
"""
Test full database discovery functionality for MySQL.
"""

import logging
import sys
import os
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Load environment
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    os.environ['DB_TYPE'] = 'mysql'
    
    # Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import Config
    from src.database_connector import DatabaseConnector
    
    try:
        # Initialize
        config = Config()
        logger.info(f"Using database type: {config.db_type}")
        
        db_connector = DatabaseConnector(config)
        logger.info("Testing full discovery process...")
        
        # Test connection
        logger.info("1. Testing connection...")
        if not db_connector.test_connection():
            logger.error("Connection test failed")
            return False
        logger.info("✅ Connection successful")
        
        # Get all tables
        logger.info("2. Getting all tables...")
        all_tables = db_connector.get_all_tables()
        logger.info(f"✅ Found {len(all_tables)} tables")
        
        # Get a subset for testing (first 5 tables)
        test_tables = all_tables[:5]
        logger.info(f"3. Testing with {len(test_tables)} tables: {test_tables}")
        
        # Get table schemas
        logger.info("4. Getting table schemas...")
        schemas = db_connector.get_table_schemas(test_tables)
        logger.info(f"✅ Got schemas for {len(schemas)} tables")
        for table, columns in schemas.items():
            logger.info(f"   {table}: {len(columns)} columns")
        
        # Get relationships
        logger.info("5. Getting table relationships...")
        relationships = db_connector.get_table_relationships(test_tables)
        logger.info(f"✅ Found {len(relationships)} relationships")
        for rel in relationships:
            logger.info(f"   {rel['parent_table']}.{rel['parent_column']} → {rel['referenced_table']}.{rel['referenced_column']}")
        
        # Get sample data
        logger.info("6. Getting sample data...")
        if test_tables:
            sample_data = db_connector.get_relational_sample(test_tables[0], test_tables, 3)
            total_rows = sum(len(rows) for rows in sample_data.values())
            logger.info(f"✅ Got sample data: {total_rows} total rows across {len(sample_data)} tables")
            for table, rows in sample_data.items():
                logger.info(f"   {table}: {len(rows)} rows")
        
        logger.info("🎉 Full discovery test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Discovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
