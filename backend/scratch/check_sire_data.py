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
    print("=== Checking genetics.animais (legacy/flat table) ===")
    total = conn.execute(text("SELECT COUNT(*) FROM genetics.animais;")).scalar()
    print(f"Total: {total}")
    
    pai_count = conn.execute(text("SELECT COUNT(*) FROM genetics.animais WHERE pai_rgn IS NOT NULL AND pai_rgn != '';")).scalar()
    print(f"Animals with pai_rgn: {pai_count}")

    mae_count = conn.execute(text("SELECT COUNT(*) FROM genetics.animais WHERE mae_rgn IS NOT NULL AND mae_rgn != '';")).scalar()
    print(f"Animals with mae_rgn: {mae_count}")

    print("\n=== Unique Sires (pai_rgn) in legacy table ===")
    unique_sires = conn.execute(text("SELECT COUNT(DISTINCT pai_rgn) FROM genetics.animais WHERE pai_rgn IS NOT NULL AND pai_rgn != '';")).scalar()
    print(f"Unique Sires: {unique_sires}")

    if unique_sires > 0:
        print("\n=== Sample of Sires in legacy table ===")
        sample = conn.execute(text("""
            SELECT pai_rgn, COUNT(*) as offspring_count
            FROM genetics.animais
            WHERE pai_rgn IS NOT NULL AND pai_rgn != ''
            GROUP BY pai_rgn
            ORDER BY offspring_count DESC
            LIMIT 5;
        """)).fetchall()
        for row in sample:
            print(f"  Sire RGN: {row[0]}, Offspring Count: {row[1]}")
