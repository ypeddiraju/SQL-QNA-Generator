#!/usr/bin/env python3
"""
Simple MySQL connection test to isolate timeout issues.
"""

import logging
import pymysql
from dotenv import load_dotenv
from src.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_connection():
    """Test direct PyMySQL connection."""
    load_dotenv()
    
    config = Config()
    config.db_type = 'mysql'
    
    logger.info("Testing direct PyMySQL connection...")
    
    try:
        # Simple connection parameters
        conn_params = {
            'host': config.db_server,
            'port': int(config.db_port),
            'user': config.db_username,
            'password': config.db_password,
            'database': config.db_database,
            'connect_timeout': 10,
            'read_timeout': 30,
            'write_timeout': 30,
        }
        
        logger.info(f"Connecting to {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
        
        # Test basic connection
        conn = pymysql.connect(**conn_params)
        logger.info("✅ Connection successful!")
        
        # Test simple query
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        logger.info(f"✅ Simple query result: {result}")
        
        # Test table discovery query
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            AND TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME
            LIMIT 5
        """, (config.db_database,))
        
        tables = cursor.fetchall()
        logger.info(f"✅ Found {len(tables)} tables (showing first 5)")
        for table in tables:
            logger.info(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        logger.info("✅ All tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False
    
    return True

if __name__ == '__main__':
    test_direct_connection()
