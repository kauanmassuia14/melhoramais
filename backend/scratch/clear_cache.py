import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append("/home/kauanmassuia/projeto-melhoramais")
load_dotenv("/home/kauanmassuia/projeto-melhoramais/.env")

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.begin() as conn:
    conn.execute(text("DELETE FROM genetics.dashboard_stats_cache"))
    print("Dashboard stats cache cleared and committed successfully!")
