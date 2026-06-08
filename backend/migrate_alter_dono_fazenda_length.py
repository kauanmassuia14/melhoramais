"""
Migration to increase the length of the 'dono_fazenda' column in 'genetics.farms' table from VARCHAR(20) to VARCHAR(255).
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine
from sqlalchemy import text

def migrate():
    print("Iniciando migração para alterar tamanho da coluna dono_fazenda na tabela genetics.farms...")
    
    with engine.connect() as conn:
        try:
            # PostgreSQL command to alter the column type
            # We use character varying(255) to support names up to 255 chars.
            alter_query = text("ALTER TABLE genetics.farms ALTER COLUMN dono_fazenda TYPE character varying(255);")
            conn.execute(alter_query)
            conn.commit()
            print("Sucesso: Coluna dono_fazenda alterada para VARCHAR(255)!")
        except Exception as e:
            conn.rollback()
            print(f"Erro ao executar migração: {e}")
            raise e

if __name__ == "__main__":
    migrate()
