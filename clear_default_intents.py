import pymysql

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'samudaay_connect'
}

def clear_default_intents():
    """Clear default 'exploring' sales intents from message table"""
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Count messages with default intent
    cursor.execute("SELECT COUNT(*) FROM message WHERE sales_intent = 'exploring'")
    count_before = cursor.fetchone()[0]
    
    print(f"Found {count_before} messages with default 'exploring' intent")
    
    if count_before > 0:
        # Clear the default intents
        cursor.execute("UPDATE message SET sales_intent = NULL WHERE sales_intent = 'exploring'")
        
        # Commit changes
        conn.commit()
        
        # Count again to verify
        cursor.execute("SELECT COUNT(*) FROM message WHERE sales_intent = 'exploring'")
        count_after = cursor.fetchone()[0]
        
        print(f"✅ Cleared {count_before - count_after} default intents")
        print(f"Remaining messages with 'exploring' intent: {count_after}")
    else:
        print("✅ No default intents found to clear")
    
    # Show current intent distribution
    print("\n📊 Current sales intent distribution:")
    cursor.execute("""
        SELECT 
            COALESCE(sales_intent, 'NULL') as intent,
            COUNT(*) as count
        FROM message 
        GROUP BY sales_intent 
        ORDER BY count DESC
    """)
    
    results = cursor.fetchall()
    for intent, count in results:
        print(f"  {intent}: {count} messages")
    
    conn.close()

if __name__ == "__main__":
    clear_default_intents() 