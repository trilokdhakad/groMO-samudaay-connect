import sqlite3
from pathlib import Path

# Connect to the database
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Get table info
cursor.execute("PRAGMA table_info(message)")
columns = cursor.fetchall()

print("Message table structure:")
for col in columns:
    print(f"Column: {col[1]}, Type: {col[2]}, Nullable: {col[3]}, Default: {col[4]}")

conn.close() 