import sqlite3
from app.sales_analysis import sales_analyzer

# Connect to the database
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Update all messages silently
cursor.execute("""
    SELECT id, content
    FROM message
    ORDER BY timestamp DESC
""")
messages = cursor.fetchall()

# Prepare batch updates
updates = []
for msg_id, content in messages:
    intent = sales_analyzer.analyze(content)
    updates.append((intent, msg_id))

# Perform batch update
cursor.executemany("""
    UPDATE message
    SET sales_intent = ?
    WHERE id = ?
""", updates)

# Commit the changes
conn.commit()
conn.close() 