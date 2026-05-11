import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== ÚLTIMO UPLOAD ===")
    res = conn.execute(text("SELECT upload_id, nome, data_upload FROM genetics.uploads ORDER BY data_upload DESC LIMIT 1")).fetchone()
    print(f"ID: {res[0]} | Nome: {res[1]} | Data: {res[2]}")
