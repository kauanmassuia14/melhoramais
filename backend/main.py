from dotenv import load_dotenv
load_dotenv()

import logging
logger = logging.getLogger(__name__)

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Optional, List
from datetime import datetime
import os
import io

from backend.models import Base, ProcessingLog, User, Notification, Upload, GeneticsAnimal, GeneticsGeneticEvaluation, GeneticsFarm, RawAnimalData
from backend.database import get_db, engine
from backend.schemas import (
    FarmCreate, FarmUpdate, FarmResponse,
    AnimalResponse, AnimalFilter,
    ColumnMappingCreate, ColumnMappingUpdate, ColumnMappingResponse,
    ProcessingLogResponse, ProcessingResult,
    DashboardStats, ReportHistoryItem, UploadDetailResponse,
    NotificationCreate, NotificationResponse, NotificationUpdate,
    UploadCreate, UploadResponse, UploadWithAnimalsResponse, UploadFilter,
)
from .processor import GeneticDataProcessor
from .auth.router import router as auth_router
from .auth.dependencies import get_current_user, require_role
from .report_generator import ReportGenerator
from .report_generator_v2 import ReportGeneratorV2
from .benchmark import router as benchmark_router

app = FastAPI(title="Melhora+ Genetic Data Unifier API", version="2.0.0")

# ============================================
# CORS — robust configuration
# ============================================
def get_origins():
    try:
        raw_origins = os.getenv("ALLOWED_ORIGINS", "")
        if not raw_origins or raw_origins.strip() == "*":
            return ["*"]
        
        origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
        
        if not origins:
            return ["*"]
            
        defaults = [
            "http://localhost:3000", 
            "http://localhost:3001", 
            "http://127.0.0.1:3000", 
            "http://127.0.0.1:3001",
            "https://melhoramais-edfn.vercel.app",
            "https://melhoramais-production.up.railway.app"
        ]
        for d in defaults:
            if d not in origins:
                origins.append(d)
        return origins
    except Exception:
        return ["*"]

ALLOWED_ORIGINS = get_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False if "*" in ALLOWED_ORIGINS else True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ============================================
# Routers Registration
# ============================================
app.include_router(auth_router)
app.include_router(benchmark_router)

# Reports Router (both prefixes and root-level)
from backend.routers.reports import router as reports_router, router_no_prefix as reports_no_prefix_router
app.include_router(reports_router)
app.include_router(reports_no_prefix_router)

# Uploads Router (root-level endpoints)
from backend.routers.uploads import router as uploads_router
app.include_router(uploads_router)

# Notifications Router (root-level endpoints)
from backend.routers.notifications import router as notifications_router
app.include_router(notifications_router)

# Dashboard Router (stats)
from backend.routers.dashboard import router as dashboard_router
app.include_router(dashboard_router)

# Migration Router (admin)
from backend.routers.migrate import router as migrate_router
app.include_router(migrate_router)

# Animals V2 Router (genetics schema)
from backend.routers.animals_v2 import router as animals_v2_router
app.include_router(animals_v2_router)

# Farms Router (genetics schema - new)
from backend.routers.farms import router as farms_router
app.include_router(farms_router)

# Genetics Farms Router (genetics schema)
from backend.routers.genetics_farms import router as genetics_farms_router
app.include_router(genetics_farms_router)

# Run PMGZ migration on startup (auto-add columns if missing)
# DISABLED - silver.animais was deleted, using genetics schema instead
# try:
#     run_migration_on_startup()
# except Exception as e:
#     logger.warning(f"Startup migration skipped: {e}")

# ============================================
# Database Schema & Initialization (LIMPO)
# ============================================
@app.on_event("startup")
def startup_event():
    """Inicializa banco - cria tabelas se não existirem."""
    #from backend.models.v2 import AnimalBase, AnimalPlatformData, AnimalSnapshot, AnimalAudit
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    if not DATABASE_URL.startswith("sqlite"):
        from sqlalchemy import text
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver"))
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS genetics"))
                
                # Create custom types if they don't exist
                conn.execute(text("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'animal_sex' AND n.nspname = 'genetics') THEN
                            CREATE TYPE genetics.animal_sex AS ENUM ('M', 'F');
                        END IF;
                        IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'boolean_status' AND n.nspname = 'genetics') THEN
                            CREATE TYPE genetics.boolean_status AS ENUM ('SIM', 'NÃO');
                        END IF;
                    END $$;
                """))
                conn.commit()
        except Exception as e:
            print(f"Erro ao criar schemas ou tipos: {e}")
    
    # Criar todas as tabelas (modelos existentes + v2)
    from backend.models import Base
    try:
        print("Ensuring database tables exist...")
        Base.metadata.create_all(bind=engine)
        print("Database tables ensured.")
    except Exception as e:
        print(f"Error during metadata.create_all: {e}")
        # We don't re-raise to allow the server to start even if it fails


# Global Exception Handler — secure for production
_IS_DEV = os.getenv("ENVIRONMENT", "production").lower() in ("development", "dev", "local", "test")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    import sys
    
    # Always log full traceback server-side
    logger.error(f"Unhandled error at {request.url}: {exc}", exc_info=True)
    
    content = {
        "detail": str(exc) if _IS_DEV else "Internal server error",
        "type": type(exc).__name__
    }
    # Only include traceback in development
    if _IS_DEV:
        content["traceback"] = traceback.format_exc()
    
    response = JSONResponse(status_code=500, content=content)
    
    # Manually add CORS if needed (Middleware might be bypassed on some crashes)
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "*"
    
    return response


# ============================================
# Health (public)
# ============================================
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "melhoramais-backend", "version": "2.0.0"}


# NOTE: /db-test and /env-debug endpoints REMOVED for security.
# Use Railway logs or direct DB access for debugging.
# If needed in dev, set ENVIRONMENT=development and use the health endpoint.

# NOTE: Legacy inline endpoints have been modularized and moved to backend/routers:
# - Uploads, mappings, processing logs -> backend/routers/uploads.py
# - SSE & notifications -> backend/routers/notifications.py
# - Reports & PDF exports -> backend/routers/reports.py
# - Animals v2 -> backend/routers/animals_v2.py
# - Farms -> backend/routers/farms.py and backend/routers/genetics_farms.py



if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)


# NOTE: /admin/seed-mappings endpoint REMOVED for security.
# Use `python -m backend.seed` from the CLI instead.
