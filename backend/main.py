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

from backend.models import Base, Farm, ColumnMapping, ProcessingLog, User, Notification, Upload, Cliente, GeneticsAnimal, GeneticsGeneticEvaluation, GeneticsFarm, RawAnimalData, Animal
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
# Auth Router (public endpoints inside)
# ============================================
app.include_router(auth_router)
app.include_router(benchmark_router)

# ============================================
# Reports Router (NOVO - PDF Customizável)
# ============================================
from backend.routers.reports import router as reports_router
app.include_router(reports_router)

# ============================================
# Dashboard Router (stats)
# ============================================
from backend.routers.dashboard import router as dashboard_router
app.include_router(dashboard_router)

# ============================================
# Migration Router (admin)
# ============================================
from backend.routers.migrate import router as migrate_router
app.include_router(migrate_router)

# ============================================
# Animals V2 Router (genetics schema)
# ============================================
from backend.routers.animals_v2 import router as animals_v2_router
app.include_router(animals_v2_router)

# ============================================
# Farms Router (genetics schema - new)
# ============================================
from backend.routers.farms import router as farms_router
app.include_router(farms_router)

# ============================================
# Genetics Farms Router (genetics schema)
# ============================================
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


# Global Exception Handler to ensure CORS headers and reveal errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    import sys
    
    # FORÇAR PRINT NO CONSOLE DO RAILWAY:
    print(f"\n[GLOBAL ERROR MIDDLEWARE] Erro capturado em {request.url}:", file=sys.stderr)
    traceback.print_exc()
    print("[GLOBAL ERROR MIDDLEWARE] Fim do traceback.\n", file=sys.stderr)
    
    content = {
        "detail": str(exc),
        "traceback": traceback.format_exc(),  # Forçado para vermos o erro real agora
        "type": type(exc).__name__
    }
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


# ============================================
# Database test (public, temporary)
# ============================================
@app.get("/db-test")
def db_test():
    """Test database connection and return info."""
    import os
    db_url = os.getenv("DATABASE_URL", "not set")
    # Mask password in URL
    db_url_masked = db_url
    if "://" in db_url and "@" in db_url:
        try:
            parts = db_url.split("://", 1)
            scheme = parts[0]
            rest = parts[1]
            auth, host = rest.split("@", 1)
            if ":" in auth:
                user, _ = auth.split(":", 1)
                db_url_masked = f"{scheme}://{user}:***@{host}"
        except:
            pass
            
    try:
        from sqlalchemy import text, inspect
        inspector = inspect(engine)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            db_status = "connected"
            
            # List tables in silver and audit
            tables = []
            try:
                res = conn.execute(text("""
                    SELECT schemaname, tablename 
                    FROM pg_catalog.pg_tables 
                    WHERE schemaname IN ('genetics')
                """))
                tables = [f"{r[0]}.{r[1]}" for r in res]
            except:
                pass

            # Try to count users
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM genetics.users"))
                user_count = result.scalar()
            except Exception as e:
                user_count = f"error: {str(e)}"
                
            # Get columns for animals
            animal_columns = []
            try:
                animal_columns = [c["name"] for c in inspector.get_columns("animals", schema="genetics")]
            except:
                pass
    except Exception as e:
        db_status = f"error: {str(e)}"
        user_count = "unknown"
        tables = []
        animal_columns = []
    
    return {
        "database_url_masked": db_url_masked,
        "database_status": db_status,
        "user_count": user_count,
        "tables": tables,
        "animal_columns": animal_columns,
        "is_sqlite": db_url.startswith("sqlite")
    }


# ============================================
# Environment variables debug (public, temporary)
# ============================================
@app.get("/env-debug")
def env_debug():
    """Show environment variables (masked)."""
    import os
    
    # List of important environment variables
    important_vars = ["DATABASE_URL", "JWT_SECRET", "ALLOWED_ORIGINS", "RAILWAY_ENVIRONMENT", "RAILWAY_SERVICE_NAME"]
    
    result = {}
    for var in important_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "://" in value and "@" in value:
                # URL with credentials
                parts = value.split("://", 1)
                if len(parts) == 2:
                    scheme = parts[0]
                    rest = parts[1]
                    if "@" in rest:
                        auth, host = rest.split("@", 1)
                        if ":" in auth:
                            user, _ = auth.split(":", 1)
                            masked_auth = f"{user}:***"
                        else:
                            masked_auth = auth
                        value = f"{scheme}://{masked_auth}@{host}"
            elif "SECRET" in var or "KEY" in var or "PASSWORD" in var:
                value = "***" if value else "not set"
            result[var] = value
        else:
            result[var] = "not set"
    
    # Also show all Railway environment variables
    railway_vars = {k: v for k, v in os.environ.items() if k.startswith("RAILWAY_")}
    result["railway_vars"] = railway_vars
    
    # Show CORS configuration
    result["cors_config"] = {
        "allowed_origins": ALLOWED_ORIGINS,
        "allowed_origins_count": len(ALLOWED_ORIGINS),
        "raw_allowed_origins_env": os.getenv("ALLOWED_ORIGINS", "USING_DEFAULT")
    }
    
    return result


