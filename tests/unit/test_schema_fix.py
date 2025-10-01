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
        
        # Test getting tables with schema qualification
        tables = db.get_all_tables()
        print(f'Found {len(tables)} tables:')
        for table in tables[:3]:  # Show first 3
            print(f'  - {table}')
        
        # Test relational sampling with schema-qualified names
        test_tables = tables[:3]  # Use first 3 tables
        print(f'\nTesting relational sampling with schema-qualified tables: {test_tables}')
        
        # Get schemas first
        schemas = db.get_table_schemas(test_tables)
        print(f'✓ Retrieved schemas for {len(schemas)} tables')
        
        # Get relationships
        relationships = db.get_table_relationships(test_tables)
        print(f'✓ Found {len(relationships)} relationships')
        
        # Try relational sampling
        primary_table = test_tables[0]
        sample_data = db.get_relational_sample(primary_table, test_tables, 3)
        print(f'✓ Successfully collected sample data from {len(sample_data)} tables:')
        for table_name, data in sample_data.items():
            print(f'  - {table_name}: {len(data)} rows')
            if data:
                print(f'    First row keys: {list(data[0].keys())}')
        
        print('\n🎉 Schema-qualified relational sampling is working correctly!')
    else:
        print('✗ Connection failed')
        
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
