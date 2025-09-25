#!/usr/bin/env python3
"""
Test improved table schema error handling.
"""

import logging
import os
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_schema_error_handling():
    """Test how the improved schema discovery handles missing/inaccessible tables."""
    
    print("Testing Schema Error Handling")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    os.environ['DB_TYPE'] = 'mysql'
    
    from src.config import Config
    from src.database_connector import DatabaseConnector
    
    try:
        # Initialize
        config = Config()
        db_connector = DatabaseConnector(config)
        
        # Test with a mix of existing and non-existing tables
        test_tables = [
            'alerting_rules',        # This exists
            'users',                 # This exists  
            'nonexistent_table_1',   # This doesn't exist
            'fake_table_xyz',        # This doesn't exist
            'business_metrics_cache' # This exists
        ]
        
        print(f"Testing schema discovery with mixed table list: {test_tables}")
        
        # Test connection first
        if not db_connector.test_connection():
            print("❌ Connection failed")
            return False
        
        print("✅ Connection successful")
        
        # Test schema discovery with error handling
        print(f"\nTesting schema discovery...")
        schemas = db_connector.get_table_schemas(test_tables)
        
        print(f"✅ Schema discovery completed")
        print(f"  Requested {len(test_tables)} tables")
        print(f"  Got schemas for {len(schemas)} tables")
        print(f"  Accessible tables: {list(schemas.keys())}")
        
        # Test relationships discovery
        print(f"\nTesting relationship discovery...")
        relationships = db_connector.get_table_relationships(list(schemas.keys()))
        
        print(f"✅ Relationship discovery completed")
        print(f"  Found {len(relationships)} relationships")
        
        # Test with completely non-existent tables
        print(f"\nTesting with completely non-existent tables...")
        try:
            fake_schemas = db_connector.get_table_schemas(['fake1', 'fake2', 'fake3'])
            print(f"❌ Expected error but got schemas: {fake_schemas}")
        except Exception as e:
            print(f"✅ Correctly handled non-existent tables: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_schema_error_handling()
    exit(0 if success else 1)
