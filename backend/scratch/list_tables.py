import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append("/home/kauanmassuia/projeto-melhoramais")
load_dotenv("/home/kauanmassuia/projeto-melhoramais/.env")

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.connect() as conn:
    # List all tables in genetics and silver schemas
    tables = conn.execute(text("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema IN ('genetics', 'silver', 'public')
        ORDER BY table_schema, table_name;
    """)).fetchall()
    
    print("Tables in database:")
    for schema, table in tables:
        # Get count of rows in the table
        try:
            count = conn.execute(text(f"SELECT count(*) FROM {schema}.{table}")).scalar()
            print(f"  {schema}.{table}: {count} rows")
        except Exception as e:
            print(f"  {schema}.{table}: Error: {e}")
