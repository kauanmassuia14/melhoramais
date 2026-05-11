"""
Run PMGZ migration endpoint
"""
from fastapi import APIRouter
from backend.database import engine
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

new_columns = [
    ("pmg_serie_rgd", "VARCHAR(50)"),
    ("pmg_p_percent", "DOUBLE PRECISION"),
    ("pmg_f_percent", "DOUBLE PRECISION"),
    ("pai_nome", "VARCHAR(255)"),
    ("pai_serie_rgd", "VARCHAR(50)"),
    ("mae_nome", "VARCHAR(255)"),
    ("mae_serie_rgd", "VARCHAR(50)"),
    ("pmg_pn_dep", "DOUBLE PRECISION"),
    ("pmg_pn_ac", "DOUBLE PRECISION"),
    ("pmg_pn_deca", "VARCHAR(10)"),
    ("pmg_pn_p_percent", "DOUBLE PRECISION"),
    ("pmg_pd_dep", "DOUBLE PRECISION"),
    ("pmg_pd_ac", "DOUBLE PRECISION"),
    ("pmg_pd_deca", "VARCHAR(10)"),
    ("pmg_pd_p_percent", "DOUBLE PRECISION"),
    ("pmg_pa_dep", "DOUBLE PRECISION"),
    ("pmg_pa_ac", "DOUBLE PRECISION"),
    ("pmg_pa_deca", "VARCHAR(10)"),
    ("pmg_pa_p_percent", "DOUBLE PRECISION"),
    ("pmg_ps_dep", "DOUBLE PRECISION"),
    ("pmg_ps_ac", "DOUBLE PRECISION"),
    ("pmg_ps_deca", "VARCHAR(10)"),
    ("pmg_ps_p_percent", "DOUBLE PRECISION"),
    ("pmg_pm_dep", "DOUBLE PRECISION"),
    ("pmg_pm_ac", "DOUBLE PRECISION"),
    ("pmg_pm_deca", "VARCHAR(10)"),
    ("pmg_pm_p_percent", "DOUBLE PRECISION"),
    ("pmg_ipp_dep", "DOUBLE PRECISION"),
    ("pmg_ipp_ac", "DOUBLE PRECISION"),
    ("pmg_ipp_deca", "VARCHAR(10)"),
    ("pmg_ipp_p_percent", "DOUBLE PRECISION"),
    ("pmg_stay_dep", "DOUBLE PRECISION"),
    ("pmg_stay_ac", "DOUBLE PRECISION"),
    ("pmg_stay_deca", "VARCHAR(10)"),
    ("pmg_stay_p_percent", "DOUBLE PRECISION"),
    ("pmg_pe365_dep", "DOUBLE PRECISION"),
    ("pmg_pe365_ac", "DOUBLE PRECISION"),
    ("pmg_pe365_deca", "VARCHAR(10)"),
    ("pmg_pe365_p_percent", "DOUBLE PRECISION"),
    ("pmg_psn_dep", "DOUBLE PRECISION"),
    ("pmg_psn_ac", "DOUBLE PRECISION"),
    ("pmg_psn_deca", "VARCHAR(10)"),
    ("pmg_psn_p_percent", "DOUBLE PRECISION"),
    ("pmg_aol_dep", "DOUBLE PRECISION"),
    ("pmg_aol_ac", "DOUBLE PRECISION"),
    ("pmg_aol_deca", "VARCHAR(10)"),
    ("pmg_aol_p_percent", "DOUBLE PRECISION"),
    ("pmg_acab_dep", "DOUBLE PRECISION"),
    ("pmg_acab_ac", "DOUBLE PRECISION"),
    ("pmg_acab_deca", "VARCHAR(10)"),
    ("pmg_acab_p_percent", "DOUBLE PRECISION"),
    ("pmg_mar_dep", "DOUBLE PRECISION"),
    ("pmg_mar_ac", "DOUBLE PRECISION"),
    ("pmg_mar_deca", "VARCHAR(10)"),
    ("pmg_mar_p_percent", "DOUBLE PRECISION"),
    ("pmg_eg_dep", "DOUBLE PRECISION"),
    ("pmg_eg_ac", "DOUBLE PRECISION"),
    ("pmg_eg_deca", "VARCHAR(10)"),
    ("pmg_eg_p_percent", "DOUBLE PRECISION"),
    ("pmg_p_dep", "DOUBLE PRECISION"),
    ("pmg_p_ac", "DOUBLE PRECISION"),
    ("pmg_p_deca", "VARCHAR(10)"),
    ("pmg_p_p_percent", "DOUBLE PRECISION"),
    ("pmg_m_dep", "DOUBLE PRECISION"),
    ("pmg_m_ac", "DOUBLE PRECISION"),
    ("pmg_m_deca", "VARCHAR(10)"),
    ("pmg_m_p_percent", "DOUBLE PRECISION"),
    ("p120_peso_120", "DOUBLE PRECISION"),
    ("desc_p120_filhos", "INTEGER"),
    ("desc_p120_rebanhos", "INTEGER"),
    ("desc_p210_filhos", "INTEGER"),
    ("desc_p210_rebanhos", "INTEGER"),
    ("desc_p365_filhos", "INTEGER"),
    ("desc_p365_rebanhos", "INTEGER"),
    ("desc_p450_filhos", "INTEGER"),
    ("desc_p450_rebanhos", "INTEGER"),
    ("desc_p120_netosc", "INTEGER"),
    ("desc_p120_netosc_rebanhos", "INTEGER"),
    ("desc_p210_netosc", "INTEGER"),
    ("desc_p210_netosc_rebanhos", "INTEGER"),
    ("desc_pe365_filhos", "INTEGER"),
    ("desc_pe365_rebanhos", "INTEGER"),
    ("desc_stay_filhos", "INTEGER"),
    ("desc_stay_rebanhos", "INTEGER"),
    ("desc_ipp_filhos", "INTEGER"),
    ("desc_ipp_rebanhos", "INTEGER"),
    ("desc_aol_filhos", "INTEGER"),
    ("desc_aol_rebanhos", "INTEGER"),
    ("desc_acab_filhos", "INTEGER"),
    ("desc_acab_rebanhos", "INTEGER"),
    ("genotipado", "BOOLEAN"),
    ("csg", "BOOLEAN"),
    ("processing_log_id", "INTEGER"),
]

