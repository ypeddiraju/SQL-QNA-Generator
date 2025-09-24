#!/usr/bin/env python3
"""
Example usage script for GenAI SQL Test Data Generator.

This script demonstrates how to use the QNA generator with sample data
and provides examples of different use cases.
"""

import os
import json
from pathlib import Path

def print_banner():
    """Print application banner."""
    print("=" * 60)
    print("GenAI SQL Test Data Generator - Example Usage")
    print("=" * 60)

def check_configuration():
    """Check if configuration is properly set up."""
    print("\n[1] Checking configuration...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found. Please copy .env.template to .env and configure it.")
        return False
    
    required_vars = [
        'OPENAI_API_KEY',
        'DB_SERVER', 
        'DB_DATABASE',
        'DB_USERNAME',
        'DB_PASSWORD'
    ]
    
    from dotenv import load_dotenv
    load_dotenv()
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == f'your_{var.lower()}_here':
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Please configure these environment variables in .env:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ Configuration looks good!")
    return True

def show_example_commands():
    """Show example commands."""
    print("\n[2] Example Commands:")
    print("-" * 40)
    
    examples = [
        {
            "description": "Basic usage with two tables",
            "command": "python generate_dataset.py --tables \"Employees,Departments\""
        },
        {
            "description": "Multiple tables with custom output file", 
            "command": "python generate_dataset.py --tables \"Employees,Departments,Projects\" --output \"custom_dataset.json\""
        },
        {
            "description": "Larger sample size with debug logging",
            "command": "python generate_dataset.py --tables \"Orders,Customers,Products\" --sample-size 20 --log-level DEBUG"
        },
        {
            "description": "E-commerce example",
            "command": "python generate_dataset.py --tables \"Users,Orders,OrderItems,Products\""
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}:")
        print(f"   {example['command']}")

def show_sample_output():
    """Show sample output format."""
    print("\n[3] Expected Output Format:")
    print("-" * 40)
    
    sample_output = [
        {
            "question": "How many employees work in the Engineering department?",
            "expected_answer": "3"
        },
        {
            "question": "What is the average salary of all employees?",
            "expected_answer": "65000"
        },
        {
            "question": "List all employees who work in departments located in New York.",
            "expected_answer": "John Smith, Jane Doe, Bob Johnson"
        },
        {
            "question": "Which department has the most employees?",
            "expected_answer": "Engineering"
        }
    ]
    
    print(json.dumps(sample_output, indent=2))

def show_common_table_examples():
    """Show common database table combinations."""
    print("\n[4] Common Table Combinations:")
    print("-" * 40)
    
    examples = [
        {
            "domain": "HR/Employee Management",
            "tables": "Employees,Departments,Positions,Salaries"
        },
        {
            "domain": "E-commerce",
            "tables": "Customers,Orders,OrderItems,Products,Categories"
        },
        {
            "domain": "Library System", 
            "tables": "Books,Authors,Members,Loans,Categories"
        },
        {
            "domain": "School/University",
            "tables": "Students,Courses,Enrollments,Instructors,Departments"
        },
        {
            "domain": "Hospital/Healthcare",
            "tables": "Patients,Doctors,Appointments,Treatments,Departments"
        },
        {
            "domain": "Project Management",
            "tables": "Projects,Tasks,Employees,Assignments,Departments"
        }
    ]
    
    for example in examples:
        print(f"\n• {example['domain']}:")
        print(f"  Tables: {example['tables']}")

def show_troubleshooting():
    """Show troubleshooting tips."""
    print("\n[5] Troubleshooting Tips:")
    print("-" * 40)
    
    tips = [
        "Ensure your database has explicit foreign key constraints defined",
        "Check that ODBC Driver 17 for SQL Server is installed", 
        "Verify database connection by testing with SQL Server Management Studio first",
        "Make sure your OpenAI API key has sufficient credits and permissions",
        "Start with simple two-table relationships before trying complex schemas",
        "Use --log-level DEBUG to see detailed execution information"
    ]
    
    for i, tip in enumerate(tips, 1):
        print(f"{i}. {tip}")

def main():
    """Main example function."""
    print_banner()
    
    config_ok = check_configuration()
    show_example_commands()
    show_sample_output()
    show_common_table_examples()
    show_troubleshooting()
    
    print("\n" + "=" * 60)
    if config_ok:
        print("✅ Ready to generate! Try one of the example commands above.")
    else:
        print("⚠️  Please configure .env file before running the generator.")
    print("=" * 60)

if __name__ == '__main__':
    main()
