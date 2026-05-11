import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== ANIMAIS COM AVALIAÇÃO ===")
    res = conn.execute(text("""
        SELECT a.rgn, a.nome, e.fonte_origem, e.safra
        FROM genetics.animals a
        JOIN genetics.genetic_evaluations e ON a.id = e.animal_id
        LIMIT 10
    """)).fetchall()
    for row in res:
        print(f"RGN: {row[0]} | Nome: {row[1]} | Fonte: {row[2]} | Safra: {row[3]}")
