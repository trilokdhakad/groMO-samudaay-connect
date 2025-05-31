import sqlite3
from datetime import datetime

def display_intents():
    # Connect to the database
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Get the most recent messages with their intents
    cursor.execute("""
        SELECT content, sales_intent, timestamp
        FROM message
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    messages = cursor.fetchall()
    
    if not messages:
        print("\nNo messages found in the database.")
    else:
        print("\nMost Recent Messages and Their Sales Intents:")
        print("-" * 70)
        for content, intent, timestamp in messages:
            # Convert timestamp to readable format
            time_str = datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            print(f"\nTime: {time_str}")
            print(f"Message: {content}")
            print(f"Intent: {'Not classified' if intent is None else intent}")
            print("-" * 70)

    conn.close()

if __name__ == "__main__":
    display_intents() 