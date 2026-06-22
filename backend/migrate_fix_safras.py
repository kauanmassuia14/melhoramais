"""
Migração corrigida: Recalcula safras e resolve conflitos de chaves duplicadas.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)


def calcular_safra(nascimento_date):
    if nascimento_date is None:
        return None
    if nascimento_date.month < 7:
        return nascimento_date.year - 1
    else:
        return nascimento_date.year


def run_migration():
    engine = create_engine(raw_db_url)

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Busca todas as avaliações genéticas com nascimento
            evals = conn.execute(text("""
                SELECT ge.id, ge.safra as safra_atual, ge.animal_id, ge.fonte_origem, a.nascimento
                FROM genetics.genetic_evaluations ge
                JOIN genetics.animals a ON ge.animal_id = a.id
                WHERE a.nascimento IS NOT NULL
            """)).fetchall()

            print(f"Total de avaliações com nascimento: {len(evals)}")

            corrected = 0
            duplicates_removed = 0
            
            for eval_id, safra_atual, animal_id, fonte_origem, nascimento in evals:
                safra_correta = calcular_safra(nascimento)
                if safra_correta is None or safra_correta == safra_atual:
                    continue

                # Verifica se já existe um registro com a chave destino (animal_id, safra_correta, fonte_origem)
                conflict = conn.execute(text("""
                    SELECT id FROM genetics.genetic_evaluations
                    WHERE animal_id = :animal_id 
                      AND safra = :safra 
                      AND fonte_origem = :fonte_origem
                      AND id != :id
                """), {
                    "animal_id": animal_id,
                    "safra": safra_correta,
                    "fonte_origem": fonte_origem,
                    "id": eval_id
                }).fetchone()

                if conflict:
                    # Conflito detectado: Já existe o registro correto. Remove o duplicado (com safra errada).
                    conn.execute(text("""
                        DELETE FROM genetics.genetic_evaluations WHERE id = :id
                    """), {"id": eval_id})
                    duplicates_removed += 1
                else:
                    # Sem conflito: Atualiza a safra para o ano correto.
                    conn.execute(text("""
                        UPDATE genetics.genetic_evaluations 
                        SET safra = :safra 
                        WHERE id = :id
                    """), {"safra": safra_correta, "id": eval_id})
                    corrected += 1

            trans.commit()
            print(f"\n✅ Sucesso!")
            print(f"  - {corrected} avaliações atualizadas para a safra pecuária correta.")
            print(f"  - {duplicates_removed} avaliações duplicadas removidas.")

        except Exception as e:
            trans.rollback()
            print(f"\n❌ Erro durante a migração: {e}")
            raise

if __name__ == "__main__":
    run_migration()
