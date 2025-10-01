#!/usr/bin/env python3
"""
Simple test to check if discover_database.py works with MySQL.
"""

import os
import subprocess
import sys
from dotenv import load_dotenv

def main():
    # Load environment and set MySQL
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    
    # Set environment for MySQL
    env = os.environ.copy()
    env['DB_TYPE'] = 'mysql'
    
    print("Testing discover_database.py with MySQL...")
    print("=" * 50)
    
    try:
        # Run discovery with limited tables
        cmd = [
            sys.executable, 
            "discover_database.py", 
            "--analyze-all", 
            "--max-tables", "3",
            "--log-level", "INFO"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        print("-" * 50)
        
        result = subprocess.run(
            cmd, 
            env=env, 
            capture_output=True, 
            text=True, 
            timeout=300  # 5 minute timeout
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ Discovery completed successfully!")
        else:
            print("❌ Discovery failed!")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Discovery timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running discovery: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
