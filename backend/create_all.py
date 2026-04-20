import sys
sys.path.append('/home/kauanmassuia/projeto-melhoramais')

from backend.database import engine
from backend.models import Base

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")