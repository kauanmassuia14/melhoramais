import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== CONTAGEM POR FONTE (Tabela Nova: genetics.animals) ===")
    # Como animals não tem fonte_origem, precisamos cruzar com evaluations
    res = conn.execute(text("""
        SELECT e.fonte_origem, COUNT(DISTINCT a.id) 
        FROM genetics.animals a
        LEFT JOIN genetics.genetic_evaluations e ON a.id = e.animal_id
        GROUP BY e.fonte_origem
    """)).fetchall()
    for row in res:
        print(f"Fonte: {row[0]} | Animais: {row[1]}")

    print("\n=== CONTAGEM POR FONTE (Tabela Legada: genetics.animais) ===")
    res_legacy = conn.execute(text("""
        SELECT fonte_origem, COUNT(*) 
        FROM genetics.animais
        GROUP BY fonte_origem
    """)).fetchall()
    for row in res_legacy:
        print(f"Fonte: {row[0]} | Animais: {row[1]}")

    print("\n=== TOTAL DE UPLOADS ===")
    res_uploads = conn.execute(text("SELECT fonte_origem, COUNT(*) FROM uploads GROUP BY fonte_origem")).fetchall()
    for row in res_uploads:
        print(f"Fonte: {row[0]} | Uploads: {row[1]}")
