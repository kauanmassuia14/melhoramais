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
    print("=== Total Animals in DB ===")
    total = conn.execute(text("SELECT COUNT(*) FROM genetics.animals;")).scalar()
    print(f"Total: {total}")
    
    print("\n=== Animals per Farm ===")
    res = conn.execute(text("""
        SELECT f.nome, COUNT(a.id)
        FROM genetics.farms f
        LEFT JOIN genetics.animals a ON a.farm_id = f.id
        GROUP BY f.nome
        ORDER BY COUNT(a.id) DESC;
    """)).fetchall()
    for row in res:
        print(f"  Farm '{row[0]}': {row[1]}")
        
    print("\n=== Upload Sessions ===")
    uploads = conn.execute(text("""
        SELECT upload_id, nome, id_farm, total_registros, rows_inserted, rows_updated, status, data_upload
        FROM genetics.uploads
        ORDER BY data_upload DESC;
    """)).fetchall()
    for u in uploads:
        print(f"  Upload: ID={u[0]}, name={u[1]}, farm_id={u[2]}, total={u[3]}, inserted={u[4]}, updated={u[5]}, status={u[6]}, data_upload={u[7]}")
