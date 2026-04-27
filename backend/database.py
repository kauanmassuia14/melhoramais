import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Configure basic logging for startup tracking
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Fix protocol issue for newer SQLAlchemy versions
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
    logger.info("Fixed DATABASE_URL protocol from postgres:// to postgresql://")

DATABASE_URL = raw_db_url
IS_SQLITE = DATABASE_URL.startswith("sqlite")

connect_args = {}
pool_settings = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

if not IS_SQLITE:
    connect_args = {
        "connect_timeout": 5,
        "options": "-c statement_timeout=30000",
        "sslmode": "require"
    }
    pool_settings["poolclass"] = QueuePool
    pool_settings["pool_size"] = 5
    pool_settings["max_overflow"] = 10

logger.info("================ STARTUP DB ================")
logger.info("Tentando criar engine SQLAlchemy...")
print(f"[DEBUG] DB Protocol: {DATABASE_URL.split('://')[0]}://")
print(f"[DEBUG] Connect Args: {connect_args}")

try:
    engine = create_engine(
        DATABASE_URL,
        **pool_settings,
        connect_args=connect_args,
    )
    logger.info("Engine SQLAlchemy configurada com sucesso.")
except Exception as e:
    logger.error(f"Erro FATAL ao configurar engine SQLAlchemy: {str(e)}")
    import traceback
    traceback.print_exc()
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
