#!/usr/bin/env python3
"""
Test MySQL connection with detailed error reporting
"""
import mysql.connector
import pymysql
from mysql.connector import Error
import socket
import sys

# MySQL connection parameters
MYSQL_CONFIG = {
    'host': '35.225.136.237',
    'database': 'recruitment',
    'user': 'mysqluser',
    'password': 'Rewqasd!001',
    'port': 3306
}

def test_socket_connection():
    """Test raw socket connection to MySQL server"""
    print("Testing socket connection...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout
        result = sock.connect_ex((MYSQL_CONFIG['host'], MYSQL_CONFIG['port']))
        sock.close()
        
        if result == 0:
            print("✅ Socket connection successful - MySQL port is accessible")
            return True
        else:
            print(f"❌ Socket connection failed with error code: {result}")
            return False
    except Exception as e:
        print(f"❌ Socket connection exception: {e}")
        return False

def test_mysql_connector():
    """Test using mysql-connector-python"""
    print("\nTesting mysql-connector-python...")
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        if connection.is_connected():
            print("✅ mysql-connector-python connection successful!")
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"MySQL Server version: {version[0]}")
            cursor.close()
            connection.close()
            return True
    except Error as e:
        print(f"❌ mysql-connector-python error: {e}")
        print(f"Error Code: {e.errno}")
        print(f"SQL State: {e.sqlstate}")
        return False
    except Exception as e:
        print(f"❌ mysql-connector-python exception: {e}")
        return False

def test_pymysql():
    """Test using PyMySQL"""
    print("\nTesting PyMySQL...")
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        print("✅ PyMySQL connection successful!")
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"MySQL Server version: {version[0]}")
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        print(f"❌ PyMySQL error: {e}")
        return False

def main():
    print("MySQL Connection Test")
    print("=" * 50)
    print(f"Host: {MYSQL_CONFIG['host']}")
    print(f"Port: {MYSQL_CONFIG['port']}")
    print(f"Database: {MYSQL_CONFIG['database']}")
    print(f"User: {MYSQL_CONFIG['user']}")
    print("=" * 50)
    
    # Test socket connection first
    socket_ok = test_socket_connection()
    
    if socket_ok:
        # Test MySQL connections
        mysql_ok = test_mysql_connector()
        pymysql_ok = test_pymysql()
        
        if mysql_ok or pymysql_ok:
            print("\n✅ At least one MySQL driver works!")
        else:
            print("\n❌ All MySQL drivers failed - check credentials or server configuration")
    else:
        print("\n❌ Cannot reach MySQL port - server may be down or port blocked")
        print("Possible issues:")
        print("- MySQL server is not running")
        print("- Port 3306 is blocked by firewall")
        print("- Server is configured to not accept external connections")
        print("- Network connectivity issues")

if __name__ == "__main__":
    main()
