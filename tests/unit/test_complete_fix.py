#!/usr/bin/env python3

import sys
import os
# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import Config
from src.database_connector import DatabaseConnector
from dotenv import load_dotenv

# Load environment from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
config = Config()

# Test with the wrapper class (like the API does)
db = DatabaseConnector(config)

try:
    if db.test_connection():
        print('✓ Connected successfully')
        
        # Test table name resolution - this is the key fix
        unqualified_names = ['CurrencyExchange', 'Customer', 'Orders']
        print(f'\nTesting table name resolution with: {unqualified_names}')
        
        resolved_names = db.resolve_table_names(unqualified_names)
        print(f'Resolved to: {resolved_names}')
        
        # Test the exact scenario that was failing in the API
        print(f'\nTesting relational sampling with resolved names...')
        
        # Get schemas - should work with resolved names
        schemas = db.get_table_schemas(resolved_names)
        print(f'✓ Retrieved schemas for {len(schemas)} tables')
        
        # Get relationships - should work with resolved names
        relationships = db.get_table_relationships(resolved_names)
        print(f'✓ Found {len(relationships)} relationships')
        
        # Test relational sampling - this was failing before
        primary_table = resolved_names[0]
        print(f'Using primary table: {primary_table}')
        
        sample_data = db.get_relational_sample(primary_table, resolved_names, 2)
        print(f'✓ Successfully collected sample data from {len(sample_data)} tables:')
        for table_name, data in sample_data.items():
            print(f'  - {table_name}: {len(data)} rows')
        
        print('\n🎉 Complete fix is working! Unqualified table names are now properly resolved!')
    else:
        print('✗ Connection failed')
        
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
