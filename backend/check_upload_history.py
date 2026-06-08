import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append("/home/kauanmassuia/projeto-melhoramais")
load_dotenv("/home/kauanmassuia/projeto-melhoramais/.env")

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("No DATABASE_URL found")
    sys.exit(1)

engine = create_engine(db_url)

with engine.connect() as conn:
    print("=== Recent Uploads in genetics.uploads ===")
    query = text("""
        SELECT upload_id, nome, fonte_origem, arquivo_nome_original, total_registros, rows_inserted, rows_updated, status, data_upload
        FROM genetics.uploads
        ORDER BY data_upload DESC
        LIMIT 10;
    """)
    res = conn.execute(query).fetchall()
    for row in res:
        print(f"ID: {row[0]}")
        print(f"  Name: {row[1]}")
        print(f"  Source System: {row[2]}")
        print(f"  Original File: {row[3]}")
        print(f"  Total Records in DF: {row[4]}")
        print(f"  Rows Inserted: {row[5]}")
        print(f"  Rows Updated: {row[6]}")
        print(f"  Status: {row[7]}")
        print(f"  Date: {row[8]}")
        print("-" * 50)
