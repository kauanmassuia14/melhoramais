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
    print("=== Sample of 10 animals in genetics.animals ===")
    query = text("""
        SELECT id, rgn, serie, nome, created_at
        FROM genetics.animals
        ORDER BY created_at DESC
        LIMIT 10;
    """)
    res = conn.execute(query).fetchall()
    for row in res:
        print(f"ID: {row[0]}")
        print(f"  RGN: {row[1]}")
        print(f"  Serie: {row[2]}")
        print(f"  Nome: {row[3]}")
        print(f"  Created At: {row[4]}")
        print("-" * 50)
