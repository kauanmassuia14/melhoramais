import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== ÚLTIMO UPLOAD E SEUS RESULTADOS ===")
    last_upload = conn.execute(text("SELECT upload_id, nome, data_upload, status, error_message FROM uploads ORDER BY data_upload DESC LIMIT 1")).fetchone()
    
    if not last_upload:
        print("Nenhum upload encontrado.")
    else:
        uid = last_upload[0]
        print(f"Upload: {last_upload[1]} | ID: {uid} | Status: {last_upload[3]}")
        print(f"Erro: {last_upload[4]}")
        
        animal_count = conn.execute(text("SELECT count(*) FROM genetics.animals WHERE upload_id = :uid"), {"uid": uid}).scalar()
        eval_count = conn.execute(text("SELECT count(*) FROM genetics.genetic_evaluations WHERE upload_id = :uid"), {"uid": uid}).scalar()
        
        print(f"Animais inseridos: {animal_count}")
        print(f"Avaliações inseridas: {eval_count}")
        
        if animal_count > 0 and eval_count == 0:
            print("\n[ALERTA] Os animais foram salvos, mas as avaliações NÃO.")
            # Vamos ver se existem avaliações órfãs ou com erro
            eval_total = conn.execute(text("SELECT count(*) FROM genetics.genetic_evaluations")).scalar()
            print(f"Total global de avaliações no banco: {eval_total}")
