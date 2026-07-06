from backend.auth.security import hash_password
from backend.database import SessionLocal
from backend.models import User

def reset_admin_password(new_password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin@melhoramais.com").first()
        if not user:
            print("Usuário admin@melhoramais.com não encontrado!")
            return
        user.senha_hash = hash_password(new_password)
        db.commit()
        print("Senha do admin atualizada com sucesso!")
    except Exception as e:
        db.rollback()
        print(f"Erro ao atualizar senha: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password("10072003Kauan@")
