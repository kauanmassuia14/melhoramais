from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Optional
import json
import logging

from backend.models import GeneticsAnimal, GeneticsGeneticEvaluation, GeneticsFarm
from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/animals", tags=["Animals V2"])


def parse_metric_block(mb_value) -> Optional[dict]:
    """Parse metric_block from database (tuple or JSON text) to dict."""
    if mb_value is None or mb_value == "":
        return None
    try:
        if isinstance(mb_value, tuple):
            return {
                "dep": float(mb_value[0]) if mb_value[0] is not None else None,
                "ac": float(mb_value[1]) if mb_value[1] is not None else None,
                "deca": int(mb_value[2]) if mb_value[2] is not None else None,
                "p_percent": float(mb_value[3]) if mb_value[3] is not None else None,
            }
        if isinstance(mb_value, str):
            return json.loads(mb_value)
        return None
    except Exception as e:
        logger.warning(f"Error parsing metric_block: {e}")
        return None


def animal_to_dict(a: GeneticsAnimal, latest_eval: Optional[GeneticsGeneticEvaluation] = None) -> dict:
    """Converte GeneticsAnimal para dict compatível com o frontend."""
    result = {
        "id": str(a.id),
        "rgn": a.rgn,
        "serie": a.serie,
        "nome": a.nome,
        "sexo": a.sexo,
        "nascimento": a.nascimento.isoformat() if a.nascimento else None,
        "genotipado": a.genotipado,
        "csg": a.csg,
        "sire_id": str(a.sire_id) if a.sire_id else None,
        "dam_id": str(a.dam_id) if a.dam_id else None,
        "farm_id": str(a.farm_id) if a.farm_id else None,
        "evaluations": [],
    }

    if latest_eval:
        result["p210_info"] = parse_metric_block(latest_eval.p210_info)
        result["p365_info"] = parse_metric_block(latest_eval.p365_info)
        result["p450_info"] = parse_metric_block(latest_eval.p450_info)
        result["evaluations"] = [eval_to_dict(latest_eval)]
    else:
        result["p210_info"] = None
        result["p365_info"] = None
        result["p450_info"] = None

    return result


def eval_to_dict(e: GeneticsGeneticEvaluation) -> dict:
    return {
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
        "p120_info": parse_metric_block(e.p120_info),
        "p210_info": parse_metric_block(e.p210_info),
        "p365_info": parse_metric_block(e.p365_info),
        "p450_info": parse_metric_block(e.p450_info),
    }


# ============================================================
# ROTAS ESTÁTICAS — devem vir ANTES de /{animal_id}
# ============================================================

@router.get("/stats/by-farm")
def get_stats_by_farm(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farms = db.query(
        GeneticsFarm.id,
        GeneticsFarm.nome,
        func.count(GeneticsAnimal.id).label("total_animals")
    ).outerjoin(
        GeneticsAnimal, GeneticsAnimal.farm_id == GeneticsFarm.id
    ).group_by(
        GeneticsFarm.id, GeneticsFarm.nome
    ).all()

    return [
        {
            "farm_id": str(f.id),
            "farm_name": f.nome,
            "total_animals": f.total_animals,
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
    ).filter(subquery.c.rn == 1)

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
            "iabczg": float(r.iabczg) if r.iabczg else None,
        }
        for r in results
    ]


@router.get("/stats")
def get_stats_v2(
    farm_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Estatísticas do dashboard vindas do schema genetics."""
    query = db.query(GeneticsAnimal)

    if farm_id:
        query = query.filter(GeneticsAnimal.farm_id == farm_id)
    elif current_user.role != "admin" and current_user.id_farm:
        query = query.filter(GeneticsAnimal.farm_id == current_user.id_farm)

    total_animals = query.count()

    sex_counts = (
        query.with_entities(GeneticsAnimal.sexo, func.count())
        .group_by(GeneticsAnimal.sexo)
        .all()
    )
    animals_by_sex = {s or "unknown": c for s, c in sex_counts}

    animal_ids = [a.id for a in query.with_entities(GeneticsAnimal.id).all()]
    source_counts = {}
    avg_p210 = avg_p365 = avg_p450 = None

    if animal_ids:
        eval_counts = (
            db.query(GeneticsGeneticEvaluation.fonte_origem, func.count())
            .filter(GeneticsGeneticEvaluation.animal_id.in_(animal_ids))
            .group_by(GeneticsGeneticEvaluation.fonte_origem)
            .all()
        )
        source_counts = {s or "unknown": c for s, c in eval_counts}

        # Médias de pesos via JSON fields
        p210 = db.execute(
            text("""
                SELECT AVG((p210_info->>'dep')::numeric)
                FROM genetics.genetic_evaluations
                WHERE animal_id = ANY(:ids)
                AND p210_info IS NOT NULL
                AND (p210_info->>'dep') IS NOT NULL
            """),
            {"ids": animal_ids}
        ).scalar()

        p365 = db.execute(
            text("""
                SELECT AVG((p365_info->>'dep')::numeric)
                FROM genetics.genetic_evaluations
                WHERE animal_id = ANY(:ids)
                AND p365_info IS NOT NULL
                AND (p365_info->>'dep') IS NOT NULL
            """),
            {"ids": animal_ids}
        ).scalar()

        p450 = db.execute(
            text("""
                SELECT AVG((p450_info->>'dep')::numeric)
                FROM genetics.genetic_evaluations
                WHERE animal_id = ANY(:ids)
                AND p450_info IS NOT NULL
                AND (p450_info->>'dep') IS NOT NULL
            """),
            {"ids": animal_ids}
        ).scalar()

        avg_p210 = round(float(p210), 2) if p210 else None
        avg_p365 = round(float(p365), 2) if p365 else None
        avg_p450 = round(float(p450), 2) if p450 else None

    return {
        "total_animals": total_animals,
        "animals_by_sex": animals_by_sex,
        "animals_by_source": source_counts,
        "avg_p210": avg_p210,
        "avg_p365": avg_p365,
        "avg_p450": avg_p450,
    }


# ============================================================
# LISTAGEM
# ============================================================

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

    if farm_id:
        query = query.filter(GeneticsAnimal.farm_id == farm_id)
    elif current_user.role != "admin" and current_user.id_farm:
        query = query.filter(GeneticsAnimal.farm_id == current_user.id_farm)

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
        latest_eval = (
            db.query(GeneticsGeneticEvaluation)
            .filter(GeneticsGeneticEvaluation.animal_id == a.id)
            .order_by(GeneticsGeneticEvaluation.safra.desc())
            .first()
        )
        results.append(animal_to_dict(a, latest_eval))

    return {"total": total, "limit": limit, "offset": offset, "data": results}


# ============================================================
# ROTA DINÂMICA — DEVE VIR POR ÚLTIMO
# ============================================================

@router.get("/{animal_id}")
def get_animal(
    animal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        import uuid as _uuid
        animal_uuid = _uuid.UUID(animal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"ID inválido: '{animal_id}' não é um UUID válido")

    animal = db.query(GeneticsAnimal).filter(GeneticsAnimal.id == animal_uuid).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")

    evaluations = (
        db.query(GeneticsGeneticEvaluation)
        .filter(GeneticsGeneticEvaluation.animal_id == animal.id)
        .order_by(GeneticsGeneticEvaluation.safra.desc())
        .all()
    )

    result = animal_to_dict(animal)
    result["evaluations"] = [eval_to_dict(e) for e in evaluations]
    return result