import os
import sys
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append("/home/kauanmassuia/projeto-melhoramais")
load_dotenv("/home/kauanmassuia/projeto-melhoramais/.env")

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.connect() as conn:
    rows = conn.execute(text("SELECT farm_id, updated_at, analytics FROM genetics.dashboard_stats_cache")).fetchall()
    print(f"Total rows in cache: {len(rows)}")
    for r in rows:
        fid, updated, analytics = r
        print(f"\nCache Key (farm_id): {fid}, Updated At: {updated}")
        if analytics:
            print(f"  Keys in analytics: {list(analytics.keys())}")
            if "top_sires" in analytics:
                print(f"  top_sires length: {len(analytics['top_sires'])}")
                print(f"  First 3 sires: {analytics['top_sires'][:3]}")
            else:
                print("  WARNING: top_sires is NOT in analytics JSON!")
        else:
            print("  analytics is empty or NULL")
