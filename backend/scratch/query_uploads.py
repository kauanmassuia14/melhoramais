import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append("/home/kauanmassuia/projeto-melhoramais")
load_dotenv("/home/kauanmassuia/projeto-melhoramais/.env")

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.connect() as conn:
    uploads = conn.execute(text("SELECT upload_id, nome, fonte_origem, arquivo_nome_original, total_registros, status FROM genetics.uploads")).fetchall()
    print("Uploads in database:")
    for row in uploads:
        print(f"  {row}")
