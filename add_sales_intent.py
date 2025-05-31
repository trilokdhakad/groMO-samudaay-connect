import sqlite3
from pathlib import Path

# Get the database file path
db_path = Path('app.db')

if not db_path.exists():
    print(f"Database not found at {db_path}")
    exit(1)

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add the sales_intent column
    cursor.execute('''
        ALTER TABLE message 
        ADD COLUMN sales_intent VARCHAR(20) DEFAULT 'exploring'
    ''')
    
    # Commit the changes
    conn.commit()
    print("Successfully added sales_intent column to message table")
    
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("Column already exists")
    else:
        print(f"Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    # Close the connection
    if 'conn' in locals():
        conn.close() 