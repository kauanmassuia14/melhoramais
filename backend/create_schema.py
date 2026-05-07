import sys
sys.path.append('/home/kauanmassuia/projeto-melhoramais')

from backend.database import engine
from sqlalchemy import text

print("Creating schemas...")
with engine.connect() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver"))
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS genetics"))
    conn.commit()
print("Schemas created.")

# Now create tables
from backend.models import Base
Base.metadata.create_all(bind=engine)
print("Tables created.")