from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, case
from typing import Optional, List
import os
import io

from .models import Base, Farm, Animal, ColumnMapping, ProcessingLog
from .schemas import (
    FarmCreate, FarmResponse,
    AnimalResponse, AnimalFilter,
    ColumnMappingCreate, ColumnMappingResponse,
    ProcessingLogResponse, ProcessingResult,
    DashboardStats,
)
from .processor import GeneticDataProcessor

app = FastAPI(title="Melhora+ Genetic Data Unifier API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

if DATABASE_URL.startswith("sqlite"):
    Base.metadata.create_all(bind=engine)


def get_db():
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# Health
# ============================================
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "melhoramais-backend", "version": "2.0.0"}


# ============================================
# Farms CRUD
# ============================================
@app.post("/farms", response_model=FarmResponse, status_code=201)
def create_farm(farm: FarmCreate, db: Session = Depends(get_db)):
    db_farm = Farm(**farm.model_dump())
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return db_farm


@app.get("/farms", response_model=List[FarmResponse])
def list_farms(db: Session = Depends(get_db)):
    return db.query(Farm).all()


@app.get("/farms/{farm_id}", response_model=FarmResponse)
def get_farm(farm_id: int, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id_farm == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


# ============================================
# Animals CRUD
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
):
    query = db.query(Animal)

    if farm_id is not None:
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
def get_animal(animal_id: int, db: Session = Depends(get_db)):
    animal = db.query(Animal).filter(Animal.id_animal == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return animal


# ============================================
# Processing (Upload)
# ============================================
@app.post("/process-genetic-data")
async def process_genetic_data(
    source_system: str = Form(...),
    file: UploadFile = File(...),
    farm_id: int = Form(default=1),
    db: Session = Depends(get_db),
):
    try:
        content = await file.read()
        processor = GeneticDataProcessor(db, farm_id=farm_id)

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
# Column Mappings CRUD
# ============================================
@app.get("/mappings", response_model=List[ColumnMappingResponse])
def list_mappings(
    source_system: Optional[str] = Query(None), db: Session = Depends(get_db)
):
    query = db.query(ColumnMapping)
    if source_system:
        query = query.filter(ColumnMapping.source_system == source_system)
    return query.all()


@app.post("/mappings", response_model=ColumnMappingResponse, status_code=201)
def create_mapping(mapping: ColumnMappingCreate, db: Session = Depends(get_db)):
    db_mapping = ColumnMapping(**mapping.model_dump())
    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)
    return db_mapping


@app.delete("/mappings/{mapping_id}", status_code=204)
def delete_mapping(mapping_id: int, db: Session = Depends(get_db)):
    mapping = db.query(ColumnMapping).filter(ColumnMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    db.delete(mapping)
    db.commit()


# ============================================
# Processing Logs
# ============================================
@app.get("/logs", response_model=List[ProcessingLogResponse])
def list_logs(
    farm_id: Optional[int] = Query(None),
    source_system: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(ProcessingLog)
    if farm_id:
        query = query.filter(ProcessingLog.id_farm == farm_id)
    if source_system:
        query = query.filter(ProcessingLog.source_system == source_system)
    return query.order_by(ProcessingLog.started_at.desc()).limit(limit).all()


# ============================================
# Dashboard Stats
# ============================================
@app.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    farm_id: Optional[int] = Query(None), db: Session = Depends(get_db)
):
    query = db.query(Animal)
    if farm_id:
        query = query.filter(Animal.id_farm == farm_id)

    total_animals = query.count()
    total_farms = db.query(Farm).count()

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

    # Average indices
    from datetime import datetime, timedelta

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_uploads = (
        db.query(ProcessingLog)
        .filter(ProcessingLog.started_at >= thirty_days_ago)
        .count()
    )

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
