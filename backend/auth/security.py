import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

_env = os.getenv("ENVIRONMENT", "production").lower()
_default_secret = "DEV-ONLY-INSECURE-SECRET-DO-NOT-USE-IN-PROD"

if _env in ("development", "dev", "local", "test"):
    SECRET_KEY = os.getenv("JWT_SECRET", _default_secret)
else:
    SECRET_KEY = os.getenv("JWT_SECRET", "")
    if not SECRET_KEY or SECRET_KEY == _default_secret:
        raise RuntimeError(
            "FATAL: JWT_SECRET environment variable is not set. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\" "
            "and set it as JWT_SECRET in your environment."
        )

_logger = logging.getLogger(__name__)
if SECRET_KEY == _default_secret:
    _logger.warning("⚠️  Using INSECURE default JWT_SECRET — only acceptable in development!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Increased from 15 for better UX
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
