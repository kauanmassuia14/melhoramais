from backend.database import engine
from sqlalchemy import text
import json

def check_animals():
    with engine.connect() as conn:
        try:
            res = conn.execute(text("""
                SELECT rgn, nome, nascimento, genotipado 
                FROM genetics.animals 
                ORDER BY created_at DESC 
                LIMIT 10
            """))
            rows = res.fetchall()
            for r in rows:
                print(f"RGN: {r[0]} | Nome: {r[1]} | Nasc: {r[2]} | Gen: {r[3]}")
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    check_animals()
