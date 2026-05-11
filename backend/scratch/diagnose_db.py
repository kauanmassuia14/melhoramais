import sys
import os

# Adiciona o diretório raiz ao path para importar os módulos do backend
sys.path.append(os.getcwd())

from backend.database import SessionLocal, engine
from backend.models import Animal, GeneticsAnimal, Upload, User, GeneticsFarm
from sqlalchemy import text

def diagnose():
    db = SessionLocal()
    try:
        print("=== DIAGNÓSTICO DE BANCO DE DADOS ===\n")
        
        # 1. Verificar contagem nas tabelas
        legacy_count = db.query(Animal).count()
        new_count = db.query(GeneticsAnimal).count()
        
        print(f"Tabela Legada (genetics.animais): {legacy_count} registros")
        print(f"Tabela Nova (genetics.animals): {new_count} registros")
        
        # 2. Verificar uploads recentes
        print("\n--- Últimos 5 Uploads ---")
        recent_uploads = db.query(Upload).order_by(Upload.data_upload.desc()).limit(5).all()
        for u in recent_uploads:
            print(f"ID: {u.upload_id} | Nome: {u.nome} | Status: {u.status}")
            print(f"   - Total no arquivo: {u.total_registros}")
            print(f"   - Inseridos: {u.rows_inserted} | Atualizados: {u.rows_updated}")
            print(f"   - Fazenda ID: {u.id_farm}")
            print(f"   - Data: {u.data_upload}")
            print("-" * 30)

        # 3. Verificar usuários e suas fazendas
        print("\n--- Usuários e Vínculos ---")
        users = db.query(User).all()
        for user in users:
            print(f"Usuário: {user.nome} ({user.email})")
            print(f"   - id_farm (no User): {user.id_farm} (Tipo: {type(user.id_farm)})")
            
            # Tentar achar a fazenda no schema novo
            try:
                import uuid
                farm_uuid = uuid.UUID(str(user.id_farm))
                farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
                if farm:
                    print(f"   - Fazenda Encontrada (Nova): {farm.nome}")
                else:
                    print(f"   - [AVISO] Fazenda não encontrada no schema novo (genetics.farms)")
            except:
                print(f"   - [ERRO] id_farm não é um UUID válido.")
            print("-" * 30)

        # 4. Verificar se há animais órfãos (sem upload_id ou farm_id inválido)
        orphan_count = db.query(GeneticsAnimal).filter(GeneticsAnimal.upload_id == None).count()
        if orphan_count > 0:
            print(f"\nAviso: Existem {orphan_count} animais na tabela nova sem vínculo de upload_id.")

    except Exception as e:
        print(f"\nErro durante o diagnóstico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    diagnose()
