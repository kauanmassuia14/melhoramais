import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== LISTANDO TODAS AS TABELAS DO BANCO ===")
    res = conn.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog')")).fetchall()
    for row in res:
        print(f"Schema: {row[0]} | Tabela: {row[1]}")
