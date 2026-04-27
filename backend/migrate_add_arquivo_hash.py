"""
Migração para adicionar coluna arquivo_hash à tabela uploads
Executar: python -m backend.migrate_add_arquivo_hash
"""
from sqlalchemy import text
from backend.database import engine


def migrate():
    """Adiciona coluna arquivo_hash à tabela uploads."""
    
    db_url = str(engine.url)
    is_sqlite = db_url.startswith("sqlite")
    
    with engine.connect() as conn:
        # Verifica se a coluna já existe
        if is_sqlite:
            result = conn.execute(text("PRAGMA table_info(uploads)"))
            cols = [row[1] for row in result.fetchall()]
        else:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'uploads' AND table_schema = 'silver'
            """))
            cols = [row[0] for row in result.fetchall()]
        
        if "arquivo_hash" in cols:
            print("Coluna arquivo_hash já existe.")
            return
        
        # Adiciona a coluna
        if is_sqlite:
            conn.execute(text("ALTER TABLE uploads ADD COLUMN arquivo_hash TEXT"))
        else:
            conn.execute(text("ALTER TABLE silver.uploads ADD COLUMN arquivo_hash VARCHAR(64)"))
        
        conn.commit()
        print("Coluna arquivo_hash adicionada com sucesso!")


if __name__ == "__main__":
    migrate()