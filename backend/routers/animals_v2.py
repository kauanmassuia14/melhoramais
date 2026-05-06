from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, String
from typing import Optional, List
import json
import logging

from backend.models import GeneticsAnimal, GeneticsGeneticEvaluation, GeneticsFarm
from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models import User

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/v2/animals", tags=["Animals V2"])


def parse_metric_block(mb_value) -> Optional[dict]:
    """Parse metric_block from database (tuple or text) to dict."""
    if mb_value is None:
        return None
    try:
        # If it's already a tuple (from psycopg2)
        if isinstance(mb_value, tuple):
            return {
                "dep": float(mb_value[0]) if mb_value[0] is not None else None,
                "ac": float(mb_value[1]) if mb_value[1] is not None else None,
                "deca": int(mb_value[2]) if mb_value[2] is not None else None,
                "p_percent": float(mb_value[3]) if mb_value[3] is not None else None,
            }
        # If it's a string (JSON)
        if isinstance(mb_value, str):
            return json.loads(mb_value)
        return None
    except Exception as e:
        logger.warning(f"Error parsing metric_block: {e}")
        return None


@router.get("")
def list_animals(
    farm_id: Optional[str] = Query(None),
    sexo: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(GeneticsAnimal)

    # Filtrar por fazenda do usuário se não for admin
    if current_user.role != "admin" and current_user.id_farm:
        # Precisa converter id_farm integer para UUID
        farm = db.query(GeneticsFarm).join(
            lambda: db.query(GeneticsFarm).filter(
                func.cast(GeneticsFarm.nome, String).like(f"%{current_user.id_farm}%")
            ).subquery()
        ).first()
        if farm:
            query = query.filter(GeneticsAnimal.farm_id == farm.id)

    if farm_id:
        query = query.filter(GeneticsAnimal.farm_id == farm_id)
    if sexo:
        query = query.filter(GeneticsAnimal.sexo == sexo)
    if search:
        query = query.filter(
            (GeneticsAnimal.rgn.ilike(f"%{search}%"))
            | (GeneticsAnimal.nome.ilike(f"%{search}%"))
        )

    total = query.count()
    animals = query.offset(offset).limit(limit).all()

    results = []
    for a in animals:
        eval_query = db.query(GeneticsGeneticEvaluation).filter(
            GeneticsGeneticEvaluation.animal_id == a.id
        )
        latest_eval = eval_query.order_by(GeneticsGeneticEvaluation.safra.desc()).first()

        result = {
            "id": str(a.id),
            "rgn": a.rgn,
            "nome": a.nome,
            "sexo": a.sexo,
            "nascimento": a.nascimento.isoformat() if a.nascimento else None,
            "genotipado": a.genotipado,
            "csg": a.csg,
            "sire_id": str(a.sire_id) if a.sire_id else None,
            "dam_id": str(a.dam_id) if a.dam_id else None,
            "farm_id": str(a.farm_id) if a.farm_id else None,
            "evaluations": []
        }

        if latest_eval:
            result["evaluations"] = [{
                "id": str(latest_eval.id),
                "safra": latest_eval.safra,
                "fonte_origem": latest_eval.fonte_origem,
                "iabczg": float(latest_eval.iabczg) if latest_eval.iabczg else None,
                "deca_index": latest_eval.deca_index,
                "pn": parse_metric_block(latest_eval.pn_ed),
                "pd": parse_metric_block(latest_eval.pd_ed),
                "pa": parse_metric_block(latest_eval.pa_ed),
                "ps": parse_metric_block(latest_eval.ps_ed),
                "pm": parse_metric_block(latest_eval.pm_em),
                "ipp": parse_metric_block(latest_eval.ipp),
                "stay": parse_metric_block(latest_eval.stay),
                "pe_365": parse_metric_block(latest_eval.pe_365),
                "psn": parse_metric_block(latest_eval.psn),
                "aol": parse_metric_block(latest_eval.aol),
                "acab": parse_metric_block(latest_eval.acab),
                "marmoreio": parse_metric_block(latest_eval.marmoreio),
                "eg": parse_metric_block(latest_eval.eg),
                "pg": parse_metric_block(latest_eval.pg),
                "mg": parse_metric_block(latest_eval.mg),
            }]

        results.append(result)

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": results
    }


