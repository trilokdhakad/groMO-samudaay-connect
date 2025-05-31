import pymysql
from datetime import datetime

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root', 
    'password': '',
    'database': 'samudaay_connect'
}

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

# Get all messages with their sales intents
cursor.execute("""
    SELECT id, content, sales_intent, timestamp 
    FROM message 
    ORDER BY timestamp DESC
""")

messages = cursor.fetchall()

print(f"Found {len(messages)} messages:")
print("-" * 80)

for msg_id, content, sales_intent, timestamp in messages:
    print(f"ID: {msg_id}")
    print(f"Content: {content[:100]}{'...' if len(content) > 100 else ''}")
    print(f"Sales Intent: {sales_intent}")
    print(f"Timestamp: {timestamp}")
    print("-" * 40)

conn.close()

if __name__ == "__main__":
    display_intents() 