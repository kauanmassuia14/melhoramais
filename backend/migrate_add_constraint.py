"""
Migration: Add named constraint uix_farm_rgn to animais table
"""
from sqlalchemy import create_engine, text
from backend.config import settings
import sys

def migrate():
    """Add uix_farm_rgn constraint if it doesn't exist."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if constraint already exists
        result = conn.execute(text("""
            SELECT conname FROM pg_constraint 
            WHERE conrelid = 'silver.animais'::regclass 
            AND conname = 'uix_farm_rgn'
        """))
        
        if result.fetchone():
            print("Constraint 'uix_farm_rgn' already exists. Skipping.")
            return
        
        # Check if there's an existing unique constraint on these columns
        result = conn.execute(text("""
            SELECT conname FROM pg_constraint 
            WHERE conrelid = 'silver.animais'::regclass 
            AND contype = 'u'
            AND conkey = ARRAY[
                (SELECT attnum FROM pg_attribute WHERE attrelid = 'silver.animais'::regclass AND attname = 'id_farm'),
                (SELECT attnum FROM pg_attribute WHERE attrelid = 'silver.animais'::regclass AND attname = 'rgn_animal')
            ]::int2[]
        """))
        
        existing = result.fetchone()
        if existing:
            print(f"Found existing constraint '{existing[0]}', renaming to 'uix_farm_rgn'...")
            conn.execute(text(f"ALTER TABLE silver.animais RENAME CONSTRAINT {existing[0]} TO uix_farm_rgn"))
            conn.commit()
            print("Constraint renamed successfully!")
        else:
            print("Adding constraint 'uix_farm_rgn'...")
            conn.execute(text("""
                ALTER TABLE silver.animais 
                ADD CONSTRAINT uix_farm_rgn UNIQUE (id_farm, rgn_animal)
            """))
            conn.commit()
            print("Constraint added successfully!")

if __name__ == "__main__":
    migrate()
