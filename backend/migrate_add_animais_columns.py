"""
Migração para adicionar novas colunas à tabela animais
Executar: python -m backend.migrate_add_animal_columns
"""
from sqlalchemy import text, inspect
from backend.database import engine, SessionLocal
from backend.models import Base


def migrate():
    """Adiciona todas as novas colunas à tabela animais."""
    
    # Colunas a adicionar (não interfere se já existirem)
    new_columns = [
        # Genealogy - 2ª geração
        ("avo_paterno_rgn", "VARCHAR(50)"),
        ("avo_paterno_mae_rgn", "VARCHAR(50)"),
        ("avo_materno_rgn", "VARCHAR(50)"),
        ("avo_materno_mae_rgn", "VARCHAR(50)"),
        
        # Genealogy - 3ª geração
        ("bisavo_paterno_pai_rgn", "VARCHAR(50)"),
        ("bisavo_paterno_mae_pai_rgn", "VARCHAR(50)"),
        ("bisavo_materno_pai_rgn", "VARCHAR(50)"),
        ("bisavo_materno_mae_pai_rgn", "VARCHAR(50)"),
        ("bisavo_paterno_mae_rgn", "VARCHAR(50)"),
        ("bisavo_paterno_mae_mae_rgn", "VARCHAR(50)"),
        ("bisavo_materno_mae_rgn", "VARCHAR(50)"),
        ("bisavo_materno_mae_mae_rgn", "VARCHAR(50)"),
        
        # Genealogy - 4ª geração
        ("trisavo_paterno_pai_rgn", "VARCHAR(50)"),
        ("trisavo_paterno_mae_pai_rgn", "VARCHAR(50)"),
        ("trisavo_materno_pai_rgn", "VARCHAR(50)"),
        ("trisavo_materno_mae_pai_rgn", "VARCHAR(50)"),
        ("trisavo_paterno_mae_rgn", "VARCHAR(50)"),
        ("trisavo_paterno_mae_mae_rgn", "VARCHAR(50)"),
        ("trisavo_materno_mae_rgn", "VARCHAR(50)"),
        ("trisavo_materno_mae_mae_rgn", "VARCHAR(50)"),
        
        # Pesos adicionais
        ("peso_nascimento", "FLOAT"),
        ("peso_final", "FLOAT"),
        
        # Medidas
        ("altura", "FLOAT"),
        ("circumference", "FLOAT"),
        
        # Reprodução
        ("intervalo_partos", "FLOAT"),
        ("dias_gestacao", "FLOAT"),
        
        # ANCP - DEP Individuais
        ("anc_dipp", "FLOAT"),
        ("anc_d3p", "FLOAT"),
        ("anc_dstay", "FLOAT"),
        ("anc_dpn", "FLOAT"),
        ("anc_dp12", "FLOAT"),
        ("anc_dpe", "FLOAT"),
        ("anc_daol", "FLOAT"),
        ("anc_dacab", "FLOAT"),
        
        # ANCP - AC
        ("anc_ac_mg", "FLOAT"),
        ("anc_ac_te", "FLOAT"),
        ("anc_ac_m", "FLOAT"),
        ("anc_ac_p", "FLOAT"),
        
        # GENEPLUS - DEP
        ("gen_pn", "FLOAT"),
        ("gen_p120", "FLOAT"),
        ("gen_tmd", "FLOAT"),
        ("gen_pd", "FLOAT"),
        ("gen_tm120", "FLOAT"),
        ("gen_ps", "FLOAT"),
        ("gen_gpd", "FLOAT"),
        ("gen_cfd", "FLOAT"),
        ("gen_cfs", "FLOAT"),
        ("gen_hp_stay", "FLOAT"),
        ("gen_rd", "FLOAT"),
        ("gen_egs", "FLOAT"),
        ("gen_acab", "FLOAT"),
        ("gen_mar", "FLOAT"),
        
        # GENEPLUS - AC
        ("gen_ac_iqg", "FLOAT"),
        ("gen_ac_pmm", "FLOAT"),
        ("gen_ac_p", "FLOAT"),
        
        # PMGZ - DEP
        ("pmg_pn", "FLOAT"),
        ("pmg_pa", "FLOAT"),
        ("pmg_ps", "FLOAT"),
        ("pmg_pm", "FLOAT"),
        ("pmg_ipp", "FLOAT"),
        ("pmg_stay", "FLOAT"),
        ("pmg_pe", "FLOAT"),
        ("pmg_aol", "FLOAT"),
        ("pmg_acab", "FLOAT"),
        ("pmg_mar", "FLOAT"),
        
        # PMGZ - DECA
        ("pmg_deca", "VARCHAR(10)"),
        ("pmg_deca_pn", "VARCHAR(10)"),
        ("pmg_deca_p12", "VARCHAR(10)"),
        ("pmg_deca_ps", "VARCHAR(10)"),
        ("pmg_deca_stay", "VARCHAR(10)"),
        ("pmg_deca_pe", "VARCHAR(10)"),
        ("pmg_deca_aol", "VARCHAR(10)"),
        
        # PMGZ - Metas
        ("pmg_meta_p", "FLOAT"),
        ("pmg_meta_m", "FLOAT"),
        ("pmg_meta_t", "FLOAT"),
        
        # PMGZ - AC
        ("pmg_ac_iabc", "FLOAT"),
        ("pmg_ac_p", "FLOAT"),
        ("pmg_ac_m", "FLOAT"),
    ]
    
    db_url = str(engine.url)
    is_sqlite = db_url.startswith("sqlite")
    
    with engine.connect() as conn:
        # Pega as colunas existentes
        if is_sqlite:
            result = conn.execute(text("PRAGMA table_info(animais)"))
            existing_cols = [row[1] for row in result.fetchall()]
        else:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'animais' AND table_schema = 'silver'
            """))
            existing_cols = [row[0] for row in result.fetchall()]
        
        print(f"Colunas existentes: {len(existing_cols)}")
        
        # Adiciona cada coluna que não existe
        added = 0
        for col_name, col_type in new_columns:
            if col_name not in existing_cols:
                if is_sqlite:
                    sql = f"ALTER TABLE animais ADD COLUMN {col_name} {col_type}"
                else:
                    sql = f"ALTER TABLE silver.animais ADD COLUMN {col_name} {col_type}"
                
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"  + Adicionado: {col_name}")
                    added += 1
                except Exception as e:
                    print(f"  ! Erro ao adicionar {col_name}: {e}")
            else:
                print(f"    Já existe: {col_name}")
        
        print(f"\nMigração concluída: {added} novas colunas adicionadas.")


if __name__ == "__main__":
    migrate()