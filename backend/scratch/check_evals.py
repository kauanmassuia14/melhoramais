import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== VERIFICANDO PRIMEIROS 5 ANIMAIS E SUAS AVALIAÇÕES ===")
    animals = conn.execute(text("SELECT id, rgn, nome FROM genetics.animals LIMIT 5")).fetchall()
    
    if not animals:
        print("Nenhum animal encontrado na tabela genetics.animals.")
    else:
        for a in animals:
            print(f"Animal: {a[1]} ({a[2]}) | ID: {a[0]}")
            evals = conn.execute(text("SELECT id, fonte_origem, metrics FROM genetics.genetic_evaluations WHERE animal_id = :aid"), {"aid": a[0]}).fetchall()
            if not evals:
                print("   -> Nenhuma avaliação encontrada.")
            for e in evals:
                print(f"   -> Avaliação {e[1]} | ID: {e[0]}")
                print(f"      Metrics: {str(e[2])[:100]}...")
