import sqlite3

def clear_default_intents():
    # Connect to the database
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Update all messages where intent is 'exploring' to NULL
    cursor.execute("""
        UPDATE message
        SET sales_intent = NULL
        WHERE sales_intent = 'exploring'
    """)
    
    # Commit the changes
    conn.commit()
    
    # Get count of updated rows
    updated_count = cursor.rowcount
    print(f"\nCleared {updated_count} default 'exploring' intents from the database.")
    
    conn.close()

if __name__ == "__main__":
    clear_default_intents() 