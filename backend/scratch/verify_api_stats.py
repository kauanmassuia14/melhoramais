import os
import sys
from dotenv import load_dotenv

sys.path.append("/home/kauanmassuia/projeto-melhoramais")
load_dotenv("/home/kauanmassuia/projeto-melhoramais/.env")

from backend.database import SessionLocal
from backend.routers.animals_v2 import compute_analytics_internal

db = SessionLocal()
try:
    print("Testing compute_analytics_internal for farm_id=None (ALL)...")
    res = compute_analytics_internal(db, farm_id=None)
    
    print("\nKeys in result:")
    print(list(res.keys()))
    
    print("\nTop Sires found:")
    if "top_sires" in res:
        for sire in res["top_sires"]:
            print(f"Sire: {sire['sire_nome']} (RGN: {sire['sire_rgn']}, Serie: {sire['sire_serie']}) - Count: {sire['count']}")
    else:
        print("ERROR: top_sires key missing from response!")
        
finally:
    db.close()
