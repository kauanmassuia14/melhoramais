import sqlite3

conn = sqlite3.connect("/home/kauanmassuia/projeto-melhoramais/test.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in test.db:")
for t in tables:
    table_name = t[0]
    cursor.execute(f"SELECT count(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  {table_name}: {count} rows")
conn.close()
