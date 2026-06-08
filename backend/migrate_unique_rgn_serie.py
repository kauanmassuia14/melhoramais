import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append("/home/kauanmassuia/projeto-melhoramais")
load_dotenv("/home/kauanmassuia/projeto-melhoramais/.env")

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("No DATABASE_URL found")
    sys.exit(1)

engine = create_engine(db_url)

with engine.connect() as conn:
    trans = conn.begin()
    try:
        print("Starting migration to update uniqueness constraint on genetics.animals...")
        
        # 1. Update existing null series to ''
        print("1. Updating NULL series to empty string...")
        conn.execute(text("""
            UPDATE genetics.animals
            SET serie = ''
            WHERE serie IS NULL;
        """))
        
        # 2. Check if there are any duplicates on (farm_id, rgn, serie) before creating constraint
        print("2. Checking for duplicates on (farm_id, rgn, serie)...")
        dup_query = text("""
            SELECT farm_id, rgn, serie, COUNT(*)
            FROM genetics.animals
            GROUP BY farm_id, rgn, serie
            HAVING COUNT(*) > 1;
        """)
        dups = conn.execute(dup_query).fetchall()
        if dups:
            print(f"Found {len(dups)} duplicate groups! Resolving duplicates by keeping the newest...")
            for d in dups:
                farm_id, rgn, serie, count = d
                print(f"  Duplicate: farm_id={farm_id}, rgn={rgn}, serie={serie} (count={count})")
                # Keep the latest created_at record, delete others
                conn.execute(text("""
                    DELETE FROM genetics.animals
                    WHERE farm_id = :farm_id AND rgn = :rgn AND COALESCE(serie, '') = :serie
                    AND id NOT IN (
                        SELECT id FROM genetics.animals
                        WHERE farm_id = :farm_id AND rgn = :rgn AND COALESCE(serie, '') = :serie
                        ORDER BY created_at DESC
                        LIMIT 1
                    );
                """), {"farm_id": farm_id, "rgn": rgn, "serie": serie or ''})
        
        # 3. Drop old constraint
        print("3. Dropping old constraint uix_farm_rgn...")
        conn.execute(text("""
            ALTER TABLE genetics.animals
            DROP CONSTRAINT IF EXISTS uix_farm_rgn;
        """))
        
        # 4. Create new unique constraint
        print("4. Creating new unique constraint uix_farm_rgn_serie...")
        conn.execute(text("""
            ALTER TABLE genetics.animals
            ADD CONSTRAINT uix_farm_rgn_serie UNIQUE (farm_id, rgn, serie);
        """))
        
        trans.commit()
        print("Migration completed successfully!")
    except Exception as e:
        trans.rollback()
        print(f"Migration failed: {e}")
        raise e
