import json
import sqlite3
import os
import glob
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sap_o2c.db")
DATA_DIR = os.path.join(BASE_DIR, "sap-o2c-data")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def ingest_jsonl_to_sqlite():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all subdirectories (each represents a table)
    table_dirs = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]

    for table_name in table_dirs:
        print(f"Ingesting table: {table_name}...")
        jsonl_files = glob.glob(os.path.join(DATA_DIR, table_name, "*.jsonl"))
        
        first_file = True
        for file_path in jsonl_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                records = []
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    records.append(record)
                
                if not records:
                    continue

                if first_file:
                    # Create table based on first record's keys
                    columns = []
                    for key, value in records[0].items():
                        # Basic type mapping
                        col_type = "TEXT"
                        if isinstance(value, (int, float)):
                            col_type = "REAL"
                        columns.append(f'"{key}" {col_type}')
                    
                    create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(columns)});'
                    cursor.execute(create_sql)
                    first_file = False

                # Insert records
                keys = list(records[0].keys())
                columns_str = ", ".join([f'"{k}"' for k in keys])
                placeholders = ", ".join(["?"] * len(keys))
                insert_sql = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'
                
                prepared_data = []
                for r in records:
                    row = []
                    for k in keys:
                        val = r.get(k)
                        if isinstance(val, (dict, list)):
                            row.append(json.dumps(val))
                        elif isinstance(val, bool):
                            row.append(1 if val else 0)
                        else:
                            row.append(val)
                    prepared_data.append(tuple(row))
                
                cursor.executemany(insert_sql, prepared_data)

        conn.commit()
    
    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    ingest_jsonl_to_sqlite()
