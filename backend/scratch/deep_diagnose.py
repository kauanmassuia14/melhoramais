import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== STATUS DAS AVALIAÇÕES GENÉTICAS ===")
    
    # 1. Total de animais e avaliações
    total_animals = conn.execute(text("SELECT count(*) FROM genetics.animals")).scalar()
    total_evals = conn.execute(text("SELECT count(*) FROM genetics.genetic_evaluations")).scalar()
    print(f"Total Animais: {total_animals}")
    print(f"Total Avaliações: {total_evals}")
    
    # 2. Ver se existem animais sem avaliações
    orphans = conn.execute(text("""
        SELECT count(*) 
        FROM genetics.animals a
        LEFT JOIN genetics.genetic_evaluations e ON a.id = e.animal_id
        WHERE e.id IS NULL
    """)).scalar()
    print(f"Animais SEM NENHUMA avaliação: {orphans}")
    
    # 3. Ver os 5 últimos uploads e suas contagens
    print("\n=== ÚLTIMOS 5 UPLOADS ===")
    uploads = conn.execute(text("""
        SELECT u.upload_id, u.nome, u.status, 
               (SELECT count(*) FROM genetics.animals WHERE upload_id = u.upload_id) as animals,
               (SELECT count(*) FROM genetics.genetic_evaluations WHERE upload_id = u.upload_id) as evals
        FROM genetics.uploads u
        ORDER BY u.data_upload DESC
        LIMIT 5
    """)).fetchall()
    for u in uploads:
        print(f"Upload: {u[1]} | Status: {u[2]} | Animais: {u[3]} | Evals: {u[4]}")
