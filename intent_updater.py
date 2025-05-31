import pymysql
import sys
import os
from datetime import datetime, timedelta, UTC

# Add the parent directory to the path to import the sales_analyzer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.sales_analysis import sales_analyzer

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'samudaay_connect'
}

def update_sales_intents():
    """Update sales intents for all messages"""
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get all messages without sales intent
    cursor.execute("""
        SELECT id, content 
        FROM message 
        WHERE sales_intent IS NULL OR sales_intent = ''
    """)
    
    messages = cursor.fetchall()
    
    if not messages:
        print("No messages found without sales intent.")
        conn.close()
        return
    
    print(f"Found {len(messages)} messages to update...")
    
    updated_count = 0
    for msg_id, content in messages:
        try:
            # Analyze the sales intent
            intent = sales_analyzer.analyze(content)
            
            # Update the message with the sales intent
            cursor.execute("""
                UPDATE message 
                SET sales_intent = %s 
                WHERE id = %s
            """, (intent, msg_id))
            
            updated_count += 1
            if updated_count % 10 == 0:
                print(f"Updated {updated_count} messages...")
                
        except Exception as e:
            print(f"Error processing message {msg_id}: {e}")
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print(f"✅ Successfully updated {updated_count} messages with sales intents!")

if __name__ == "__main__":
    update_sales_intents() 