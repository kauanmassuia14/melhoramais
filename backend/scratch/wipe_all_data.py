import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== LIMPANDO TODO O BANCO DE DADOS DE GENÉTICA ===")
    
    # Ordem importante para não violar chaves estrangeiras
    print("1/4: Removendo avaliações genéticas...")
    conn.execute(text("DELETE FROM genetics.genetic_evaluations"))
    
    print("2/4: Removendo animais...")
    conn.execute(text("DELETE FROM genetics.animals"))
    
    print("3/4: Removendo histórico de uploads...")
    conn.execute(text("DELETE FROM genetics.uploads"))
    
    print("4/4: Removendo logs de processamento...")
    conn.execute(text("DELETE FROM genetics.processing_log"))
    
    conn.commit()
    print("\n=== BANCO DE DADOS ZERADO COM SUCESSO! ===")
    print("Total de Animais: 0")
    print("Total de Avaliações: 0")
    print("Você já pode começar os novos uploads.")
