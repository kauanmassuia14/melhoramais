import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append("/home/kauanmassuia/projeto-melhoramais")
load_dotenv("/home/kauanmassuia/projeto-melhoramais/.env")

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.connect() as conn:
    cnt = conn.execute(text("SELECT count(*) FROM genetics.animals WHERE sire_id IS NOT NULL")).scalar()
    print(f"Animals with sire_id populated: {cnt}")
    
    cnt_dam = conn.execute(text("SELECT count(*) FROM genetics.animals WHERE dam_id IS NOT NULL")).scalar()
    print(f"Animals with dam_id populated: {cnt_dam}")
