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
    print("=== Checking genetics.animals ===")
    total = conn.execute(text("SELECT COUNT(*) FROM genetics.animals;")).scalar()
    print(f"Total animals: {total}")
    
    with_sire = conn.execute(text("SELECT COUNT(*) FROM genetics.animals WHERE sire_id IS NOT NULL;")).scalar()
    print(f"Animals with sire_id: {with_sire}")

    with_dam = conn.execute(text("SELECT COUNT(*) FROM genetics.animals WHERE dam_id IS NOT NULL;")).scalar()
    print(f"Animals with dam_id: {with_dam}")

    print("\n=== Top 10 Sires in genetics.animals ===")
    top_sires = conn.execute(text("""
        SELECT s.rgn, s.nome, COUNT(a.id) as offspring_count
        FROM genetics.animals a
        JOIN genetics.animals s ON a.sire_id = s.id
        GROUP BY s.id, s.rgn, s.nome
        ORDER BY offspring_count DESC
        LIMIT 10;
    """)).fetchall()
    for row in top_sires:
        print(f"  Sire RGN: {row[0]}, Name: {row[1]}, Offspring Count: {row[2]}")
