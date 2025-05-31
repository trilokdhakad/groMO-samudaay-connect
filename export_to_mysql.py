import sqlite3
import json
from datetime import datetime
import os

def format_value(value):
    if value is None:
        return 'NULL'
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, bool):
        return '1' if value else '0'
    elif isinstance(value, (dict, list)):
        return f"'{json.dumps(value).replace("'", "''")}'"
    elif isinstance(value, datetime):
        return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
    else:
        return f"'{str(value).replace("'", "''")}'"

def get_table_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [column[1] for column in cursor.fetchall()]

def export_table(cursor, table_name, output_dir):
    print(f"Exporting table: {table_name}")
    
    # Get column names
    columns = get_table_columns(cursor, table_name)
    
    # Get all data
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    if not rows:
        print(f"No data found in table {table_name}")
        return
    
    # Create output file
    output_file = os.path.join(output_dir, f"{table_name}.sql")
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write file header
        f.write(f"-- {table_name} table export\n")
        f.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Write SET statements for MySQL
        f.write("SET FOREIGN_KEY_CHECKS=0;\n")
        f.write("SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';\n\n")
        
        # Write table truncate
        f.write(f"TRUNCATE TABLE `{table_name}`;\n\n")
        
        # Write INSERT statements in batches
        batch_size = 1000
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            values_strings = []
            
            for row in batch:
                formatted_values = [format_value(val) for val in row]
                values_strings.append(f"({', '.join(formatted_values)})")
            
            insert_stmt = f"INSERT INTO `{table_name}` (`{'`, `'.join(columns)}`) VALUES\n"
            insert_stmt += ",\n".join(values_strings) + ";\n"
            
            f.write(insert_stmt)
        
        # Write footer
        f.write("\nSET FOREIGN_KEY_CHECKS=1;\n")
    
    print(f"Exported {len(rows)} rows to {output_file}")

def main():
    # Create output directory
    output_dir = "mysql_export"
    os.makedirs(output_dir, exist_ok=True)
    
    # Connect to SQLite database
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    # Export each table
    for (table_name,) in tables:
        try:
            export_table(cursor, table_name, output_dir)
        except Exception as e:
            print(f"Error exporting table {table_name}: {str(e)}")
    
    # Close connection
    conn.close()
    
    print("\nExport completed! Files are in the 'mysql_export' directory.")
    print("Note: Please review the exported files before importing to MySQL.")

if __name__ == "__main__":
    main() 