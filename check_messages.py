import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Get the columns in the message table
cursor.execute("PRAGMA table_info(message)")
columns = cursor.fetchall()
print("\nMessage table columns:")
for col in columns:
    print(f"{col[1]} ({col[2]})")

# Get a sample of messages
cursor.execute("""
    SELECT content, sales_intent
    FROM message
    LIMIT 5
""")

print("\nSample messages:")
print("-" * 40)
messages = cursor.fetchall()
for msg in messages:
    content, sales_intent = msg
    print(f"Content: {content}")
    print(f"Sales Intent: {sales_intent}")
    print("-" * 40)

conn.close() 