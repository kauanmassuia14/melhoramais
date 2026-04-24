from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime
import os
import io

from backend.models import Base, Farm, Animal, ColumnMapping, ProcessingLog, User, Notification, Upload
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
from .benchmark import router as benchmark_router

app = FastAPI(title="Melhora+ Genetic Data Unifier API", version="2.0.0")

# ============================================
# CORS — restricted to frontend origin
# ============================================
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001,https://melhoramais-edfn.vercel.app").split(",")
ALLOWED_ORIGINS = [o.strip() for o in ALLOWED_ORIGINS if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# ============================================
# Auth Router (public endpoints inside)
# ============================================
app.include_router(auth_router)
app.include_router(benchmark_router)

# ============================================
# Create tables on SQLite (dev only)
# ============================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
if DATABASE_URL.startswith("sqlite"):
    Base.metadata.create_all(bind=engine)


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
    from sqlalchemy import text
    
    db_url = os.getenv("DATABASE_URL", "not set")
    # Mask password in URL
    if "://" in db_url and "@" in db_url:
        parts = db_url.split("://", 1)
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
                db_url_masked = f"{scheme}://{masked_auth}@{host}"
            else:
                db_url_masked = db_url
        else:
            db_url_masked = db_url
    else:
        db_url_masked = db_url
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            db_status = "connected"
            # Try to count users
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM silver.usuarios"))
                user_count = result.scalar()
            except Exception as e:
                user_count = f"error: {str(e)}"
    except Exception as e:
        db_status = f"error: {str(e)}"
        user_count = "unknown"
    
    return {
        "database_url_masked": db_url_masked,
        "database_status": db_status,
        "user_count": user_count,
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
# Farms CRUD (protected)
# ============================================
@app.post("/farms", response_model=FarmResponse, status_code=201)
def create_farm(
    farm: FarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    db_farm = Farm(**farm.model_dump())
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return db_farm


@app.get("/farms", response_model=List[FarmResponse])
def list_farms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return db.query(Farm).all()
    if current_user.id_farm:
        return db.query(Farm).filter(Farm.id_farm == current_user.id_farm).all()
    return []


@app.get("/farms/{farm_id}", response_model=FarmResponse)
def get_farm(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm = db.query(Farm).filter(Farm.id_farm == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if current_user.role != "admin" and current_user.id_farm != farm_id:
        raise HTTPException(status_code=403, detail="Access denied to this farm")
    return farm


@app.put("/farms/{farm_id}", response_model=FarmResponse)
def update_farm(
    farm_id: int,
    farm: FarmUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Update farm - admin only or farm owner can edit their own farm."""
    db_farm = db.query(Farm).filter(Farm.id_farm == farm_id).first()
    if not db_farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    update_data = farm.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_farm, key, value)
    
    db.commit()
    db.refresh(db_farm)
    return db_farm


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
    farm_id: int = Form(default=1),
    upload_id: str = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "user")),
):
    # Non-admin can only upload to their own farm
    effective_farm_id = farm_id
    if current_user.role != "admin" and current_user.id_farm:
        effective_farm_id = current_user.id_farm
    
    # Validate upload_id if provided
    if upload_id:
        upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        if upload.id_farm != effective_farm_id:
            raise HTTPException(status_code=403, detail="Upload does not belong to this farm")
        if upload.status == "completed":
            raise HTTPException(status_code=400, detail="Upload already processed")

    try:
        content = await file.read()
        processor = GeneticDataProcessor(db, farm_id=effective_farm_id, upload_id=upload_id)

        df_cleaned, log, upload = processor.process_file(content, file.filename or f"upload_{source_system}", source_system)
        excel_data = processor.generate_formatted_excel(df_cleaned)

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=output_tratado_{source_system}.xlsx"
            },
        )
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
    
    # Verify farm exists
    farm = db.query(Farm).filter(Farm.id_farm == upload.id_farm).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    db_upload = Upload(
        nome=upload.nome,
        id_farm=upload.id_farm,
        fonte_origem=upload.fonte_origem,
        arquivo_nome_original=upload.arquivo_nome_original,
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
    
    # Get farm name
    farm = db.query(Farm).filter(Farm.id_farm == upload.id_farm).first()
    farm_nome = farm.nome_farm if farm else "Unknown"
    
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
    current_user: User = Depends(require_role("admin")),
):
    """Delete an upload and all associated animals (admin only)."""
    upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Delete associated animals first
    db.query(Animal).filter(Animal.upload_id == upload_id).delete()
    
    # Delete the upload
    db.delete(upload)
    db.commit()
    
    return {"message": "Upload deleted successfully"}


# ============================================
# Dashboard Stats — protected
# ============================================
@app.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    farm_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Animal)

    # Scope to user's farm if not admin
    if current_user.role != "admin" and current_user.id_farm:
        query = query.filter(Animal.id_farm == current_user.id_farm)
    elif farm_id:
        query = query.filter(Animal.id_farm == farm_id)

    total_animals = query.count()

    if current_user.role == "admin":
        total_farms = db.query(Farm).count()
    else:
        total_farms = 1 if current_user.id_farm else 0

    # Animals by source
    source_counts = (
        db.query(Animal.fonte_origem, func.count(Animal.id_animal))
        .group_by(Animal.fonte_origem)
        .all()
    )
    animals_by_source = {s or "unknown": c for s, c in source_counts}

    # Animals by sex
    sex_counts = (
        db.query(Animal.sexo, func.count(Animal.id_animal))
        .group_by(Animal.sexo)
        .all()
    )
    animals_by_sex = {s or "unknown": c for s, c in sex_counts}

    # Recent uploads
    from datetime import datetime, timedelta, timezone

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    log_query = db.query(ProcessingLog).filter(ProcessingLog.started_at >= thirty_days_ago)
    if current_user.role != "admin" and current_user.id_farm:
        log_query = log_query.filter(ProcessingLog.id_farm == current_user.id_farm)
    recent_uploads = log_query.count()

    avg_p210 = db.query(func.avg(Animal.p210_peso_desmama)).scalar()
    avg_p365 = db.query(func.avg(Animal.p365_peso_ano)).scalar()
    avg_p450 = db.query(func.avg(Animal.p450_peso_sobreano)).scalar()

    return DashboardStats(
        total_animals=total_animals,
        total_farms=total_farms,
        animals_by_source=animals_by_source,
        animals_by_sex=animals_by_sex,
        recent_uploads=recent_uploads,
        avg_p210=round(avg_p210, 2) if avg_p210 else None,
        avg_p365=round(avg_p365, 2) if avg_p365 else None,
        avg_p450=round(avg_p450, 2) if avg_p450 else None,
    )


# ============================================
# PDF Report — protected
# ============================================
@app.get("/report/dashboard")
def generate_dashboard_report(
    farm_id: Optional[int] = Query(None),
    include_animals: bool = Query(False),
    include_logs: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get stats
    animal_query = db.query(Animal)
    if current_user.role != "admin" and current_user.id_farm:
        animal_query = animal_query.filter(Animal.id_farm == current_user.id_farm)
    elif farm_id is not None:
        animal_query = animal_query.filter(Animal.id_farm == farm_id)

    total_animals = animal_query.count()

    if current_user.role == "admin":
        total_farms = db.query(Farm).count()
    else:
        total_farms = 1 if current_user.id_farm else 0

    source_counts = (
        db.query(Animal.fonte_origem, func.count(Animal.id_animal))
        .group_by(Animal.fonte_origem)
        .all()
    )
    animals_by_source = {s or "unknown": c for s, c in source_counts}

    sex_counts = (
        db.query(Animal.sexo, func.count(Animal.id_animal))
        .group_by(Animal.sexo)
        .all()
    )
    animals_by_sex = {s or "unknown": c for s, c in sex_counts}

    from datetime import datetime, timedelta, timezone
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    log_query = db.query(ProcessingLog).filter(ProcessingLog.started_at >= thirty_days_ago)
    if current_user.role != "admin" and current_user.id_farm:
        log_query = log_query.filter(ProcessingLog.id_farm == current_user.id_farm)
    recent_uploads = log_query.count()

    avg_p210 = db.query(func.avg(Animal.p210_peso_desmama)).scalar()
    avg_p365 = db.query(func.avg(Animal.p365_peso_ano)).scalar()
    avg_p450 = db.query(func.avg(Animal.p450_peso_sobreano)).scalar()

    stats = {
        "total_animals": total_animals,
        "total_farms": total_farms,
        "animals_by_source": animals_by_source,
        "animals_by_sex": animals_by_sex,
        "recent_uploads": recent_uploads,
        "avg_p210": round(float(avg_p210), 2) if avg_p210 else None,
        "avg_p365": round(float(avg_p365), 2) if avg_p365 else None,
        "avg_p450": round(float(avg_p450), 2) if avg_p450 else None,
    }

    # Get animals if requested
    animals_data = None
    if include_animals:
        animals = animal_query.limit(200).all()
        animals_data = [
            {
                "rgn_animal": a.rgn_animal,
                "nome_animal": a.nome_animal,
                "sexo": a.sexo,
                "raca": a.raca,
                "p210_peso_desmama": a.p210_peso_desmama,
                "p365_peso_ano": a.p365_peso_ano,
                "p450_peso_sobreano": a.p450_peso_sobreano,
                "fonte_origem": a.fonte_origem,
            }
            for a in animals
        ]

    # Get logs if requested
    logs_data = None
    if include_logs:
        logs_q = db.query(ProcessingLog)
        if current_user.role != "admin" and current_user.id_farm:
            logs_q = logs_q.filter(ProcessingLog.id_farm == current_user.id_farm)
        elif farm_id:
            logs_q = logs_q.filter(ProcessingLog.id_farm == farm_id)
        logs = logs_q.order_by(ProcessingLog.started_at.desc()).limit(20).all()
        logs_data = [
            {
                "source_system": l.source_system,
                "filename": l.filename,
                "total_rows": l.total_rows,
                "rows_inserted": l.rows_inserted,
                "status": l.status,
                "started_at": l.started_at.isoformat() if l.started_at else None,
            }
            for l in logs
        ]

    # Get farm name
    farm_name = None
    if current_user.id_farm:
        farm = db.query(Farm).filter(Farm.id_farm == current_user.id_farm).first()
        if farm:
            farm_name = farm.nome_farm

    # Generate PDF
    generator = ReportGenerator()
    pdf_bytes = generator.generate_dashboard_report(
        stats=stats,
        animals=animals_data,
        logs=logs_data,
        farm_name=farm_name,
    )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=relatorio_dashboard_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
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
    
    farm = db.query(Farm).filter(Farm.id_farm == log.id_farm).first()
    farm_name = farm.nome_farm if farm else None
    
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
    
    farm = db.query(Farm).filter(Farm.id_farm == animal.id_farm).first()
    
    generator = ReportGenerator()
    pdf_bytes = generator.generate_animal_report(
        animal=animal,
        farm_name=farm.nome_farm if farm else None,
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
    farm_id: Optional[int] = Query(None),
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
    
    query = db.query(Animal)
    if farm_id:
        query = query.filter(Animal.id_farm == farm_id)
    elif current_user.role != "admin" and current_user.id_farm:
        query = query.filter(Animal.id_farm == current_user.id_farm)
    
    query = query.filter(getattr(Animal, column_name).isnot(None))
    animals = query.all()
    
    farm = None
    farm_name = None
    if farm_id:
        farm = db.query(Farm).filter(Farm.id_farm == farm_id).first()
        farm_name = farm.nome_farm if farm else None
    elif current_user.id_farm:
        farm = db.query(Farm).filter(Farm.id_farm == current_user.id_farm).first()
        farm_name = farm.nome_farm if farm else None
    
    generator = ReportGenerator()
    pdf_bytes = generator.generate_benchmark_report(
        platform_code=platform_code,
        platform_name=platform["name"],
        characteristic=char_info,
        animals=animals,
        farm_name=farm_name,
    )
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=relatorio_benchmark_{platform_code}_{characteristic}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        },
    )


@app.post("/notifications", response_model=NotificationResponse, status_code=201)
def create_notification(
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
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
