import pymysql
from pathlib import Path

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'samudaay_connect'
}

def add_sales_intent_column():
    """Add sales_intent column to message table if it doesn't exist"""
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if sales_intent column already exists
        cursor.execute("DESCRIBE message")
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]
        
        if 'sales_intent' in column_names:
            print("✅ sales_intent column already exists in message table")
        else:
            # Add the sales_intent column
            cursor.execute("""
                ALTER TABLE message 
                ADD COLUMN sales_intent VARCHAR(255) DEFAULT NULL
            """)
            
            conn.commit()
            print("✅ Successfully added sales_intent column to message table")
        
        # Show current table structure
        print("\n📋 Current message table structure:")
        cursor.execute("DESCRIBE message")
        columns = cursor.fetchall()
        
        for col in columns:
            field, type_info, null, key, default, extra = col
            key_info = f" ({key})" if key else ""
            null_info = "NULL" if null == "YES" else "NOT NULL"
            default_info = f" DEFAULT {default}" if default else ""
            extra_info = f" {extra}" if extra else ""
            print(f"  - {field}: {type_info} {null_info}{default_info}{extra_info}{key_info}")
        
        conn.close()
        
    except pymysql.Error as e:
        print(f"❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    add_sales_intent_column() 