"""
Migração para criar tabela uploads
Executar: python -m backend.migrate_create_uploads_table
"""
from sqlalchemy import text, inspect
from backend.database import engine


def migrate():
    """Cria a tabela uploads se não existir."""
    
    db_url = str(engine.url)
    is_sqlite = db_url.startswith("sqlite")
    
    with engine.connect() as conn:
        # Verifica se a tabela já existe
        if is_sqlite:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='uploads'"))
            exists = result.fetchone() is not None
        else:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'uploads' AND table_schema = 'silver'
            """))
            exists = result.fetchone() is not None
        
        if exists:
            print("Tabela uploads já existe.")
            return
        
        # Cria a tabela
        if is_sqlite:
            sql = """
                CREATE TABLE uploads (
                    upload_id TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    id_farm INTEGER NOT NULL,
                    fonte_origem TEXT NOT NULL,
                    arquivo_nome_original TEXT,
                    total_registros INTEGER DEFAULT 0,
                    rows_inserted INTEGER DEFAULT 0,
                    rows_updated INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'processing',
                    error_message TEXT,
                    usuario_id INTEGER,
                    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (id_farm) REFERENCES fazendas(id_farm)
                )
            """
        else:
            sql = """
                CREATE TABLE silver.uploads (
                    upload_id VARCHAR(36) PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    id_farm INTEGER NOT NULL REFERENCES silver.fazendas(id_farm),
                    fonte_origem VARCHAR(50) NOT NULL,
                    arquivo_nome_original VARCHAR(255),
                    total_registros INTEGER DEFAULT 0,
                    rows_inserted INTEGER DEFAULT 0,
                    rows_updated INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'processing',
                    error_message TEXT,
                    usuario_id INTEGER REFERENCES silver.usuarios(id),
                    data_upload TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP
                )
            """
        
        conn.execute(text(sql))
        conn.commit()
        
        # Adiciona upload_id à tabela animais se não existir
        if is_sqlite:
            result = conn.execute(text("PRAGMA table_info(animais)"))
            cols = [row[1] for row in result.fetchall()]
        else:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'animais' AND table_schema = 'silver'
            """))
            cols = [row[0] for row in result.fetchall()]
        
        if "upload_id" not in cols:
            if is_sqlite:
                conn.execute(text("ALTER TABLE animais ADD COLUMN upload_id TEXT"))
            else:
                conn.execute(text("ALTER TABLE silver.animais ADD COLUMN upload_id VARCHAR(36)"))
            conn.commit()
            print("Coluna upload_id adicionada à tabela animais.")
        
        print("Tabela uploads criada com sucesso!")


if __name__ == "__main__":
    migrate()