#!/usr/bin/env python3
"""
Simple PyMySQL connection test with timeout
"""
import pymysql
import socket

def test_pymysql_connection():
    """Test PyMySQL connection with timeout"""
    print("Testing PyMySQL connection...")
    
    try:
        print("Attempting connection with 10 second timeout...")
        connection = pymysql.connect(
            host='35.225.136.237',
            port=3306,
            user='mysqluser',
            password='Rewqasd!001',
            database='recruitment',
            connect_timeout=10,
            read_timeout=10,
            write_timeout=10,
            charset='utf8mb4'
        )
        
        print("✅ PyMySQL connection successful!")
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"MySQL version: {version[0]}")
        
        cursor.execute("SHOW TABLES LIMIT 5")
        tables = cursor.fetchall()
        print(f"Sample tables: {[table[0] for table in tables]}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ PyMySQL connection failed: {e}")
        print(f"Error type: {type(e)}")
        return False

if __name__ == "__main__":
    test_pymysql_connection()
