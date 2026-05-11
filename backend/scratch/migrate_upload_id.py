import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("DATABASE_URL not found")
    exit(1)

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Adicionando coluna upload_id à tabela genetics.animals...")
        conn.execute(text("ALTER TABLE genetics.animals ADD COLUMN IF NOT EXISTS upload_id VARCHAR(36)"))
        conn.commit()
        print("Coluna adicionada com sucesso!")
except Exception as e:
    print(f"Erro: {e}")
