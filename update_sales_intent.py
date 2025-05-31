import pymysql
import sys
import os

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

def update_specific_message(message_id):
    """Update sales intent for a specific message"""
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get the message content
    cursor.execute("SELECT id, content FROM message WHERE id = %s", (message_id,))
    result = cursor.fetchone()
    
    if not result:
        print(f"❌ Message with ID {message_id} not found")
        conn.close()
        return
    
    msg_id, content = result
    print(f"📝 Message {msg_id}: {content[:100]}...")
    
    # Analyze the sales intent
    intent = sales_analyzer.analyze(content)
    print(f"🤖 Analyzed intent: {intent}")
    
    # Update the message
    cursor.execute("""
        UPDATE message 
        SET sales_intent = %s 
        WHERE id = %s
    """, (intent, msg_id))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated message {msg_id} with intent: {intent}")

def update_all_messages():
    """Update sales intent for all messages without intent"""
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get messages without sales intent
    cursor.execute("""
        SELECT id, content 
        FROM message 
        WHERE sales_intent IS NULL OR sales_intent = ''
        ORDER BY id
    """)
    
    messages = cursor.fetchall()
    
    if not messages:
        print("✅ All messages already have sales intent assigned")
        conn.close()
        return
    
    print(f"🔄 Updating {len(messages)} messages...")
    
    updated_count = 0
    for msg_id, content in messages:
        try:
            # Analyze the sales intent
            intent = sales_analyzer.analyze(content)
            
            # Update the message
            cursor.execute("""
                UPDATE message 
                SET sales_intent = %s 
                WHERE id = %s
            """, (intent, msg_id))
            
            updated_count += 1
            
            if updated_count % 10 == 0:
                print(f"   Updated {updated_count}/{len(messages)} messages...")
                
        except Exception as e:
            print(f"❌ Error processing message {msg_id}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Successfully updated {updated_count} messages!")

def show_intent_distribution():
    """Show the current distribution of sales intents"""
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COALESCE(sales_intent, 'NULL') as intent,
            COUNT(*) as count
        FROM message 
        GROUP BY sales_intent 
        ORDER BY count DESC
    """)
    
    results = cursor.fetchall()
    
    print("📊 Current Sales Intent Distribution:")
    for intent, count in results:
        print(f"   {intent}: {count} messages")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Update specific message by ID
        try:
            message_id = int(sys.argv[1])
            update_specific_message(message_id)
        except ValueError:
            print("❌ Please provide a valid message ID")
    else:
        # Show current distribution
        show_intent_distribution()
        
        # Ask user what to do
        choice = input("\nWould you like to update all messages without intent? (y/N): ")
        if choice.lower() in ['y', 'yes']:
            update_all_messages()
            print("\n" + "="*50)
            show_intent_distribution()
        else:
            print("ℹ️  No updates made. Use 'python update_sales_intent.py <message_id>' to update a specific message.") 