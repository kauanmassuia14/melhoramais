# perf_test.py
# Script de verificação de performance para o endpoint de relatórios.
# Mede número de queries, consumo de memória e uso de índice funcional (EXPLAIN ANALYZE).

import os
import sys
import resource
import time
from sqlalchemy import create_engine, event, text, and_, func
from sqlalchemy.orm import sessionmaker, load_only, aliased
from dotenv import load_dotenv

# Garantir imports do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import get_max_completed_safra, IS_SQLITE
from backend.models import GeneticsAnimal, GeneticsGeneticEvaluation, GeneticsFarm

load_dotenv()

from sqlalchemy.engine import Engine

# Contador de queries executadas no motor do SQLAlchemy
query_count = 0

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    global query_count
    query_count += 1

def run_performance_test():
    global query_count
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Erro: DATABASE_URL não definida no ambiente.")
        sys.exit(1)
        
    print(f"Conectando ao banco de dados...")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # 1. Obter a fazenda Fazenda Camparino (com 31k+ animais)
    farm = db.query(GeneticsFarm).filter(GeneticsFarm.nome.ilike("%Camparino%")).first()
    if not farm:
        print("Erro: Fazenda de teste não encontrada.")
        sys.exit(1)
        
    print(f"Fazenda selecionada: {farm.nome} (ID: {farm.id})")
    
    # Medir memória inicial
    mem_start = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    
    # Resetar contador de queries
    query_count = 0
    start_time = time.time()
    
    # 2. Configurar timeout no banco
    if not IS_SQLITE:
        db.execute(text("SET statement_timeout = 10000"))
        
    max_safra = get_max_completed_safra()
    limit = 500
    min_p210 = 5.0
    max_p210 = 25.0
    valid_platforms = ["ANCP", "PMGZ"]
    
    print("\n--- Executando Queries de Otimização ---")
    
    # query de animais otimizada
    query = db.query(GeneticsAnimal).filter(GeneticsAnimal.farm_id == farm.id)
    
    # EXISTS Plataforma
    query = query.filter(
        db.query(GeneticsGeneticEvaluation.id)
        .filter(
            GeneticsGeneticEvaluation.animal_id == GeneticsAnimal.id,
            GeneticsGeneticEvaluation.fonte_origem.in_(valid_platforms),
            GeneticsGeneticEvaluation.safra <= max_safra
        ).exists()
    )
    
    # EXISTS Peso com Coalesce no JSON de métricas
    latest_safra_sub = db.query(func.max(GeneticsGeneticEvaluation.safra))\
                         .filter(
                             GeneticsGeneticEvaluation.animal_id == GeneticsAnimal.id,
                             GeneticsGeneticEvaluation.safra <= max_safra
                         ).correlate(GeneticsAnimal).scalar_subquery()

    pd_edg_val = GeneticsGeneticEvaluation.metrics['PD-EDg']['dep'].as_float()
    dp210_val = GeneticsGeneticEvaluation.metrics['DP210']['dep'].as_float()
    dp120_val = GeneticsGeneticEvaluation.metrics['DP120']['dep'].as_float()
    pd_val = func.coalesce(pd_edg_val, dp210_val, dp120_val)

    weight_exists = db.query(GeneticsGeneticEvaluation.id).filter(
        GeneticsGeneticEvaluation.animal_id == GeneticsAnimal.id,
        GeneticsGeneticEvaluation.safra == latest_safra_sub
    )
    
    weight_exists = weight_exists.filter(pd_val >= min_p210)
    weight_exists = weight_exists.filter(pd_val <= max_p210)
    
    query = query.filter(weight_exists.exists())
    
    # Otimizações ORM
    query = query.options(load_only(
        GeneticsAnimal.id,
        GeneticsAnimal.rgn,
        GeneticsAnimal.nome,
        GeneticsAnimal.sexo,
        GeneticsAnimal.nascimento,
        GeneticsAnimal.genotipado
    ))
    
    # Executar query principal
    animals = query.limit(limit).all()
    print(f"Animais encontrados: {len(animals)}")
    
    # Executar query em lote com window function
    animal_ids = [a.id for a in animals]
    eval_map = {}
    
    if animal_ids:
        row_num_col = func.row_number().over(
            partition_by=GeneticsGeneticEvaluation.animal_id,
            order_by=(GeneticsGeneticEvaluation.safra.desc(), GeneticsGeneticEvaluation.created_at.desc())
        ).label("row_num")
        
        subq = db.query(
            GeneticsGeneticEvaluation.id.label("eval_id"),
            row_num_col
        ).filter(
            GeneticsGeneticEvaluation.animal_id.in_(animal_ids),
            GeneticsGeneticEvaluation.safra <= max_safra
        ).subquery()
        
        latest_evals = db.query(GeneticsGeneticEvaluation).join(
            subq,
            and_(
                GeneticsGeneticEvaluation.id == subq.c.eval_id,
                subq.c.row_num == 1
            )
        ).all()
        
        for ev in latest_evals:
            eval_map[ev.animal_id] = ev
            
    duration = time.time() - start_time
    mem_end = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    mem_diff_kb = mem_end - mem_start
    
    print("\n=== MÉTRICAS DE PERFORMANCE ===")
    print(f"Tempo total de execução: {duration:.4f} segundos")
    print(f"Quantidade total de queries: {query_count}")
    print(f"Uso de memória pico (RSS): {mem_end / 1024:.2f} MB")
    print(f"Aumento de memória nesta transação: {mem_diff_kb / 1024:.2f} MB")
    
    # Validações estritas de assertiva
    assert len(animals) > 0, "Deveria ter encontrado animais!"
    assert query_count <= 4, f"Erro: Foram feitas {query_count} queries (esperado <= 4)!"
    print("✓ Sucesso: Quantidade de queries dentro do limite fixo O(1)!")
    
    # 3. EXPLAIN ANALYZE no PostgreSQL para validar uso do Índice Funcional
    if not IS_SQLITE:
        print("\n--- Analisando Plano de Execução do PostgreSQL (EXPLAIN ANALYZE) ---")
        # Obter o SQL cru compilado do SQLAlchemy
        from sqlalchemy.dialects import postgresql
        compiled = query.statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
        sql_statement = str(compiled)
        
        explain_query = f"EXPLAIN ANALYZE {sql_statement}"
        explain_rows = db.execute(text(explain_query)).fetchall()
        plan = "\n".join([r[0] for r in explain_rows])
        
        # Salvar plano de execução em arquivo para fins de auditoria
        with open("backend/scratch/explain_plan.txt", "w") as f:
            f.write(plan)
            
        print("Plano de execução salvo em backend/scratch/explain_plan.txt")
        
        # Verificar o uso do índice funcional
        use_index = "idx_eval_metrics_pd_dep_float" in plan
        has_seq_scan = "Seq Scan on genetic_evaluations" in plan
        
        print(f"Contém índice funcional 'idx_eval_metrics_pd_dep_float'? {'SIM' if use_index else 'NÃO'}")
        print(f"Contém Seq Scan na tabela de avaliações? {'SIM' if has_seq_scan else 'NÃO'}")
        
        # Assertiva de performance do banco de dados
        assert use_index, "Erro: O planejador de query não utilizou o índice funcional idx_eval_metrics_pd_dep_float!"
        assert not has_seq_scan, "Erro: Foi detectado Seq Scan na tabela genetic_evaluations!"
        print("✓ Sucesso: O banco de dados está utilizando o Índice Funcional por expressão de forma otimizada (Index Scan)!")

    print("\nTodas as validações de performance foram aprovadas com sucesso!")
    db.close()

if __name__ == "__main__":
    run_performance_test()