@router.post("/admin/migrate-pmgz")
def run_pmgz_migration():
    """Run PMGZ columns migration"""
    with engine.connect() as conn:
        for col_name, col_type in new_columns:
            try:
                result = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'animais' AND column_name = '{col_name}'
                """))
                if not result.fetchone():
                    conn.execute(text(f"""
                        ALTER TABLE silver.animais ADD COLUMN {col_name} {col_type}
                    """))
                    logger.info(f"Added: {col_name}")
                else:
                    logger.info(f"Exists: {col_name}")
            except Exception as e:
                logger.error(f"Error {col_name}: {e}")
        conn.commit()
    
    return {"status": "success", "columns_added": len(new_columns)}


@router.post("/admin/fix-sequences")
def fix_sequences():
    """Fix database sequences and add missing columns for v2 schema"""
    try:
        with engine.connect() as conn:
            # 1. Fix sequences
            conn.execute(text("""
                SELECT setval('genetics.notifications_id_seq', COALESCE((SELECT MAX(id) FROM genetics.notifications), 1) + 100);
            """))
            
            # 2. Add missing columns to genetic_evaluations (Unified v2)
            eval_cols = [
                ("indice_principal", "NUMERIC(10,4)"),
                ("rank_principal", "INTEGER"),
                ("percentil_principal", "NUMERIC(10,4)"),
                ("metrics", "JSONB"),
                ("progeny_stats", "JSONB"),
                ("phenotypes", "JSONB"),
                ("upload_id", "VARCHAR(36)"),
                ("fonte_origem", "VARCHAR(50)")
            ]
            
            for col_name, col_type in eval_cols:
                try:
                    # PostgreSQL check if column exists
                    res = conn.execute(text(f"""
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_schema = 'genetics' 
                        AND table_name = 'genetic_evaluations' 
                        AND column_name = '{col_name}'
                    """)).fetchone()
                    
                    if not res:
                        conn.execute(text(f"ALTER TABLE genetics.genetic_evaluations ADD COLUMN {col_name} {col_type}"))
                        logger.info(f"Migration: added {col_name} to genetic_evaluations")
                except Exception as e:
                    logger.warning(f"Skipping col {col_name}: {e}")

            # 3. Add unique constraint for upserts if not exists
            try:
                conn.execute(text("""
                    DO $$ 
                    BEGIN 
                        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uix_animal_safra_fonte') THEN
                            ALTER TABLE genetics.genetic_evaluations 
                            ADD CONSTRAINT uix_animal_safra_fonte UNIQUE (animal_id, safra, fonte_origem);
                        END IF;
                    END $$;
                """))
                logger.info("Migration: added unique constraint uix_animal_safra_fonte")
            except Exception as e:
                logger.warning(f"Could not add constraint: {e}")

            conn.commit()
        return {"status": "success", "message": "Sequences, Schema and Constraints synchronized successfully"}
    except Exception as e:
        logger.error(f"Error fixing sequences: {e}")
        return {"status": "error", "message": str(e)}


def run_migration_on_startup():
    """Run migration automatically on startup"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with engine.connect() as conn:
            for col_name, col_type in new_columns:
                try:
                    result = conn.execute(text(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'animais' AND column_name = '{col_name}'
                    """))
                    if not result.fetchone():
                        conn.execute(text(f"""
                            ALTER TABLE genetics.animais ADD COLUMN {col_name} {col_type}
                        """))
                        logger.info(f"[MIGRATION] Added column: {col_name}")
                    else:
                        logger.info(f"[MIGRATION] Exists: {col_name}")
                except Exception as e:
                    logger.error(f"[MIGRATION] Error {col_name}: {e}")
            conn.commit()
        logger.info("[MIGRATION] PMGZ columns migration completed!")
    except Exception as e:
        logger.warning(f"[MIGRATION] Could not run: {e}")