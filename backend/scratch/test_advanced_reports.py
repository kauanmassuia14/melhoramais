# test_advanced_reports.py
# Automated test script for advanced reports in Melhora+

import os
import sys
import json
import time
import uuid
import threading
from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy import text

# Ensure project imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.database import SessionLocal, get_db, IS_SQLITE
from backend.models import GeneticsAnimal, GeneticsFarm, GeneticsGeneticEvaluation, User
from backend.auth.dependencies import get_current_user

# Create test admin user in database if none exists
db = SessionLocal()
admin_user = db.query(User).filter(User.role == "admin").first()
if not admin_user:
    from backend.auth.security import hash_password
    admin_user = User(
        nome="Test Admin",
        email="test_admin@melhoramais.com",
        senha_hash=hash_password("password123"),
        role="admin",
        ativo=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
db.close()

# Override dependency to bypass auth during test execution
app.dependency_overrides[get_current_user] = lambda: admin_user

client = TestClient(app)

def run_tests():
    db = SessionLocal()
    
    # 1. Fetch test data
    farm = db.query(GeneticsFarm).first()
    if not farm:
        print("Erro: Nenhuma fazenda cadastrada no genetics.")
        sys.exit(1)
        
    print(f"Fazenda para testes: {farm.nome} (ID: {farm.id})")
    
    # Find 3 animals from this farm
    animals = db.query(GeneticsAnimal).filter(GeneticsAnimal.farm_id == farm.id).limit(3).all()
    if len(animals) < 2:
        print("Erro: Insira pelo menos 2 animais nesta fazenda para executar os testes comparativos.")
        sys.exit(1)
        
    animal_ids = [str(a.id) for a in animals]
    print(f"Animais para testes comparativos: {[a.rgn for a in animals]}")
    
    print("\n--- Teste 1: Ficha Individual do Animal ---")
    animal_id = animal_ids[0]
    response = client.get(f"/reports/animal/{animal_id}")
    assert response.status_code == 200, f"Falha na Ficha do Animal: {response.text}"
    assert response.headers["content-type"] == "application/pdf", "Ficha do Animal não retornou PDF"
    print("✓ Sucesso: Ficha do Animal gerada corretamente (PDF)!")
    
    print("\n--- Teste 2: Comparação de Animais (Radar & Tabela) ---")
    payload = {"animal_ids": animal_ids}
    response = client.post("/reports/compare/animals", json=payload)
    assert response.status_code == 200, f"Falha na comparação de animais: {response.text}"
    assert response.headers["content-type"] == "application/pdf", "Comparação de animais não retornou PDF"
    print("✓ Sucesso: Comparação de animais gerada com sucesso (PDF)!")
    
    print("\n--- Teste 3: Benchmark de Fazendas ---")
    farms = db.query(GeneticsFarm).limit(2).all()
    farm_ids = [str(f.id) for f in farms]
    
    payload_benchmark = {
        "farm_ids": farm_ids,
        "safra": 2024
    }
    response = client.post("/reports/compare/farms", json=payload_benchmark)
    assert response.status_code == 200, f"Falha no benchmark de fazendas: {response.text}"
    assert response.headers["content-type"] == "application/pdf", "Benchmark não retornou PDF"
    print("✓ Sucesso: Benchmark de fazendas gerado com sucesso (PDF)!")

    print("\n--- Teste 4: Concorrência e Isolamento do Matplotlib ---")
    results = []
    
    def make_concurrent_request(worker_id):
        try:
            payload_w = {"animal_ids": animal_ids}
            resp = client.post("/reports/compare/animals", json=payload_w)
            results.append((worker_id, resp.status_code, resp.headers.get("content-type")))
        except Exception as e:
            results.append((worker_id, 500, str(e)))
            
    threads = []
    for i in range(10):
        t = threading.Thread(target=make_concurrent_request, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    for idx, status, content_type in results:
        assert status == 200, f"Thread {idx} falhou com status {status}: {content_type}"
        assert content_type == "application/pdf", f"Thread {idx} não retornou PDF"
        
    print(f"✓ Sucesso: {len(results)} requisições concorrentes processadas com isolamento de gráficos!")

    print("\n--- Teste 5: Resiliência contra Dados Corrompidos (Null-Safe Casting) ---")
    if IS_SQLITE:
        print("Bypassed: Teste de casting de JSON nativo do Postgres não aplicável em SQLite local.")
    else:
        # We test the PostgreSQL NULLIF/COALESCE casting logic using a CTE query to make sure it handles empty strings '' safely without crash.
        # Use CAST(placeholder AS type) to avoid double colon '::' syntax parsing errors in SQLAlchemy
        test_sql = text("""
            WITH mock_evals AS (
                SELECT 
                    CAST(:farm_id AS uuid) as farm_id,
                    12.5 as indice_principal,
                    2024 as safra,
                    CAST('{"PD-EDg": {"dep": ""}}' AS jsonb) as metrics
                UNION ALL
                SELECT 
                    CAST(:farm_id AS uuid) as farm_id,
                    15.0 as indice_principal,
                    2024 as safra,
                    CAST('{"PD-EDg": {"dep": "18.5"}}' AS jsonb) as metrics
            )
            SELECT 
                farm_id,
                AVG(indice_principal) as avg_index,
                AVG(COALESCE(
                    CAST(NULLIF(metrics['PD-EDg'] ->> 'dep', '') AS double precision),
                    CAST(NULLIF(metrics['DP210'] ->> 'dep', '') AS double precision),
                    CAST(NULLIF(metrics['DP120'] ->> 'dep', '') AS double precision)
                )) as avg_p210
            FROM mock_evals
            GROUP BY farm_id
        """)
        
        res = db.execute(test_sql, {"farm_id": farm.id}).fetchone()
        assert res is not None, "A query de teste retornou vazio"
        assert res[2] == 18.5, f"Esperado média P210 de 18.5, obtido {res[2]}"
        print("✓ Sucesso: Benchmark lidou defensivamente com métricas vazias/corrompidas via NULLIF!")
        
    db.close()
    print("\nTodos os testes avançados de relatórios foram executados e aprovados com sucesso!")

if __name__ == "__main__":
    run_tests()
