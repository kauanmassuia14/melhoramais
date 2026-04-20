import sys
sys.path.append('/home/kauanmassuia/projeto-melhoramais')

from backend.database import engine, IS_SQLITE
from sqlalchemy import text

BENCHMARK_COLUMNS = [
    # ANCP
    ("anc_mg", "DOUBLE PRECISION"),
    ("anc_te", "DOUBLE PRECISION"),
    ("anc_m", "DOUBLE PRECISION"),
    ("anc_p", "DOUBLE PRECISION"),
    ("anc_dp", "DOUBLE PRECISION"),
    ("anc_sp", "DOUBLE PRECISION"),
    ("anc_e", "DOUBLE PRECISION"),
    ("anc_sao", "DOUBLE PRECISION"),
    ("anc_leg", "DOUBLE PRECISION"),
    ("anc_sh", "DOUBLE PRECISION"),
    ("anc_pp30", "DOUBLE PRECISION"),
    # GENEPLUS
    ("gen_iqg", "DOUBLE PRECISION"),
    ("gen_pmm", "DOUBLE PRECISION"),
    ("gen_p", "DOUBLE PRECISION"),
    ("gen_dp", "DOUBLE PRECISION"),
    ("gen_sp", "DOUBLE PRECISION"),
    ("gen_e", "DOUBLE PRECISION"),
    ("gen_sao", "DOUBLE PRECISION"),
    ("gen_leg", "DOUBLE PRECISION"),
    ("gen_sh", "DOUBLE PRECISION"),
    ("gen_pp30", "DOUBLE PRECISION"),
    # PMGZ
    ("pmg_iabc", "DOUBLE PRECISION"),
    ("pmg_zpmm", "DOUBLE PRECISION"),
    ("pmg_p", "DOUBLE PRECISION"),
    ("pmg_dp", "DOUBLE PRECISION"),
    ("pmg_sp", "DOUBLE PRECISION"),
    ("pmg_e", "DOUBLE PRECISION"),
    ("pmg_sao", "DOUBLE PRECISION"),
    ("pmg_leg", "DOUBLE PRECISION"),
    ("pmg_sh", "DOUBLE PRECISION"),
    ("pmg_pp30", "DOUBLE PRECISION"),
]


def run_migration():
    print("Running migration to add benchmark columns to animais table...")
    
    with engine.connect() as conn:
        for col_name, col_type in BENCHMARK_COLUMNS:
            sql = f'ALTER TABLE silver.animais ADD COLUMN IF NOT EXISTS {col_name} {col_type}'
            try:
                conn.execute(text(sql))
                print(f"  Added column: {col_name}")
            except Exception as e:
                print(f"  Error adding {col_name}: {e}")
        
        conn.commit()
    
    print("\nMigration completed!")
    print("Benchmark columns added to silver.animais table.")


if __name__ == "__main__":
    run_migration()
