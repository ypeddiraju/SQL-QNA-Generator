#!/usr/bin/env python3

import sys
import os
# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import Config
from src.database_connector import DatabaseConnector  # Using the wrapper
from dotenv import load_dotenv

# Load environment from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
config = Config()

print(f"Config DB Type: {config.db_type}")

# Test with the wrapper class (like the API does)
db = DatabaseConnector(config)

print(f"Connector type: {type(db._connector)}")
print(f"Connector class: {db._connector.__class__.__name__}")

try:
    if db.test_connection():
        print('✓ Connected successfully')
        
        # Test getting tables - this should return schema-qualified names
        tables = db.get_all_tables()
        print(f'Found {len(tables)} tables:')
        for table in tables[:3]:  # Show first 3
            print(f'  - {table}')
        
        # Test the exact scenario that's failing
        if len(tables) >= 3:
            test_tables = tables[:3]
            print(f'\nTesting relational sampling with: {test_tables}')
            
            primary_table = test_tables[0]
            print(f'Primary table: {primary_table}')
            
            sample_data = db.get_relational_sample(primary_table, test_tables, 2)
            print(f'✓ Successfully collected sample data from {len(sample_data)} tables')
            
        print('\n🎉 DatabaseConnector wrapper is working with schema-qualified names!')
    else:
        print('✗ Connection failed')
        
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
