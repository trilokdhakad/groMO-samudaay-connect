import pymysql

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'samudaay_connect'
}

print("MySQL Database Structure Check")
print("=" * 50)

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

# Show all tables
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()

print(f"\nFound {len(tables)} tables:")
for table in tables:
    table_name = table[0]
    print(f"\n📋 Table: {table_name}")
    
    # Show table structure
    cursor.execute(f"DESCRIBE {table_name}")
    columns = cursor.fetchall()
    
    print("   Columns:")
    for col in columns:
        field, type_info, null, key, default, extra = col
        key_info = f" ({key})" if key else ""
        null_info = "NULL" if null == "YES" else "NOT NULL"
        default_info = f" DEFAULT {default}" if default else ""
        extra_info = f" {extra}" if extra else ""
        print(f"     - {field}: {type_info} {null_info}{default_info}{extra_info}{key_info}")
    
    # Show record count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"   Records: {count}")

conn.close()
print("\n✅ Database structure check complete!") 