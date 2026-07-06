import os
import sys
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append("/home/kauanmassuia/projeto-melhoramais")
load_dotenv("/home/kauanmassuia/projeto-melhoramais/.env")

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.connect() as conn:
    res = conn.execute(text("""
        SELECT metrics, progeny_stats, phenotypes 
        FROM genetics.genetic_evaluations 
        WHERE metrics IS NOT NULL AND metrics != '{}'::jsonb
        LIMIT 5
    """)).fetchall()
    
    for idx, row in enumerate(res):
        print(f"Row {idx}:")
        print(f"  metrics: {json.dumps(row[0])[:200]}")
        print(f"  progeny_stats: {json.dumps(row[1])}")
        print(f"  phenotypes: {json.dumps(row[2])}")
