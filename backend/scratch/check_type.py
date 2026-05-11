from backend.database import engine
from sqlalchemy import text

def check_type():
    with engine.connect() as conn:
        try:
            # Check if it's an ENUM
            res = conn.execute(text("""
                SELECT n.nspname as schema, t.typname as type, e.enumlabel as label
                FROM pg_type t 
                JOIN pg_enum e ON t.oid = e.enumtypid  
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE t.typname = 'boolean_status'
            """))
            rows = res.fetchall()
            if rows:
                print("ENUM labels:", [r[2] for r in rows])
            else:
                # Check if it's a DOMAIN or something else
                res = conn.execute(text("""
                    SELECT n.nspname, t.typname, t.typtype
                    FROM pg_type t
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = 'boolean_status'
                """))
                row = res.fetchone()
                print("Type info:", row)
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    check_type()
