import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== BUSCANDO ANCP ===")
    res = conn.execute(text("SELECT count(*) FROM genetics.genetic_evaluations WHERE fonte_origem = 'ANCP'")).scalar()
    print(f"Total ANCP Evals: {res}")
    
    if res > 0:
        print("\nExemplo de avaliação ANCP:")
        ex = conn.execute(text("SELECT animal_id, metrics FROM genetics.genetic_evaluations WHERE fonte_origem = 'ANCP' LIMIT 1")).fetchone()
        print(f"Animal ID: {ex[0]}")
        print(f"Metrics: {str(ex[1])[:200]}...")
