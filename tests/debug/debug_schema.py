#!/usr/bin/env python3

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import Config
from src.database_factory import DatabaseConnectorFactory
import sys
import os
from dotenv import load_dotenv
import pyodbc

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
config = Config()
db = DatabaseConnectorFactory.create_connector(config)

try:
    if db.test_connection():
        print('Connected successfully')
        
        # Check what schema the tables are in
        with db._create_connection() as conn:
            cursor = conn.cursor()
            
            # Query to see tables with their schema
            query = """
            SELECT 
                TABLE_SCHEMA,
                TABLE_NAME,
                TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            AND TABLE_SCHEMA != 'sys'
            AND TABLE_NAME NOT LIKE 'sys%'
            AND TABLE_NAME NOT LIKE 'MSreplication%'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            
            cursor.execute(query)
            print("\nTables with their schemas:")
            for row in cursor.fetchall():
                print(f"  {row.TABLE_SCHEMA}.{row.TABLE_NAME} ({row.TABLE_TYPE})")
            
            # Try to query CurrencyExchange with different schema qualifications
            test_queries = [
                "SELECT TOP 1 * FROM CurrencyExchange",
                "SELECT TOP 1 * FROM [CurrencyExchange]", 
                "SELECT TOP 1 * FROM dbo.CurrencyExchange",
                "SELECT TOP 1 * FROM [dbo].[CurrencyExchange]"
            ]
            
            print("\nTesting different table name formats:")
            for query in test_queries:
                try:
                    cursor.execute(query)
                    print(f"  ✓ {query} - WORKS")
                    cursor.fetchall()  # consume results
                    break
                except Exception as e:
                    print(f"  ✗ {query} - Failed: {e}")
                    
    else:
        print('Connection failed')
        
except Exception as e:
    print(f'Error: {e}')
