import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== BUSCANDO RGN 1528 ===")
    res = conn.execute(text("SELECT id, farm_id, upload_id, nome FROM genetics.animals WHERE rgn = '1528'")).fetchall()
    for row in res:
        print(f"ID: {row[0]} | Farm: {row[1]} | Upload: {row[2]} | Nome: {row[3]}")
        evals = conn.execute(text("SELECT id, fonte_origem, metrics FROM genetics.genetic_evaluations WHERE animal_id = :aid"), {"aid": row[0]}).fetchall()
        print(f"   -> Avaliações: {len(evals)}")
