from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta, timezone

from backend.models import User
from backend.database import get_db
from backend.schemas import (
    DashboardStats,
)
from backend.auth.dependencies import get_current_user


router = APIRouter(prefix="/stats", tags=["Dashboard"])


@router.get("", response_model=DashboardStats)
def get_dashboard_stats(
    farm_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.models import Animal, Farm
    from sqlalchemy import func
    
    query = db.query(Animal)

    if current_user.role != "admin" and current_user.id_farm:
        query = query.filter(Animal.id_farm == current_user.id_farm)
    elif farm_id:
        query = query.filter(Animal.id_farm == farm_id)

    total_animals = query.count()

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

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    from backend.models import ProcessingLog
    log_query = db.query(ProcessingLog).filter(ProcessingLog.started_at >= thirty_days_ago)
    if current_user.role != "admin" and current_user.id_farm:
        log_query = log_query.filter(ProcessingLog.id_farm == current_user.id_farm)
    recent_uploads = log_query.count()

    avg_p210 = query.with_entities(func.avg(Animal.p210_peso_desmama)).scalar()
    avg_p365 = query.with_entities(func.avg(Animal.p365_peso_ano)).scalar()
    avg_p450 = query.with_entities(func.avg(Animal.p450_peso_sobreano)).scalar()

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