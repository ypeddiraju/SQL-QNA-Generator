#!/usr/bin/env python3
"""
Test MySQL connection with timeout debugging
"""
import sys
import os
import logging
from dotenv import load_dotenv

# Set up logging first
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mysql_connection():
    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    
    # Force MySQL type
    os.environ['DB_TYPE'] = 'mysql'
    
    # Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import Config
    from src.database_connector import DatabaseConnector
    
    config = Config()
    logger.info(f"Using database type: {config.db_type}")
    logger.info(f"Connection params: {config.mysql_connection_params}")
    
    db_connector = DatabaseConnector(config)
    
    # Test basic connection
    logger.info("Testing basic connection...")
    try:
        result = db_connector.test_connection()
        logger.info(f"Connection test result: {result}")
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False
    
    # Test discovery
    logger.info("Testing table discovery...")
    try:
        tables = db_connector.get_all_tables()
        logger.info(f"Found {len(tables)} tables: {tables}")
        return True
    except Exception as e:
        logger.error(f"Table discovery failed: {e}")
        return False

if __name__ == "__main__":
    test_mysql_connection()
