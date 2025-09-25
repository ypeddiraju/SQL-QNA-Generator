"""
Test script to verify dataset generation with MySQL database.
"""

import requests
import json
import sys

def test_dataset_generation():
    """Test the dataset generation endpoint with MySQL database."""
    
    # API endpoint
    base_url = "http://localhost:8000"
    
    # Test health first
    try:
        health_response = requests.get(f"{base_url}/health")
        print(f"✅ API Health: {health_response.json()}")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False
    
    # MySQL configuration (from the working test)
    db_config = {
        "server": "35.225.136.237",
        "database": "recruitment",
        "username": "root",
        "password": "password"
    }
    
    # Simple OpenAI config (will fail if no key, but should get past database analysis)
    openai_config = {
        "api_key": "test-key",
        "model": "gpt-3.5-turbo"
    }
    
    # Generation request
    request_data = {
        "database_config": db_config,
        "openai_config": openai_config,
        "generation_config": {
            "sample_size": 5,
            "min_questions": 3
        },
        "discover_all": True
    }
    
    print("🔍 Testing dataset generation...")
    print(f"Database: {db_config['server']}/{db_config['database']}")
    
    try:
        response = requests.post(f"{base_url}/api/generate/dataset", json=request_data)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result}")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_dataset_generation()
    sys.exit(0 if success else 1)
