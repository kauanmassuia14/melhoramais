import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

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
    }
    pool_settings["poolclass"] = QueuePool
    pool_settings["pool_size"] = 5
    pool_settings["max_overflow"] = 10

engine = create_engine(
    DATABASE_URL,
    **pool_settings,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
