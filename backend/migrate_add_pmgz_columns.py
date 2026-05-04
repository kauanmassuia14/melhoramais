"""
Migration: Add PMGZ Cavafunda columns to existing animais table
"""
from backend.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

new_columns = [
    # ANIMAL - dados básicos
    ("pmg_serie_rgd", "VARCHAR(50)"),
    ("pmg_p_percent", "DOUBLE PRECISION"),
    ("pmg_f_percent", "DOUBLE PRECISION"),
    
    # Genealogia expandida
    ("pai_nome", "VARCHAR(255)"),
    ("pai_serie_rgd", "VARCHAR(50)"),
    ("mae_nome", "VARCHAR(255)"),
    ("mae_serie_rgd", "VARCHAR(50)"),
    
    # CARACTERÍSTICAS DE CRESCIMENTO - PN-EDg
    ("pmg_pn_dep", "DOUBLE PRECISION"),
    ("pmg_pn_ac", "DOUBLE PRECISION"),
    ("pmg_pn_deca", "VARCHAR(10)"),
    ("pmg_pn_p_percent", "DOUBLE PRECISION"),
    
    # PD-EDg
    ("pmg_pd_dep", "DOUBLE PRECISION"),
    ("pmg_pd_ac", "DOUBLE PRECISION"),
    ("pmg_pd_deca", "VARCHAR(10)"),
    ("pmg_pd_p_percent", "DOUBLE PRECISION"),
    
    # PA-EDg
    ("pmg_pa_dep", "DOUBLE PRECISION"),
    ("pmg_pa_ac", "DOUBLE PRECISION"),
    ("pmg_pa_deca", "VARCHAR(10)"),
    ("pmg_pa_p_percent", "DOUBLE PRECISION"),
    
    # PS-EDg
    ("pmg_ps_dep", "DOUBLE PRECISION"),
    ("pmg_ps_ac", "DOUBLE PRECISION"),
    ("pmg_ps_deca", "VARCHAR(10)"),
    ("pmg_ps_p_percent", "DOUBLE PRECISION"),
    
    # PM-EMg
    ("pmg_pm_dep", "DOUBLE PRECISION"),
    ("pmg_pm_ac", "DOUBLE PRECISION"),
    ("pmg_pm_deca", "VARCHAR(10)"),
    ("pmg_pm_p_percent", "DOUBLE PRECISION"),
    
    # IPPg
    ("pmg_ipp_dep", "DOUBLE PRECISION"),
    ("pmg_ipp_ac", "DOUBLE PRECISION"),
    ("pmg_ipp_deca", "VARCHAR(10)"),
    ("pmg_ipp_p_percent", "DOUBLE PRECISION"),
    
    # STAYg
    ("pmg_stay_dep", "DOUBLE PRECISION"),
    ("pmg_stay_ac", "DOUBLE PRECISION"),
    ("pmg_stay_deca", "VARCHAR(10)"),
    ("pmg_stay_p_percent", "DOUBLE PRECISION"),
    
    # PE-365g
    ("pmg_pe365_dep", "DOUBLE PRECISION"),
    ("pmg_pe365_ac", "DOUBLE PRECISION"),
    ("pmg_pe365_deca", "VARCHAR(10)"),
    ("pmg_pe365_p_percent", "DOUBLE PRECISION"),
    
    # PSNg
    ("pmg_psn_dep", "DOUBLE PRECISION"),
    ("pmg_psn_ac", "DOUBLE PRECISION"),
    ("pmg_psn_deca", "VARCHAR(10)"),
    ("pmg_psn_p_percent", "DOUBLE PRECISION"),
    
    # AOLg
    ("pmg_aol_dep", "DOUBLE PRECISION"),
    ("pmg_aol_ac", "DOUBLE PRECISION"),
    ("pmg_aol_deca", "VARCHAR(10)"),
    ("pmg_aol_p_percent", "DOUBLE PRECISION"),
    
    # ACABg
    ("pmg_acab_dep", "DOUBLE PRECISION"),
    ("pmg_acab_ac", "DOUBLE PRECISION"),
    ("pmg_acab_deca", "VARCHAR(10)"),
    ("pmg_acab_p_percent", "DOUBLE PRECISION"),
    
    # MARg
    ("pmg_mar_dep", "DOUBLE PRECISION"),
    ("pmg_mar_ac", "DOUBLE PRECISION"),
    ("pmg_mar_deca", "VARCHAR(10)"),
    ("pmg_mar_p_percent", "DOUBLE PRECISION"),
    
    # Eg
    ("pmg_eg_dep", "DOUBLE PRECISION"),
    ("pmg_eg_ac", "DOUBLE PRECISION"),
    ("pmg_eg_deca", "VARCHAR(10)"),
    ("pmg_eg_p_percent", "DOUBLE PRECISION"),
    
    # Pg
    ("pmg_p_dep", "DOUBLE PRECISION"),
    ("pmg_p_ac", "DOUBLE PRECISION"),
    ("pmg_p_deca", "VARCHAR(10)"),
    ("pmg_p_p_percent", "DOUBLE PRECISION"),
    
    # Mg
    ("pmg_m_dep", "DOUBLE PRECISION"),
    ("pmg_m_ac", "DOUBLE PRECISION"),
    ("pmg_m_deca", "VARCHAR(10)"),
    ("pmg_m_p_percent", "DOUBLE PRECISION"),
    
    # Pesos simples
    ("p120_peso_120", "DOUBLE PRECISION"),
    
    # Descendentes
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
    
    # Extras
    ("genotipado", "BOOLEAN"),
    ("csg", "BOOLEAN"),
    
    # processing_log_id
    ("processing_log_id", "INTEGER"),
]

def migrate():
    with engine.connect() as conn:
        for col_name, col_type in new_columns:
            try:
                # Check if column exists
                result = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'animais' AND column_name = '{col_name}'
                """))
                if not result.fetchone():
                    conn.execute(text(f"""
                        ALTER TABLE silver.animais ADD COLUMN {col_name} {col_type}
                    """))
                    logger.info(f"Added column: {col_name}")
                else:
                    logger.info(f"Column already exists: {col_name}")
            except Exception as e:
                logger.error(f"Error adding {col_name}: {e}")
        
        conn.commit()
        logger.info("Migration complete!")

if __name__ == "__main__":
    migrate()