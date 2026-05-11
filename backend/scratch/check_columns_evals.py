import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== COLUNAS DE genetic_evaluations ===")
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema = 'genetics' AND table_name = 'genetic_evaluations'")).fetchall()
    for row in res:
        print(row[0])
