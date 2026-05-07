
import sys
import os
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório raiz ao path para importar os módulos do backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import DATABASE_URL, engine
from backend.models import Base, User, Notification, GeneticsFarm

def migrate():
    print("🚀 Iniciando migração de usuários para o schema genetics...")
    
    # 1. Garantir que o schema genetics existe
    with engine.connect() as conn:
        print("📁 Garantindo existência do schema genetics...")
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS genetics"))
        conn.commit()

    # 2. Criar as tabelas no schema genetics (usando os novos modelos)
    print("🛠 Criando novas tabelas (users, notifications)...")
    Base.metadata.create_all(bind=engine, tables=[User.__table__, Notification.__table__])
    
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 3. Buscar usuários antigos
        print("🔍 Buscando usuários em silver.usuarios...")
        old_users = session.execute(text("SELECT id, nome, email, senha_hash, id_farm, role, ativo, ultimo_login, created_at FROM silver.usuarios")).fetchall()
        
        if not old_users:
            print("ℹ️ Nenhum usuário encontrado em silver.usuarios.")
        else:
            print(f"📦 Migrando {len(old_users)} usuários...")
            for old_u in old_users:
                # Tentar encontrar a fazenda correspondente no genetics
                new_farm_id = None
                if old_u.id_farm:
                    # Buscar nome da fazenda antiga
                    old_farm_name = session.execute(
                        text("SELECT nome_farm FROM silver.fazendas WHERE id_farm = :id"),
                        {"id": old_u.id_farm}
                    ).scalar()
                    
                    if old_farm_name:
                        # Buscar UUID da fazenda no genetics pelo nome
                        new_farm_id = session.execute(
                            text("SELECT id FROM genetics.farms WHERE nome = :nome"),
                            {"nome": old_farm_name}
                        ).scalar()
                        
                        if new_farm_id:
                            new_farm_id = str(new_farm_id)
                
                # Inserir no novo schema
                # Verificamos se já existe para evitar duplicatas
                exists = session.execute(
                    text("SELECT id FROM genetics.users WHERE email = :email"),
                    {"email": old_u.email}
                ).scalar()
                
                if not exists:
                    session.execute(
                        text("""
                            INSERT INTO genetics.users (id, nome, email, senha_hash, id_farm, role, ativo, ultimo_login, created_at)
                            VALUES (:id, :nome, :email, :senha_hash, :id_farm, :role, :ativo, :ultimo_login, :created_at)
                        """),
                        {
                            "id": old_u.id,
                            "nome": old_u.nome,
                            "email": old_u.email,
                            "senha_hash": old_u.senha_hash,
                            "id_farm": new_farm_id,
                            "role": old_u.role,
                            "ativo": old_u.ativo,
                            "ultimo_login": old_u.ultimo_login,
                            "created_at": old_u.created_at
                        }
                    )
            session.commit()
            print("✅ Usuários migrados com sucesso!")

        # 4. Migrar notificações
        print("🔍 Buscando notificações em silver.notifications...")
        try:
            old_notifications = session.execute(text("SELECT id, id_user, title, message, type, is_read, link, created_at FROM silver.notifications")).fetchall()
            if old_notifications:
                print(f"📦 Migrando {len(old_notifications)} notificações...")
                for old_n in old_notifications:
                    # Verificar se já existe
                    exists = session.execute(
                        text("SELECT id FROM genetics.notifications WHERE id = :id"),
                        {"id": old_n.id}
                    ).scalar()
                    
                    if not exists:
                        session.execute(
                            text("""
                                INSERT INTO genetics.notifications (id, id_user, title, message, type, is_read, link, created_at)
                                VALUES (:id, :id_user, :title, :message, :type, :is_read, :link, :created_at)
                            """),
                            {
                                "id": old_n.id,
                                "id_user": old_n.id_user,
                                "title": old_n.title,
                                "message": old_n.message,
                                "type": old_n.type,
                                "is_read": old_n.is_read,
                                "link": old_n.link,
                                "created_at": old_n.created_at
                            }
                        )
                session.commit()
                print("✅ Notificações migradas com sucesso!")
        except Exception as e:
            print(f"⚠️ Erro ao migrar notificações (pode ser que a tabela não exista): {e}")

        # 5. Opcional: Remover as tabelas antigas (EXCLUIR conforme solicitado)
        print("🗑 Removendo tabelas antigas do schema silver...")
        # session.execute(text("DROP TABLE IF EXISTS silver.notifications CASCADE"))
        # session.execute(text("DROP TABLE IF EXISTS silver.usuarios CASCADE"))
        # session.commit()
        print("ℹ️ DROP das tabelas comentado por segurança. Se tudo estiver OK, você pode rodar: DROP TABLE silver.usuarios, silver.notifications;")

    except Exception as e:
        session.rollback()
        print(f"❌ Erro durante a migração: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
