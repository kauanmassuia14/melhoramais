import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine
from sqlalchemy import text

def migrate():
    print("Starting migration to Unified Architecture (v2)...")
    
    with engine.connect() as conn:
        # 1. Drop existing columns that are not in the new model
        # Note: We are using a fresh start for evaluations since it's empty
        print("Dropping old columns and adding new ones to genetics.genetic_evaluations...")
        
        try:
            # Drop columns (ignoring if they don't exist)
            cols_to_drop = [
                "pn_ed", "pd_ed", "pa_ed", "ps_ed", "pm_em", "ipp", "stay", "pe_365", 
                "psn", "aol", "acab", "marmoreio", "eg", "pg", "mg",
                "fenotipo_aol", "fenotipo_acab", "fenotipo_ipp", "fenotipo_stay",
                "p120_info", "p210_info", "p365_info", "p450_info",
                "iabczg", "deca_index"
            ]
            
            for col in cols_to_drop:
                conn.execute(text(f"ALTER TABLE genetics.genetic_evaluations DROP COLUMN IF EXISTS {col} CASCADE"))
            
            # Add new columns
            conn.execute(text("ALTER TABLE genetics.genetic_evaluations ADD COLUMN IF NOT EXISTS data_referencia DATE"))
            conn.execute(text("ALTER TABLE genetics.genetic_evaluations ADD COLUMN IF NOT EXISTS indice_principal NUMERIC(10, 4)"))
            conn.execute(text("ALTER TABLE genetics.genetic_evaluations ADD COLUMN IF NOT EXISTS rank_principal INTEGER"))
            conn.execute(text("ALTER TABLE genetics.genetic_evaluations ADD COLUMN IF NOT EXISTS percentil_principal NUMERIC(10, 4)"))
            conn.execute(text("ALTER TABLE genetics.genetic_evaluations ADD COLUMN IF NOT EXISTS metrics JSONB NOT NULL DEFAULT '{}'"))
            conn.execute(text("ALTER TABLE genetics.genetic_evaluations ADD COLUMN IF NOT EXISTS progeny_stats JSONB NOT NULL DEFAULT '{}'"))
            conn.execute(text("ALTER TABLE genetics.genetic_evaluations ADD COLUMN IF NOT EXISTS phenotypes JSONB NOT NULL DEFAULT '{}'"))
            conn.execute(text("ALTER TABLE genetics.genetic_evaluations ADD COLUMN IF NOT EXISTS upload_id VARCHAR(36)"))
            
            # Update data_processamento logic or other fields if needed
            conn.execute(text("ALTER TABLE genetics.genetic_evaluations ALTER COLUMN fonte_origem TYPE VARCHAR(50)"))
            
            conn.commit()
            print("Migration successful.")
            
        except Exception as e:
            conn.rollback()
            print(f"Migration failed: {e}")
            raise e

if __name__ == "__main__":
    migrate()
