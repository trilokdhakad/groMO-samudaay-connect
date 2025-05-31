import sqlite3

def get_mysql_type(sqlite_type):
    sqlite_type = sqlite_type.upper()
    if 'INTEGER' in sqlite_type:
        return 'INT'
    elif 'REAL' in sqlite_type or 'FLOAT' in sqlite_type:
        return 'FLOAT'
    elif 'TEXT' in sqlite_type:
        return 'TEXT'
    elif 'BOOLEAN' in sqlite_type:
        return 'TINYINT(1)'
    elif 'DATETIME' in sqlite_type:
        return 'DATETIME'
    elif 'VARCHAR' in sqlite_type or 'STRING' in sqlite_type:
        length = '255'
        if '(' in sqlite_type:
            length = sqlite_type.split('(')[1].split(')')[0]
        return f'VARCHAR({length})'
    else:
        return 'TEXT'

def generate_mysql_schema():
    # Connect to SQLite database
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    # Create output file
    with open('mysql_export/schema.sql', 'w', encoding='utf-8') as f:
        f.write("-- MySQL Schema generated from SQLite\n")
        f.write("-- Generated on " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n")
        
        f.write("SET FOREIGN_KEY_CHECKS=0;\n")
        f.write("SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';\n")
        f.write("START TRANSACTION;\n")
        f.write("SET time_zone = '+00:00';\n\n")
        
        # Process each table
        for (table_name,) in tables:
            print(f"Processing table: {table_name}")
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()
            
            # Start CREATE TABLE statement
            f.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
            f.write(f"CREATE TABLE `{table_name}` (\n")
            
            # Process columns
            column_defs = []
            primary_keys = []
            
            for col in columns:
                col_id, col_name, col_type, not_null, default_value, is_pk = col
                
                # Build column definition
                col_def = [f"`{col_name}`"]
                col_def.append(get_mysql_type(col_type))
                
                if not_null:
                    col_def.append("NOT NULL")
                if default_value is not None:
                    if isinstance(default_value, str):
                        col_def.append(f"DEFAULT '{default_value}'")
                    else:
                        col_def.append(f"DEFAULT {default_value}")
                
                if is_pk:
                    if col_type.upper() == 'INTEGER':
                        col_def.append("AUTO_INCREMENT")
                    primary_keys.append(col_name)
                
                column_defs.append("  " + " ".join(col_def))
            
            # Add primary key constraint
            if primary_keys:
                column_defs.append(f"  PRIMARY KEY (`{'`, `'.join(primary_keys)}`)")
            
            # Add foreign key constraints
            for fk in foreign_keys:
                id, seq, table, from_, to, on_update, on_delete, match = fk
                fk_def = f"  CONSTRAINT `fk_{table_name}_{from_}` FOREIGN KEY (`{from_}`) "
                fk_def += f"REFERENCES `{table}` (`{to}`)"
                if on_delete:
                    fk_def += f" ON DELETE {on_delete}"
                if on_update:
                    fk_def += f" ON UPDATE {on_update}"
                column_defs.append(fk_def)
            
            # Write column definitions
            f.write(",\n".join(column_defs))
            f.write("\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n\n")
        
        f.write("SET FOREIGN_KEY_CHECKS=1;\n")
        f.write("COMMIT;\n")
    
    conn.close()
    print("MySQL schema has been generated in mysql_export/schema.sql")

if __name__ == "__main__":
    from datetime import datetime
    import os
    
    # Create output directory if it doesn't exist
    os.makedirs("mysql_export", exist_ok=True)
    
    # Generate schema
    generate_mysql_schema() 