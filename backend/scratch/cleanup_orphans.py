import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== INICIANDO LIMPEZA DE DADOS QUEBRADOS ===")
    
    # 1. Contar antes
    before_animals = conn.execute(text("SELECT count(*) FROM genetics.animals")).scalar()
    
    # 2. Excluir animais sem avaliações (os que ficaram "órfãos" dos uploads antigos)
    print("Removendo animais sem avaliações genéticas...")
    deleted_animals = conn.execute(text("""
        DELETE FROM genetics.animals 
        WHERE id NOT IN (SELECT DISTINCT animal_id FROM genetics.genetic_evaluations)
    """))
    
    # 3. Excluir uploads que não geraram avaliações
    print("Removendo histórico de uploads incompletos...")
    deleted_uploads = conn.execute(text("""
        DELETE FROM genetics.uploads 
        WHERE upload_id NOT IN (SELECT DISTINCT upload_id FROM genetics.genetic_evaluations)
    """))
    
    conn.commit()
    
    # 4. Contar depois
    after_animals = conn.execute(text("SELECT count(*) FROM genetics.animals")).scalar()
    total_evals = conn.execute(text("SELECT count(*) FROM genetics.genetic_evaluations")).scalar()
    
    print("\n=== LIMPEZA CONCLUÍDA ===")
    print(f"Animais removidos: {before_animals - after_animals}")
    print(f"Animais restantes: {after_animals}")
    print(f"Total de avaliações mantidas: {total_evals}")
    print("Agora seu banco de dados contém apenas animais com dados completos!")
