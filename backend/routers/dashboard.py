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
    from backend.models import GeneticsAnimal, GeneticsGeneticEvaluation, GeneticsFarm
    from sqlalchemy import func, cast, String
    
    # Usar genetics.animals + genetic_evaluations
    query = db.query(GeneticsAnimal)

    # Filtrar por farm usando id_farm UUID diretamente (genetics schema)
    genetics_farm = None
    if current_user.role != "admin" and current_user.id_farm:
        import uuid as _uuid
        try:
            farm_uuid = _uuid.UUID(str(current_user.id_farm))
            genetics_farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
            if genetics_farm:
                query = query.filter(GeneticsAnimal.farm_id == genetics_farm.id)
        except (ValueError, AttributeError):
            pass

    total_animals = query.count()

    # Total farms
    if current_user.role == "admin":
        total_farms = db.query(GeneticsFarm).count()
    else:
        total_farms = 1 if current_user.id_farm else 0

    # Animals by source (fonte_origem vem das avaliações)
    source_subq = db.query(
        GeneticsGeneticEvaluation.animal_id,
        GeneticsGeneticEvaluation.fonte_origem
    ).distinct().subquery()
    
    source_counts = (
        db.query(source_subq.c.fonte_origem, func.count(source_subq.c.animal_id))
        .group_by(source_subq.c.fonte_origem)
        .all()
    )
    animals_by_source = {s or "unknown": c for s, c in source_counts}

    # Animals by sex - Improved mapping
    sex_counts = (
        db.query(GeneticsAnimal.sexo, func.count(GeneticsAnimal.id))
        .group_by(GeneticsAnimal.sexo)
        .all()
    )
    animals_by_sex = {}
    for s, c in sex_counts:
        label = "Macho" if s == "M" else "Fêmea" if s == "F" else "Indefinido"
        animals_by_sex[label] = animals_by_sex.get(label, 0) + c

    # Recent uploads (de silver.uploads)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    from backend.models import Upload
    log_query = db.query(Upload).filter(Upload.data_upload >= thirty_days_ago)
    if current_user.role != "admin" and current_user.id_farm:
        log_query = log_query.filter(Upload.id_farm == str(current_user.id_farm))
    recent_uploads = log_query.count()

    # Pesos médios das avaliações
    # Buscar últimas avaliações e extrair PD (peso desmama) e PS (peso sobreano)
    latest_evals = db.query(
        GeneticsGeneticEvaluation.animal_id,
        GeneticsGeneticEvaluation.pd_ed,
        GeneticsGeneticEvaluation.ps_ed,
        GeneticsGeneticEvaluation.pa_ed
    ).join(
        GeneticsAnimal, GeneticsAnimal.id == GeneticsGeneticEvaluation.animal_id
    )
    
    if current_user.role != "admin" and current_user.id_farm and genetics_farm:
        latest_evals = latest_evals.filter(GeneticsAnimal.farm_id == genetics_farm.id)
    
    evals = latest_evals.all()
    
    import json
    pd_values = []
    pa_values = []
    ps_values = []
    for e in evals:
        # PD (Desmama ~210d)
        if e.pd_ed:
            try:
                pd = json.loads(e.pd_ed)
                if pd and pd.get('dep') is not None:
                    pd_values.append(float(pd['dep']))
            except: pass
            
        # PA (Ano ~365d)
        if e.pa_ed:
            try:
                pa = json.loads(e.pa_ed)
                if pa and pa.get('dep') is not None:
                    pa_values.append(float(pa['dep']))
            except: pass
            
        # PS (Sobreano ~450d)
        if e.ps_ed:
            try:
                ps = json.loads(e.ps_ed)
                if ps and ps.get('dep') is not None:
                    ps_values.append(float(ps['dep']))
            except: pass
    
    avg_p210 = sum(pd_values) / len(pd_values) if pd_values else None
    avg_p365 = sum(pa_values) / len(pa_values) if pa_values else None
    avg_p450 = sum(ps_values) / len(ps_values) if ps_values else None

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