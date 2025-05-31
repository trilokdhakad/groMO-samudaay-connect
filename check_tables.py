import pymysql

# Connect to MySQL database
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='samudaay_connect'
)
cursor = conn.cursor()

# Show tables
cursor.execute("SHOW TABLES;")
tables = cursor.fetchall()

print("Tables in the database:")
for table in tables:
    print(f"- {table[0]}")

conn.close() 