# ============================================
# Animals CRUD (protected)
# ============================================
@app.get("/animals", response_model=List[AnimalResponse])
def list_animals(
    farm_id: Optional[int] = Query(None),
    source: Optional[str] = Query(None),
    raca: Optional[str] = Query(None),
    sexo: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Animal)

    # Non-admin users can only see their farm's animals
    if current_user.role != "admin" and current_user.id_farm:
        query = query.filter(Animal.id_farm == current_user.id_farm)
    elif farm_id is not None:
        query = query.filter(Animal.id_farm == farm_id)

    if source:
        query = query.filter(Animal.fonte_origem == source)
    if raca:
        query = query.filter(Animal.raca == raca)
    if sexo:
        query = query.filter(Animal.sexo == sexo)
    if search:
        query = query.filter(
            (Animal.rgn_animal.ilike(f"%{search}%"))
            | (Animal.nome_animal.ilike(f"%{search}%"))
        )

    return query.offset(offset).limit(limit).all()


@app.get("/animals/{animal_id}", response_model=AnimalResponse)
def get_animal(
    animal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    animal = db.query(Animal).filter(Animal.id_animal == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    if current_user.role != "admin" and current_user.id_farm != animal.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    return animal


# ============================================
# Processing (Upload) — protected
# ============================================
@app.post("/process-genetic-data")
async def process_genetic_data(
    source_system: str = Form(...),
    file: UploadFile = File(...),
    farm_id: str = Form(default=None),
    upload_id: str = Form(default=None),
    download_excel: bool = Form(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "user")),
):
    effective_farm_id = farm_id
    if current_user.role != "admin" and current_user.id_farm:
        effective_farm_id = str(current_user.id_farm)
    
    if upload_id:
        upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        if upload.id_farm != effective_farm_id:
            raise HTTPException(status_code=403, detail="Upload does not belong to this farm")
        if upload.status == "completed":
            raise HTTPException(status_code=400, detail="Upload already processed")

    if not effective_farm_id:
        raise HTTPException(status_code=400, detail="farm_id is required")

    try:
        import asyncio
        content = await file.read()
        processor = GeneticDataProcessor(db, farm_id=effective_farm_id, upload_id=upload_id)

        # Rodar processamento pesado em thread para não bloquear o event loop
        loop = asyncio.get_event_loop()
        df_cleaned, log, upload = await loop.run_in_executor(
            None, 
            processor.process_file, 
            content, 
            file.filename or f"upload_{source_system}", 
            source_system
        )
        
        # Se process_file retorna None para log/upload, ler do upload ou criar objetos vazios
        if log is not None:
            inserted = log.rows_inserted or 0
            updated = log.rows_updated or 0
            failed = log.rows_failed or 0
        elif upload is not None:
            inserted = upload.rows_inserted or 0
            updated = upload.rows_updated or 0
            failed = 0
        else:
            inserted, updated, failed = 0, 0, 0
        
        logger.info(f"Processamento concluído: {len(df_cleaned)} linhas, inserted={inserted}, updated={updated}, failed={failed}")
        
        if download_excel:
            excel_data = await loop.run_in_executor(
                None,
                processor.generate_formatted_excel,
                df_cleaned
            )

            return StreamingResponse(
                io.BytesIO(excel_data),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=output_tratado_{source_system}.xlsx",
                    "Access-Control-Expose-Headers": "Content-Disposition"
                },
            )
        else:
            return {
                "status": "success",
                "message": "File processed successfully",
                "inserted": inserted,
                "updated": updated,
                "failed": failed,
                "upload_id": upload_id or (upload.upload_id if upload else None)
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# Column Mappings CRUD — protected (admin only for write)
# ============================================
@app.get("/mappings", response_model=List[ColumnMappingResponse])
def list_mappings(
    source_system: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ColumnMapping)
    if source_system:
        query = query.filter(ColumnMapping.source_system == source_system)
    return query.all()


@app.post("/mappings", response_model=ColumnMappingResponse, status_code=201)
def create_mapping(
    mapping: ColumnMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    db_mapping = ColumnMapping(**mapping.model_dump())
    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)
    return db_mapping


@app.put("/mappings/{mapping_id}", response_model=ColumnMappingResponse)
def update_mapping(
    mapping_id: int,
    mapping: ColumnMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    db_mapping = db.query(ColumnMapping).filter(ColumnMapping.id == mapping_id).first()
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    update_data = mapping.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_mapping, key, value)
    
    db.commit()
    db.refresh(db_mapping)
    return db_mapping


@app.delete("/mappings/{mapping_id}", status_code=204)
def delete_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    mapping = db.query(ColumnMapping).filter(ColumnMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    db.delete(mapping)
    db.commit()


# ============================================
# Processing Logs — protected
# ============================================
@app.get("/logs", response_model=List[ProcessingLogResponse])
def list_logs(
    farm_id: Optional[int] = Query(None),
    source_system: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ProcessingLog)
    if current_user.role != "admin" and current_user.id_farm:
        query = query.filter(ProcessingLog.id_farm == current_user.id_farm)
    elif farm_id:
        query = query.filter(ProcessingLog.id_farm == farm_id)
    if source_system:
        query = query.filter(ProcessingLog.source_system == source_system)
    return query.order_by(ProcessingLog.started_at.desc()).limit(limit).all()


@app.delete("/logs", status_code=204)
def delete_logs(
    log_ids: List[int] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete multiple processing logs and all their associated data."""
    if not log_ids:
        raise HTTPException(status_code=400, detail="No log IDs provided")
    
    logs = db.query(ProcessingLog).filter(ProcessingLog.id.in_(log_ids)).all()
    if not logs:
        raise HTTPException(status_code=404, detail="Logs not found")
    
    for log in logs:
        if current_user.role != "admin" and log.id_farm != current_user.id_farm:
            raise HTTPException(status_code=403, detail=f"Access denied to log {log.id}")
    
    for log in logs:
        log_id = log.id
        
        # Find upload associated with this log via animals
        upload_ids = db.query(Animal.upload_id).filter(
            Animal.id_farm == log.id_farm,
            Animal.processing_log_id == log_id,
            Animal.upload_id.isnot(None)
        ).distinct().all()
        upload_ids = [u[0] for u in upload_ids if u[0]]
        
        # Delete raw animal data first (has FK to processing_log)
        db.query(RawAnimalData).filter(
            RawAnimalData.processing_log_id == log_id
        ).delete(synchronize_session=False)
        
        # Get all animal IDs to delete raw data
        animais = db.query(Animal).filter(
            Animal.id_farm == log.id_farm,
            Animal.processing_log_id == log_id
        ).all()
        animais_ids = [a.id_animal for a in animais]
        
        # Delete raw data for those animals
        if animais_ids:
            db.query(RawAnimalData).filter(RawAnimalData.id_animal.in_(animais_ids)).delete(synchronize_session=False)
        
        # Delete animals
        db.query(Animal).filter(
            Animal.id_farm == log.id_farm,
            Animal.processing_log_id == log_id
        ).delete(synchronize_session=False)
        
        # Delete associated uploads
        if upload_ids:
            for upload_id in upload_ids:
                upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
                if upload:
                    db.delete(upload)
        
        # Delete the log
        db.delete(log)
    
    db.commit()
    return {"message": f"{len(logs)} logs and associated data deleted successfully"}


@app.delete("/logs/{log_id}", status_code=204)
def delete_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a processing log, associated animals, and linked upload."""
    from sqlalchemy import text
    
    log = db.query(ProcessingLog).filter(ProcessingLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    if current_user.role != "admin" and log.id_farm != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete raw animal data first (has FK to processing_log)
    db.query(RawAnimalData).filter(
        RawAnimalData.processing_log_id == log_id
    ).delete(synchronize_session=False)
    
    # Find upload associated with this log via animals
    upload_ids = db.query(Animal.upload_id).filter(
        Animal.id_farm == log.id_farm,
        Animal.processing_log_id == log_id,
        Animal.upload_id.isnot(None)
    ).distinct().all()
    upload_ids = [u[0] for u in upload_ids if u[0]]
    
    # Get all animal IDs to delete raw data
    animais = db.query(Animal).filter(
        Animal.id_farm == log.id_farm,
        Animal.processing_log_id == log_id
    ).all()
    animais_ids = [a.id_animal for a in animais]
    
    # Delete raw animal data
    if animais_ids:
        db.query(RawAnimalData).filter(RawAnimalData.id_animal.in_(animais_ids)).delete(synchronize_session=False)
    
    # Delete animals
    db.query(Animal).filter(
        Animal.id_farm == log.id_farm,
        Animal.processing_log_id == log_id
    ).delete(synchronize_session=False)
    
    # Delete associated uploads
    if upload_ids:
        for upload_id in upload_ids:
            upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
            if upload:
                db.delete(upload)
    
    # Delete genetics.animals and genetic_evaluations linked to this log via upload_id
    if upload_ids:
        for upload_id in upload_ids:
            # Get animal IDs from genetics
            animals = db.execute(
                text("SELECT id FROM genetics.animals WHERE upload_id = :upload_id"),
                {"upload_id": upload_id}
            ).fetchall()
            
            if animals:
                animal_ids = [a[0] for a in animals]
                
                # Delete genetic evaluations first
                db.execute(
                    text("DELETE FROM genetics.genetic_evaluations WHERE animal_id = ANY(:animal_ids)"),
                    {"animal_ids": animal_ids}
                )
                
                # Delete animals
                db.execute(
                    text("DELETE FROM genetics.animals WHERE upload_id = :upload_id"),
                    {"upload_id": upload_id}
                )
    
    # Delete the log
    db.delete(log)
    db.commit()
    return {"message": "Log and associated data deleted successfully"}


# ============================================
# Uploads API — protected
# ============================================
@app.post("/uploads", response_model=UploadResponse, status_code=201)
def create_upload(
    upload: UploadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new upload record before processing file."""
    # Check farm access
    if current_user.role != "admin" and current_user.id_farm != upload.id_farm:
        raise HTTPException(status_code=403, detail="Access denied to this farm")
    
    # Verify farm exists in genetics.farms
    import uuid as _uuid
    try:
        farm_uuid = _uuid.UUID(upload.id_farm)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid farm ID format")
    farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    db_upload = Upload(
        nome=upload.nome,
        id_farm=upload.id_farm,
        fonte_origem=upload.fonte_origem,
        arquivo_nome_original=upload.arquivo_nome_original,
        arquivo_hash=upload.arquivo_hash,
        usuario_id=current_user.id,
        status="processing",
    )
    db.add(db_upload)
    db.commit()
    db.refresh(db_upload)
    return db_upload


@app.get("/uploads", response_model=List[UploadResponse])
def list_uploads(
    farm_id: Optional[int] = Query(None),
    fonte_origem: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List uploads with optional filtering."""
    query = db.query(Upload)
    
    # Scope to user's farm if not admin
    if current_user.role != "admin" and current_user.id_farm:
        query = query.filter(Upload.id_farm == current_user.id_farm)
    elif farm_id:
        query = query.filter(Upload.id_farm == farm_id)
    
    if fonte_origem:
        query = query.filter(Upload.fonte_origem == fonte_origem)
    if status:
        query = query.filter(Upload.status == status)
    
    return query.order_by(Upload.data_upload.desc()).offset(offset).limit(limit).all()


@app.get("/uploads/{upload_id}", response_model=UploadWithAnimalsResponse)
def get_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get upload details with animal preview."""
    upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Check access
    if current_user.role != "admin" and upload.id_farm != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get farm name from genetics.farms
    import uuid as _uuid
    farm_nome = "Unknown"
    try:
        farm_uuid = _uuid.UUID(upload.id_farm)
        farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
        farm_nome = farm.nome if farm else "Unknown"
    except (ValueError, AttributeError):
        pass
    
    # Get animal preview (first 100)
    animais = (
        db.query(Animal)
        .filter(Animal.upload_id == upload_id)
        .order_by(Animal.id_animal.desc())
        .limit(100)
        .all()
    )
    
    total_animais = db.query(Animal).filter(Animal.upload_id == upload_id).count()
    
    return UploadWithAnimalsResponse(
        upload=UploadResponse.model_validate(upload),
        farm_nome=farm_nome,
        animais_preview=[AnimalResponse.model_validate(a) for a in animais],
        total_animais=total_animais,
    )


@app.delete("/uploads/{upload_id}", status_code=204)
def delete_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an upload and all associated data."""
    upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    if current_user.role != "admin" and upload.id_farm != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 1. Tenta deletar dados legacy de forma segura (ignora se as tabelas não existirem)
    try:
        animais_ids = [a.id_animal for a in db.query(Animal.id_animal).filter(Animal.upload_id == upload_id).all()]
        if animais_ids:
            db.query(RawAnimalData).filter(RawAnimalData.id_animal.in_(animais_ids)).delete(synchronize_session=False)
        db.query(Animal).filter(Animal.upload_id == upload_id).delete(synchronize_session=False)
        db.flush()
    except Exception as e:
        logger.warning(f"Bypassing legacy silver animal deletion because table doesn't exist: {e}")
        db.rollback()
        # Restaura o objeto upload na sessão após o rollback
        upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found after transaction rollback")
    
    # 2. Deleta genetics.animals e genetics.genetic_evaluations
    try:
        genetics_animals = db.execute(
            text("SELECT id FROM genetics.animals WHERE upload_id = :upload_id"),
            {"upload_id": upload_id}
        ).fetchall()
        
        if genetics_animals:
            animal_ids = [a[0] for a in genetics_animals]
            db.execute(
                text("DELETE FROM genetics.genetic_evaluations WHERE animal_id = ANY(:animal_ids)"),
                {"animal_ids": animal_ids}
            )
            db.execute(
                text("DELETE FROM genetics.animals WHERE upload_id = :upload_id"),
                {"upload_id": upload_id}
            )
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting genetics data: {e}")
        raise HTTPException(status_code=500, detail=f"Database error deleting genetics data: {str(e)}")
    
    # 3. Deleta a entrada de upload
    try:
        db.delete(upload)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error finalizing upload deletion: {e}")
        raise HTTPException(status_code=500, detail=f"Database error during commit: {str(e)}")
    
    return {"message": "Upload and associated data deleted successfully"}


@app.delete("/uploads/{upload_id}/genetics", status_code=200)
def delete_upload_genetics(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete genetics.animals and genetic_evaluations linked to an upload."""
    from sqlalchemy import text
    
    upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    if current_user.role != "admin" and upload.id_farm != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Buscar IDs dos animais deste upload
    animals = db.execute(
        text("SELECT id FROM genetics.animals WHERE upload_id = :upload_id"),
        {"upload_id": upload_id}
    ).fetchall()
    
    animal_ids = [a[0] for a in animals]
    
    if animal_ids:
        # Deletar genetic_evaluations primeiro (FK)
        db.execute(
            text("DELETE FROM genetics.genetic_evaluations WHERE animal_id = ANY(:animal_ids)"),
            {"animal_ids": animal_ids}
        )
        
        # Deletar animals
        db.execute(
            text("DELETE FROM genetics.animals WHERE upload_id = :upload_id"),
            {"upload_id": upload_id}
        )
    
    db.commit()
    
    return {"message": f"Deleted {len(animal_ids)} genetics animals and their evaluations"}


@app.delete("/admin/clear-genetics", status_code=200)
def clear_all_genetics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin only: Clear all genetics data."""
    from sqlalchemy import text
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    # Delete all genetic evaluations
    db.execute(text("DELETE FROM genetics.genetic_evaluations"))
    
    # Delete all animals
    db.execute(text("DELETE FROM genetics.animals"))
    
    db.commit()
    
    return {"message": "All genetics data cleared"}





# ============================================
# PDF Report — protected
# ============================================
@app.get("/report/dashboard")
def generate_dashboard_report(
    farm_id: Optional[str] = Query(None),
    include_animals: bool = Query(False),
    include_logs: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid as _uuid
    import statistics
    import json

    # Access Control
    if current_user.role != "admin" and current_user.id_farm:
        farm_id = str(current_user.id_farm)

    if not farm_id:
        raise HTTPException(status_code=400, detail="Farm ID is required")

    try:
        farm_uuid = _uuid.UUID(str(farm_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Farm UUID")

    farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    farm_name = farm.nome

    # Get all animals in the farm
    animal_query = db.query(GeneticsAnimal).filter(GeneticsAnimal.farm_id == farm_uuid)
    total_animals = animal_query.count()

    # Sex Breakdown
    sex_counts_query = (
        db.query(GeneticsAnimal.sexo, func.count(GeneticsAnimal.id))
        .filter(GeneticsAnimal.farm_id == farm_uuid)
        .group_by(GeneticsAnimal.sexo)
        .all()
    )
    animals_by_sex = {s or "unknown": c for s, c in sex_counts_query}

    # Source Platform Breakdown & Evaluations
    eval_query = db.query(GeneticsGeneticEvaluation).filter(GeneticsGeneticEvaluation.farm_id == farm_uuid)
    source_counts_query = (
        db.query(GeneticsGeneticEvaluation.fonte_origem, func.count(GeneticsGeneticEvaluation.id))
        .filter(GeneticsGeneticEvaluation.farm_id == farm_uuid)
        .group_by(GeneticsGeneticEvaluation.fonte_origem)
        .all()
    )
    animals_by_source = {s or "unknown": c for s, c in source_counts_query}

    # Calculate weight statistics (P210, P365, P450)
    all_evals = eval_query.all()

    p210_list = []
    p365_list = []
    p450_list = []

    for ev in all_evals:
        metrics = ev.metrics if isinstance(ev.metrics, dict) else {}
        if isinstance(ev.metrics, str):
            try:
                metrics = json.loads(ev.metrics)
            except:
                metrics = {}

        pd_m = metrics.get("PD-EDg") or metrics.get("DP210") or metrics.get("DP120")
        if pd_m and pd_m.get("dep") is not None:
            p210_list.append(float(pd_m["dep"]))

        pa_m = metrics.get("PA-EDg") or metrics.get("DP365")
        if pa_m and pa_m.get("dep") is not None:
            p365_list.append(float(pa_m["dep"]))

        ps_m = metrics.get("PS-EDg") or metrics.get("DP450")
        if ps_m and ps_m.get("dep") is not None:
            p450_list.append(float(ps_m["dep"]))

    avg_p210 = statistics.mean(p210_list) if p210_list else None
    avg_p365 = statistics.mean(p365_list) if p365_list else None
    avg_p450 = statistics.mean(p450_list) if p450_list else None

    # Recent Uploads (past 30 days)
    from datetime import datetime, timedelta, timezone
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_uploads = (
        db.query(ProcessingLog)
        .filter(ProcessingLog.id_farm == farm_id, ProcessingLog.started_at >= thirty_days_ago)
        .count()
    )

    stats = {
        "total_animals": total_animals,
        "total_farms": 1,
        "animals_by_source": animals_by_source,
        "animals_by_sex": animals_by_sex,
        "recent_uploads": recent_uploads,
        "avg_p210": avg_p210,
        "avg_p365": avg_p365,
        "avg_p450": avg_p450,
    }

    # Fetch animals if requested
    animals_data = None
    if include_animals:
        animals_list = animal_query.all()
        animals_data = []
        
        # Optimize N+1 Query: Fetch all evaluations in a single query
        animal_ids = [a.id for a in animals_list]
        eval_map = {}
        if animal_ids:
            all_evals_for_list = (
                db.query(GeneticsGeneticEvaluation)
                .filter(GeneticsGeneticEvaluation.animal_id.in_(animal_ids))
                .all()
            )
            for ev in all_evals_for_list:
                existing = eval_map.get(ev.animal_id)
                if not existing or (ev.safra and (not existing.safra or ev.safra > existing.safra)):
                    eval_map[ev.animal_id] = ev

        for a in animals_list:
            latest_eval = eval_map.get(a.id)

            p210_val = None
            p365_val = None
            p450_val = None
            metrics = {}
            if latest_eval:
                metrics = latest_eval.metrics if isinstance(latest_eval.metrics, dict) else {}
                if isinstance(latest_eval.metrics, str):
                    try:
                        metrics = json.loads(latest_eval.metrics)
                    except:
                        metrics = {}

                pd_m = metrics.get("PD-EDg") or metrics.get("DP210") or metrics.get("DP120")
                if pd_m and pd_m.get("dep") is not None:
                    p210_val = float(pd_m["dep"])
                pa_m = metrics.get("PA-EDg") or metrics.get("DP365")
                if pa_m and pa_m.get("dep") is not None:
                    p365_val = float(pa_m["dep"])
                ps_m = metrics.get("PS-EDg") or metrics.get("DP450")
                if ps_m and ps_m.get("dep") is not None:
                    p450_val = float(ps_m["dep"])

            animals_data.append({
                "rgn_animal": a.rgn,
                "nome_animal": a.nome or "—",
                "sexo": a.sexo or "—",
                "raca": a.serie or "—",
                "p210_peso_desmama": p210_val,
                "p365_peso_ano": p365_val,
                "p450_peso_sobreano": p450_val,
                "fonte_origem": latest_eval.fonte_origem if latest_eval else "—",
                "metrics": metrics,
            })

    # Generate PDF
    generator = ReportGeneratorV2()
    pdf_bytes = generator.generate_dashboard_report(
        stats=stats,
        animals=animals_data,
        farm_name=farm_name,
    )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=relatorio_dashboard_{datetime.now(timezone(timedelta(hours=-3))).strftime('%Y%m%d_%H%M')}.pdf"
        },
    )


# ============================================
# Upload Detail — protected
# ============================================
@app.get("/reports/upload/{log_id}", response_model=UploadDetailResponse)
def get_upload_detail(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(ProcessingLog).filter(ProcessingLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Processing log not found")
    
    if current_user.role != "admin" and log.id_farm != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    animals = (
        db.query(Animal)
        .filter(Animal.id_farm == log.id_farm, Animal.fonte_origem == log.source_system)
        .order_by(Animal.id_animal.desc())
        .limit(100)
        .all()
    )
    
    return UploadDetailResponse(
        log=ProcessingLogResponse.model_validate(log),
        animals_preview=[AnimalResponse.model_validate(a) for a in animals],
        total_count=log.total_rows,
    )


# ============================================
# Upload PDF Report — protected
# ============================================
@app.get("/reports/upload/{log_id}/pdf")
def generate_upload_report(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(ProcessingLog).filter(ProcessingLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Processing log not found")
    
    if current_user.role != "admin" and log.id_farm != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    animals = (
        db.query(Animal)
        .filter(Animal.id_farm == log.id_farm, Animal.fonte_origem == log.source_system)
        .all()
    )
    
    farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == log.id_farm).first() if log.id_farm else None
    farm_name = farm.nome if farm else None
    
    generator = ReportGenerator()
    pdf_bytes = generator.generate_upload_report(
        log=log,
        animals=animals,
        farm_name=farm_name,
    )
    
    filename_safe = (log.filename or "upload").replace(".", "_").replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=relatorio_upload_{log_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        },
    )


# ============================================
# Animal PDF Report — protected
# ============================================
@app.get("/reports/animal/{animal_id}/pdf")
def generate_animal_report(
    animal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    animal = db.query(Animal).filter(Animal.id_animal == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    
    if current_user.role != "admin" and animal.id_farm != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    import uuid as _uuid
    farm_name = None
    try:
        farm_uuid = _uuid.UUID(str(animal.id_farm))
        farm_g = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
        farm_name = farm_g.nome if farm_g else None
    except (ValueError, AttributeError):
        pass
    
    generator = ReportGenerator()
    pdf_bytes = generator.generate_animal_report(
        animal=animal,
        farm_name=farm_name,
    )
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=relatorio_animal_{animal_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        },
    )


# ============================================
# Benchmark PDF Report — protected
# ============================================
@app.get("/reports/benchmark/pdf")
def generate_benchmark_report(
    platform_code: str = Query(..., description="Platform code (ANCP, GENEPLUS, PMGZ)"),
    characteristic: str = Query(..., description="Characteristic code"),
    farm_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from .benchmark import PLATFORMS
    
    if platform_code not in PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Platform {platform_code} not found")
    
    platform = PLATFORMS[platform_code]
    char_info = None
    for char in platform["characteristics"]:
        if char["code"] == characteristic:
            char_info = char
            break
    
    if not char_info:
        raise HTTPException(status_code=404, detail=f"Characteristic {characteristic} not found")
    
    column_name = char_info["column"]
    
    query = db.query(GeneticsGeneticEvaluation).join(GeneticsAnimal).filter(
        GeneticsGeneticEvaluation.fonte_origem == platform_code
    )
    if farm_id:
        query = query.filter(GeneticsAnimal.farm_id == farm_id)
    elif current_user.role != "admin" and current_user.id_farm:
        query = query.filter(GeneticsAnimal.farm_id == str(current_user.id_farm))
    
    query = query.filter(getattr(GeneticsGeneticEvaluation, column_name).isnot(None))
    evaluations = query.all()
    
    farm_name = None
    if farm_id:
        try:
            import uuid
            farm_uuid = uuid.UUID(farm_id)
            farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
            farm_name = farm.nome if farm else None
        except ValueError:
            pass
    elif current_user.id_farm:
        try:
            import uuid
            farm_uuid = uuid.UUID(str(current_user.id_farm))
            farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
            farm_name = farm.nome if farm else None
        except ValueError:
            pass
    
    generator = ReportGenerator()
    pdf_bytes = generator.generate_benchmark_report(
        platform_code=platform_code,
        platform_name=platform["name"],
        characteristic=char_info,
        evaluations=evaluations,
        farm_name=farm_name,
    )
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=relatorio_benchmark_{platform_code}_{characteristic}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        },
    )


import asyncio
import json
from backend.auth.security import decode_token

class NotificationPublisher:
    def __init__(self):
        self._listeners = {}

    def subscribe(self, user_id: int) -> asyncio.Queue:
        if user_id not in self._listeners:
            self._listeners[user_id] = set()
        queue = asyncio.Queue()
        self._listeners[user_id].add(queue)
        return queue

    def unsubscribe(self, user_id: int, queue: asyncio.Queue):
        if user_id in self._listeners:
            self._listeners[user_id].discard(queue)
            if not self._listeners[user_id]:
                del self._listeners[user_id]

    async def publish(self, user_id: int, notification_data: dict):
        if user_id in self._listeners:
            for queue in self._listeners[user_id]:
                await queue.put(notification_data)

notification_publisher = NotificationPublisher()

def get_current_user_sse(
    token: str = Query(None),
    db: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token type invalid")
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == user_id, User.ativo == True).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


@app.post("/notifications", response_model=NotificationResponse, status_code=201)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_notification = Notification(
        id_user=current_user.id,
        title=notification.title,
        message=notification.message,
        type=notification.type,
        link=notification.link,
    )
    try:
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
        
        notification_payload = {
            "id": db_notification.id,
            "id_user": db_notification.id_user,
            "title": db_notification.title,
            "message": db_notification.message,
            "type": db_notification.type,
            "is_read": db_notification.is_read,
            "link": db_notification.link,
            "created_at": db_notification.created_at.isoformat() if db_notification.created_at else None
        }
        await notification_publisher.publish(current_user.id, notification_payload)
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        db.rollback()
    return db_notification


@app.get("/notifications/sse")
async def notifications_sse(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sse),
):
    async def event_generator():
        queue = notification_publisher.subscribe(current_user.id)
        try:
            yield "data: {\"type\": \"connected\"}\n\n"
            while True:
                try:
                    notification = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(notification)}\n\n"
                except asyncio.TimeoutError:
                    yield "data: {\"type\": \"ping\"}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            notification_publisher.unsubscribe(current_user.id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/notifications", response_model=List[NotificationResponse])
def list_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Notification).filter(Notification.id_user == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(Notification.created_at.desc()).limit(50).all()


@app.get("/notifications/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = db.query(Notification).filter(
        Notification.id_user == current_user.id,
        Notification.is_read == False,
    ).count()
    return {"count": count}


@app.put("/notifications/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.id_user == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


@app.put("/notifications/{notification_id}", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    update: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.id_user == current_user.id,
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    if update.is_read is not None:
        notification.is_read = update.is_read
    
    db.commit()
    db.refresh(notification)
    return notification


@app.delete("/notifications/clear-read", status_code=200)
def clear_read_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.id_user == current_user.id,
        Notification.is_read == True,
    ).delete(synchronize_session=False)
    db.commit()
    return {"message": "All read notifications cleared"}


@app.delete("/notifications/{notification_id}", status_code=200)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.id_user == current_user.id,
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    return {"message": "Notification deleted successfully"}



if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)


# ============================================================
# TEMPORARY ENDPOINT FOR SEEDING - REMOVE AFTER USE
# ============================================================
@app.post("/admin/seed-mappings")
def seed_mappings_temp():
    """Temporary endpoint to seed column mappings. Remove after use!"""
    from sqlalchemy.orm import sessionmaker
    from backend.database import engine
    from backend.seed import seed
    
    # Run the seed using a fresh session
    try:
        seed()
        return {"message": "Mappings seeded successfully"}
    except Exception as e:
        # If error, might already exist - that's ok
        return {"message": f"Seed attempted: {str(e)[:100]}", "status": "done"}
