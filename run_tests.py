#!/usr/bin/env python3
"""
Test runner for GenAI SQL Test Data Generator.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py unit              # Run only unit tests
    python run_tests.py integration       # Run only integration tests  
    python run_tests.py debug             # Run debug utilities
    python run_tests.py -f test_name      # Run specific test file
"""

import sys
import os
import subprocess
import glob
import argparse

def run_test_file(file_path):
    """Run a single test file."""
    print(f"\n{'='*60}")
    print(f"Running: {file_path}")
    print('='*60)
    
    try:
        result = subprocess.run([sys.executable, file_path], 
                              capture_output=False, 
                              cwd=os.getcwd())
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {file_path}: {e}")
        return False

def run_tests_in_directory(test_dir, pattern="*.py"):
    """Run all test files in a directory."""
    if not os.path.exists(test_dir):
        print(f"Directory not found: {test_dir}")
        return []
    
    test_files = glob.glob(os.path.join(test_dir, pattern))
    # Exclude __init__.py files
    test_files = [f for f in test_files if not f.endswith('__init__.py')]
    
    results = []
    for test_file in sorted(test_files):
        success = run_test_file(test_file)
        results.append((test_file, success))
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Run tests for GenAI SQL Test Data Generator')
    parser.add_argument('suite', nargs='?', choices=['unit', 'integration', 'debug', 'all'], 
                        default='all', help='Test suite to run')
    parser.add_argument('-f', '--file', help='Run specific test file')
    
    args = parser.parse_args()
    
    if args.file:
        # Run specific file
        test_file = args.file
        if not test_file.endswith('.py'):
            test_file += '.py'
        
        # Look for the file in test directories
        search_paths = [
            test_file,
            f"tests/unit/{test_file}",
            f"tests/integration/{test_file}", 
            f"tests/debug/{test_file}"
        ]
        
        found = False
        for path in search_paths:
            if os.path.exists(path):
                run_test_file(path)
                found = True
                break
        
        if not found:
            print(f"Test file not found: {test_file}")
            return 1
    
    else:
        # Run test suites
        all_results = []
        
        if args.suite in ['all', 'unit']:
            print("\n" + "="*60)
            print("RUNNING UNIT TESTS")
            print("="*60)
            results = run_tests_in_directory('tests/unit')
            all_results.extend(results)
        
        if args.suite in ['all', 'integration']:
            print("\n" + "="*60) 
            print("RUNNING INTEGRATION TESTS")
            print("="*60)
            results = run_tests_in_directory('tests/integration')
            all_results.extend(results)
        
        if args.suite in ['all', 'debug']:
            print("\n" + "="*60)
            print("RUNNING DEBUG UTILITIES")  
            print("="*60)
            results = run_tests_in_directory('tests/debug')
            all_results.extend(results)
        
        # Summary
        if all_results:
            print("\n" + "="*60)
            print("TEST SUMMARY")
            print("="*60)
            
            passed = sum(1 for _, success in all_results if success)
            total = len(all_results)
            
            for test_file, success in all_results:
                status = "✓ PASS" if success else "✗ FAIL"
                print(f"{status} {os.path.basename(test_file)}")
            
            print(f"\nTotal: {passed}/{total} tests passed")
            
            return 0 if passed == total else 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
