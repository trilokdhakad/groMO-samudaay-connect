#!/usr/bin/env python3
"""
MySQL Connection and Table Verification Script
"""
import pymysql
import sys

def check_mysql_connection():
    try:
        # Connect to MySQL database
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='Trilok1234#1',
            database='samudaay_connect'
        )
        print("✅ Successfully connected to MySQL database 'samudaay_connect'")
        
        cursor = conn.cursor()
        
        # Show tables
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        
        print(f"\n📊 Found {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            
            # Get record count for each table
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            print(f"  - {table_name}: {count} records")
        
        # Check specific important tables
        important_tables = ['user', 'message', 'room']
        print("\n🔍 Checking important tables:")
        
        for table_name in important_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  ✅ {table_name}: {count} records")
            except Exception as e:
                print(f"  ❌ {table_name}: Error - {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to MySQL: {e}")
        return False

if __name__ == "__main__":
    if check_mysql_connection():
        print("\n🎉 MySQL is properly configured and working!")
        sys.exit(0)
    else:
        print("\n💥 MySQL connection failed!")
        sys.exit(1) 