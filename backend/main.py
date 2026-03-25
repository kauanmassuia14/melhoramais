from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
import os
import io

from .models import Base, Farm, Animal, ColumnMapping, ProcessingLog, User
from .database import get_db, engine
from .schemas import (
    FarmCreate, FarmResponse,
    AnimalResponse, AnimalFilter,
    ColumnMappingCreate, ColumnMappingResponse,
    ProcessingLogResponse, ProcessingResult,
    DashboardStats,
)
from .processor import GeneticDataProcessor
from .auth.router import router as auth_router
from .auth.dependencies import get_current_user, require_role

app = FastAPI(title="Melhora+ Genetic Data Unifier API", version="2.0.0")

# ============================================
# CORS — restricted to frontend origin
# ============================================
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# ============================================
# Auth Router (public endpoints inside)
# ============================================
app.include_router(auth_router)

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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "user")),
):
    # Non-admin can only upload to their own farm
    effective_farm_id = farm_id
    if current_user.role != "admin" and current_user.id_farm:
        effective_farm_id = current_user.id_farm

    try:
        content = await file.read()
        processor = GeneticDataProcessor(db, farm_id=effective_farm_id)

        df_cleaned, log = processor.process_file(content, file.filename, source_system)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
