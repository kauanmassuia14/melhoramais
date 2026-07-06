import sys
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente antes de qualquer import do projeto!
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from backend.processor import GeneticDataProcessor
import pandas as pd
import io

# 1. Conecta no seu Docker
engine = create_engine(os.getenv("DATABASE_URL"))
session = Session(engine)

# 2. Cria um "Arquivo Falso" da ANCP para testar
data = {
    'RGN': ['1234', '5678'],
    'NOME': ['BOI TESTE 1', 'BOI TESTE 2'],
    'SEXO': ['MACHO', 'FEMEA'],
    'DT_NASC': ['2024-01-01', '2024-02-15'],
    'PESO_DESM': [210.5, 195.0]
}
df_teste = pd.DataFrame(data)

# Converte o DataFrame em bytes (simulando um upload de arquivo)
tobytes = io.BytesIO()
df_teste.to_excel(tobytes, index=False)
content = tobytes.getvalue()

# 3. Roda o Processador
processor = GeneticDataProcessor(session)
try:
    print("🔥 Iniciando teste de processamento...")
    df_limpo = processor.process_file(content, "teste_ancp.xlsx", "ANCP")
    
    # 4. Salva no Banco (Silver)
    print("📥 Salvando na camada Silver do Postgres...")
    df_limpo.to_sql('animais', con=engine, schema='silver', if_exists='append', index=False)
    
    print("✅ SUCESSO! Verifique o Beekeeper agora!")
except Exception as e:
    print(f"❌ Erro no teste: {e}")