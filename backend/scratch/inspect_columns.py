import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append("/home/kauanmassuia/projeto-melhoramais")
load_dotenv("/home/kauanmassuia/projeto-melhoramais/.env")

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.connect() as conn:
    cols = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'genetics' AND table_name = 'genetic_evaluations'
        ORDER BY ordinal_position;
    """)).fetchall()
    
    print("Columns in genetics.genetic_evaluations:")
    for col, dtype in cols:
        print(f"  {col}: {dtype}")
