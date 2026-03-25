import sqlite3
DB_PATH = "sap_o2c.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(sales_order_items);")
columns = [row[1] for row in cursor.fetchall()]
print(f"Columns in sales_order_items: {columns}")
conn.close()
