import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== CONSTRAINTS DE genetic_evaluations ===")
    res = conn.execute(text("""
        SELECT conname, pg_get_constraintdef(c.oid)
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE n.nspname = 'genetics' AND conrelid = 'genetics.genetic_evaluations'::regclass
    """)).fetchall()
    for row in res:
        print(f"Constraint: {row[0]} | Def: {row[1]}")
