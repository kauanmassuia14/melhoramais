import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Pega a URL do banco
db_url = os.getenv("DATABASE_URL")

if not db_url:
    print("❌ Erro: DATABASE_URL não encontrada no seu arquivo .env")
else:
    engine = create_engine(db_url)

    try:
        with engine.connect() as conn:
            # Testa se o schema 'silver' que criamos no Beekeeper existe
            query = text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'silver'")
            result = conn.execute(query)
            row = result.fetchone()
            
            if row:
                print(f"✅ Conexão Sucesso! Schema encontrado: {row[0]}")
            else:
                print("⚠️ Conectou, mas o schema 'silver' não foi encontrado. Você rodou o SQL no Beekeeper?")
                
    except Exception as e:
        print(f"❌ Erro ao conectar no Docker: {e}")