@router.get("/{animal_id}")
def get_animal(
    animal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    animal = db.query(GeneticsAnimal).filter(GeneticsAnimal.id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    evaluations = db.query(GeneticsGeneticEvaluation).filter(
        GeneticsGeneticEvaluation.animal_id == animal.id
    ).order_by(GeneticsGeneticEvaluation.safra.desc()).all()

    return {
        "id": str(animal.id),
        "rgn": animal.rgn,
        "nome": animal.nome,
        "sexo": animal.sexo,
        "nascimento": animal.nascimento.isoformat() if animal.nascimento else None,
        "genotipado": animal.genotipado,
        "csg": animal.csg,
        "sire_id": str(animal.sire_id) if animal.sire_id else None,
        "dam_id": str(animal.dam_id) if animal.dam_id else None,
        "farm_id": str(animal.farm_id) if animal.farm_id else None,
        "evaluations": [
            {
                "id": str(e.id),
                "safra": e.safra,
                "fonte_origem": e.fonte_origem,
                "iabczg": float(e.iabczg) if e.iabczg else None,
                "deca_index": e.deca_index,
                "pn": parse_metric_block(e.pn_ed),
                "pd": parse_metric_block(e.pd_ed),
                "pa": parse_metric_block(e.pa_ed),
                "ps": parse_metric_block(e.ps_ed),
                "pm": parse_metric_block(e.pm_em),
                "ipp": parse_metric_block(e.ipp),
                "stay": parse_metric_block(e.stay),
                "pe_365": parse_metric_block(e.pe_365),
                "psn": parse_metric_block(e.psn),
                "aol": parse_metric_block(e.aol),
                "acab": parse_metric_block(e.acab),
                "marmoreio": parse_metric_block(e.marmoreio),
                "eg": parse_metric_block(e.eg),
                "pg": parse_metric_block(e.pg),
                "mg": parse_metric_block(e.mg),
            }
            for e in evaluations
        ]
    }


@router.get("/stats/by-farm")
def get_stats_by_farm(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farms = db.query(
        GeneticsFarm.id,
        GeneticsFarm.nome,
        func.count(GeneticsAnimal.id).label("total_animals")
    ).join(
        GeneticsAnimal, GeneticsAnimal.farm_id == GeneticsFarm.id
    ).group_by(
        GeneticsFarm.id, GeneticsFarm.nome
    ).all()

    return [
        {
            "farm_id": str(f.id),
            "farm_name": f.nome,
            "total_animals": f.total_animals
        }
        for f in farms
    ]


@router.get("/stats/ranking")
def get_animal_ranking(
    farm_id: Optional[str] = Query(None),
    metric: str = Query("iabczg"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subquery = db.query(
        GeneticsGeneticEvaluation.animal_id,
        GeneticsGeneticEvaluation.iabczg,
        func.row_number().over(
            partition_by=GeneticsGeneticEvaluation.animal_id,
            order_by=GeneticsGeneticEvaluation.safra.desc()
        ).label("rn")
    ).subquery()

    query = db.query(
        GeneticsAnimal.id,
        GeneticsAnimal.rgn,
        GeneticsAnimal.nome,
        GeneticsAnimal.sexo,
        subquery.c.iabczg
    ).join(
        subquery, subquery.c.animal_id == GeneticsAnimal.id
    ).filter(
        subquery.c.rn == 1
    )

    if farm_id:
        query = query.filter(GeneticsAnimal.farm_id == farm_id)

    if metric == "iabczg":
        query = query.order_by(subquery.c.iabczg.desc())

    results = query.limit(limit).all()

    return [
        {
            "animal_id": str(r.id),
            "rgn": r.rgn,
            "nome": r.nome,
            "sexo": r.sexo,
            "iabczg": float(r.iabczg) if r.iabczg else None
        }
        for r in results
    ]


@router.get("/stats")
def get_stats_v2(
    farm_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard statistics from genetics schema."""
    query = db.query(GeneticsAnimal)
    
    if farm_id:
        query = query.filter(GeneticsAnimal.farm_id == farm_id)
    
    total_animals = query.count()
    
    # Animals by sex
    sex_counts = (
        query.with_entities(GeneticsAnimal.sexo, func.count())
        .group_by(GeneticsAnimal.sexo)
        .all()
    )
    animals_by_sex = {s or "unknown": c for s, c in sex_counts}
    
    # Get evaluations to count by source
    animal_ids = [a.id for a in query.all()]
    source_counts = {}
    if animal_ids:
        eval_counts = (
            db.query(GeneticsGeneticEvaluation.fonte_origem, func.count())
            .filter(GeneticsGeneticEvaluation.animal_id.in_(animal_ids))
            .group_by(GeneticsGeneticEvaluation.fonte_origem)
            .all()
        )
        source_counts = {s or "unknown": c for s, c in eval_counts}
    
    return {
        "total_animals": total_animals,
        "animals_by_sex": animals_by_sex,
        "animals_by_source": source_counts,
    }