from sqlalchemy import create_engine, text
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Neon database URL from the summary
NEON_DATABASE_URL = "postgresql://neondb_owner:npg_OHiFUPo9X0le@ep-cool-resonance-acsa3yku.sa-east-1.aws.neon.tech/neondb?sslmode=require"

# Admin user details
ADMIN_EMAIL = "kauan.massuia@sou.inteli.edu.br"
ADMIN_PASSWORD_HASH = "$2b$12$RFRtOizTJsfSeczrpvlKROLef5bSTfwWHee8Su9UxD4BQvnjh3EzK"
ADMIN_NAME = "Melhoramais"
ADMIN_FARM_ID = 1
ADMIN_ROLE = "admin"
ADMIN_ATIVO = True
CREATED_AT = datetime.now()

def create_admin_user():
    """Create admin user on Neon database if not exists."""
    engine = create_engine(NEON_DATABASE_URL)
    
    try:
        with engine.begin() as conn:
            # 1. Ensure farm exists in genetics schema
            ADMIN_FARM_ID = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
            res = conn.execute(
                text("SELECT id FROM genetics.farms WHERE id = :id"),
                {"id": ADMIN_FARM_ID}
            ).first()
            
            if not res:
                print(f"Creating admin farm {ADMIN_FARM_ID}...")
                conn.execute(
                    text("INSERT INTO genetics.farms (id, nome, documento) VALUES (:id, :nome, :doc)"),
                    {"id": ADMIN_FARM_ID, "nome": "Fazenda Matriz", "doc": "00.000.000/0001-00"}
                )

            # 2. Ensure user exists in genetics schema
            senha_hash = pwd_context.hash("admin123")
            res = conn.execute(
                text("SELECT id FROM genetics.users WHERE email = :email"),
                {"email": "kauan.massuia@sou.inteli.edu.br"}
            ).first()

            if not res:
                print("Creating admin user in genetics.users...")
                conn.execute(
                    text("""
                        INSERT INTO genetics.users (email, senha_hash, nome, id_farm, role, ativo)
                        VALUES (:email, :hash, :nome, :farm, :role, :ativo)
                    """),
                    {
                        "email": "kauan.massuia@sou.inteli.edu.br",
                        "hash": senha_hash,
                        "nome": "Kauan Admin",
                        "farm": ADMIN_FARM_ID,
                        "role": "admin",
                        "ativo": True
                    }
                )
            else:
                print("Admin user already exists. Updating farm and status...")
                conn.execute(
                    text("UPDATE genetics.users SET id_farm = :farm, ativo = True, role = 'admin' WHERE email = :email"),
                    {"farm": ADMIN_FARM_ID, "email": "kauan.massuia@sou.inteli.edu.br"}
                )
            
            print("Success! Admin user and farm are ready in 'genetics' schema.")
            return True
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return None

if __name__ == "__main__":
    print("Creating admin user on Neon database...")
    user_id = create_admin_user()
    if user_id:
        print("✅ Admin user created/verified successfully")
    else:
        print("❌ Failed to create admin user")