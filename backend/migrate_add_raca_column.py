"""
Migração: Adiciona coluna 'raca' ao genetics.animals
Segura para produção - apenas ADD COLUMN, sem deletar nada.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check if column already exists
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = 'genetics' AND table_name = 'animals' AND column_name = 'raca'
    """))
    if result.fetchone():
        print("Column 'raca' already exists in genetics.animals — skipping.")
    else:
        conn.execute(text("ALTER TABLE genetics.animals ADD COLUMN raca VARCHAR(100)"))
        conn.commit()
        print("SUCCESS: Added column 'raca' to genetics.animals")
