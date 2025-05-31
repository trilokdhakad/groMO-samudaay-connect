import sqlite3

# Connect to the database
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Get list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("\nTables in database:")
print("-" * 40)
for table in tables:
    print(f"Table: {table[0]}")
    # Get count of records in each table
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"Number of records: {count}")
    print("-" * 20)

conn.close() 