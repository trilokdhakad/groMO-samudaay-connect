import sqlite3

# Connect to the database
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Get all rooms
cursor.execute("SELECT id, name FROM room")
rooms = cursor.fetchall()

print("\nAvailable Rooms:")
print("-" * 40)
for room_id, name in rooms:
    print(f"ID: {room_id}, Name: {name}")

conn.close() 