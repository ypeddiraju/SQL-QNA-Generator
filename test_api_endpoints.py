#!/usr/bin/env python3
"""
Test the actual API endpoint to see if it's using updated code.
"""

import requests
import json
import os
from dotenv import load_dotenv

def test_api_discovery():
    """Test the actual API discovery endpoint."""
    
    print("Testing API Discovery Endpoint")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    api_base = "http://localhost:8000"
    
    # Test API discovery endpoint
    discovery_payload = {
        "db_type": "mysql",
        "exclude_tables": ""
    }
    
    try:
        print("Making API request to /api/database/discover...")
        response = requests.post(
            f"{api_base}/api/database/discover",
            json=discovery_payload,
            timeout=60
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Discovery successful!")
            print(f"  Tables found: {len(data.get('tables', []))}")
            print(f"  Message: {data.get('message', 'No message')}")
            
            # Check if alerting_rules is in the results
            tables = data.get('tables', [])
            alerting_rules_found = any(t.get('name') == 'alerting_rules' for t in tables)
            print(f"  alerting_rules found: {alerting_rules_found}")
            
        else:
            print(f"❌ Discovery failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error text: {response.text}")
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server")
        print("   Make sure the API server is running: python api/main.py")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_api_generation():
    """Test the actual API generation endpoint."""
    
    print("\nTesting API Generation Endpoint")
    print("=" * 50)
    
    api_base = "http://localhost:8000"
    
    # Test with just a few tables including alerting_rules
    generation_payload = {
        "tables": ["alerting_rules", "users"],
        "questions_per_table": 2,
        "difficulty_level": "easy",
        "max_tables": 5,
        "db_type": "mysql"
    }
    
    try:
        print("Making API request to /api/generate/dataset...")
        response = requests.post(
            f"{api_base}/api/generate/dataset",
            json=generation_payload,
            timeout=120
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Generation successful!")
            print(f"  Questions generated: {len(data.get('dataset', []))}")
            print(f"  Message: {data.get('message', 'No message')}")
            
        else:
            print(f"❌ Generation failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
                
                # Check if it's still the old error
                error_detail = error_data.get('detail', '')
                if 'alerting_rules' in error_detail and 'not found or has no columns' in error_detail:
                    print("🔍 This is the old error - API server needs restart!")
                    
            except:
                print(f"Error text: {response.text}")
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server")
        print("   Make sure the API server is running: python api/main.py")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing if API server is using updated code...")
    
    discovery_success = test_api_discovery()
    generation_success = test_api_generation()
    
    if not discovery_success and not generation_success:
        print("\n💡 Recommendation: Restart the API server to load updated code")
        print("   1. Stop the current API server (Ctrl+C)")
        print("   2. Restart: python api/main.py")
    elif discovery_success and not generation_success:
        print("\n🔍 Discovery works but generation fails - investigating...")
    elif discovery_success and generation_success:
        print("\n🎉 All tests passed! The issue is resolved.")
