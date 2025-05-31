import pymysql

# Configuration  
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'samudaay_connect'
}

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

# Get all rooms with their message counts
cursor.execute("""
    SELECT 
        r.id,
        r.name,
        r.description,
        r.created_at,
        COUNT(m.id) as message_count
    FROM room r
    LEFT JOIN message m ON r.id = m.room_id
    GROUP BY r.id, r.name, r.description, r.created_at
    ORDER BY r.created_at DESC
""")

rooms = cursor.fetchall()

print(f"📋 Found {len(rooms)} rooms in the database:")
print("=" * 80)

for room_id, name, description, created_at, msg_count in rooms:
    print(f"\n🏠 Room ID: {room_id}")
    print(f"   Name: {name}")
    print(f"   Description: {description}")
    print(f"   Created: {created_at}")
    print(f"   Messages: {msg_count}")
    
    # Get recent messages for this room
    cursor.execute("""
        SELECT content, timestamp, sales_intent 
        FROM message 
        WHERE room_id = %s 
        ORDER BY timestamp DESC 
        LIMIT 3
    """, (room_id,))
    
    recent_messages = cursor.fetchall()
    
    if recent_messages:
        print("   Recent messages:")
        for content, timestamp, intent in recent_messages:
            content_preview = content[:50] + "..." if len(content) > 50 else content
            intent_info = f" [{intent}]" if intent else " [no intent]"
            print(f"     - {timestamp}: {content_preview}{intent_info}")
    else:
        print("     - No messages yet")
    
    print("-" * 40)

conn.close()
print("\n✅ Room check complete!") 