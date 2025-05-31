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

# Get message statistics
cursor.execute("SELECT COUNT(*) FROM message")
total_messages = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM message WHERE sales_intent IS NOT NULL")
messages_with_intent = cursor.fetchone()[0]

print(f"📊 Message Statistics:")
print(f"   Total messages: {total_messages}")
print(f"   Messages with sales intent: {messages_with_intent}")
print(f"   Messages without intent: {total_messages - messages_with_intent}")

# Get intent distribution
print(f"\n📈 Sales Intent Distribution:")
cursor.execute("""
    SELECT 
        COALESCE(sales_intent, 'NULL') as intent,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / %s, 2) as percentage
    FROM message 
    GROUP BY sales_intent 
    ORDER BY count DESC
""", (total_messages,))

intent_stats = cursor.fetchall()
for intent, count, percentage in intent_stats:
    print(f"   {intent}: {count} messages ({percentage}%)")

# Get recent messages
print(f"\n💬 Recent Messages (Last 10):")
cursor.execute("""
    SELECT 
        m.id,
        u.username,
        r.name as room_name,
        m.content,
        m.sales_intent,
        m.timestamp
    FROM message m
    LEFT JOIN user u ON m.user_id = u.id
    LEFT JOIN room r ON m.room_id = r.id
    ORDER BY m.timestamp DESC
    LIMIT 10
""")

recent_messages = cursor.fetchall()
print("-" * 100)

for msg_id, username, room_name, content, intent, timestamp in recent_messages:
    content_preview = content[:60] + "..." if len(content) > 60 else content
    username = username or "Unknown"
    room_name = room_name or "Unknown Room"
    intent = intent or "No Intent"
    
    print(f"ID: {msg_id} | User: {username} | Room: {room_name}")
    print(f"Content: {content_preview}")
    print(f"Intent: {intent} | Time: {timestamp}")
    print("-" * 100)

conn.close()
print("\n✅ Message check complete!") 