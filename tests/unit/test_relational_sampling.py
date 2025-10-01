#!/usr/bin/env python3

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import Config
from src.database_factory import DatabaseConnectorFactory
import sys
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
config = Config()
db = DatabaseConnectorFactory.create_connector(config)

try:
    if db.test_connection():
        print('✓ Connected successfully')
        
        # Test relational sampling with CurrencyExchange table
        tables = ['CurrencyExchange', 'Customer', 'Orders']
        print(f'\nTesting relational sampling with tables: {tables}')
        
        # Get schemas first
        schemas = db.get_table_schemas(tables)
        print(f'✓ Retrieved schemas for {len(schemas)} tables')
        
        # Get relationships
        relationships = db.get_table_relationships(tables)
        print(f'✓ Found {len(relationships)} relationships')
        
        # Try relational sampling
        sample_data = db.get_relational_sample('CurrencyExchange', tables, 5)
        print(f'✓ Successfully collected sample data from {len(sample_data)} tables:')
        for table_name, data in sample_data.items():
            print(f'  - {table_name}: {len(data)} rows')
        
        print('\n🎉 Relational sampling is working correctly!')
    else:
        print('✗ Connection failed')
        
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
