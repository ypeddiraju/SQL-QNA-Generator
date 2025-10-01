#!/usr/bin/env python3

import sys
import os
"""
Debug script to test the API request and see validation errors.
"""

import requests
import json

# Test payload similar to what JavaScript would send
test_payload = {
    "tables": [],  # Empty for auto-discovery
    "questions_per_table": 10,
    "include_joins": True,
    "difficulty_level": "mixed",
    "output_file": None
}

print("Testing API request with payload:")
print(json.dumps(test_payload, indent=2))
print("-" * 50)

try:
    response = requests.post(
        'http://localhost:8000/api/generate/dataset',
        json=test_payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Content: {response.text}")
    
    if response.status_code == 422:
        print("\nValidation Error Details:")
        try:
            error_data = response.json()
            print(json.dumps(error_data, indent=2))
        except:
            print("Could not parse error response as JSON")
            
except Exception as e:
    print(f"Request failed: {e}")
