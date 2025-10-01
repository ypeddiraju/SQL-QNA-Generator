#!/usr/bin/env python3

import sys
import os
# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import Config
from src.database_factory import DatabaseConnectorFactory
from dotenv import load_dotenv

# Load environment from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
config = Config()
db = DatabaseConnectorFactory.create_connector(config)

try:
    if db.test_connection():
        print('Connected successfully')
        tables = db.get_all_tables()
        print(f'Found {len(tables)} tables:')
        for table in sorted(tables):
            print(f'  - {table}')
        
        # Check if CurrencyExchange exists
        if 'CurrencyExchange' in tables:
            print('\n✓ CurrencyExchange table exists')
        else:
            print('\n✗ CurrencyExchange table NOT found')
            print('Looking for similar names:')
            for table in tables:
                if 'currency' in table.lower() or 'exchange' in table.lower():
                    print(f'  - {table}')
    else:
        print('Connection failed')
        
except Exception as e:
    print(f'Error: {e}')
