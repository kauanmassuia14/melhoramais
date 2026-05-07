from fastapi import APIRouter, Depends, HTTPException, Query, Body
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
    """Parse metric_block: suporta JSON, tuple PostgreSQL '(dep,ac,deca,p_pct)' e None."""
    if mb_value is None:
        return None
    if isinstance(mb_value, str):
        mb_value = mb_value.strip()
        if not mb_value:
            return None
        # Formato tuple PostgreSQL: '(0.87,36.0,10,)'
        if mb_value.startswith('(') and mb_value.endswith(')'):
            try:
                inner = mb_value[1:-1]  # remove parênteses
                parts = inner.split(',')
                return {
                    "dep": float(parts[0]) if parts[0].strip() else None,
                    "ac": float(parts[1]) if len(parts) > 1 and parts[1].strip() else None,
                    "deca": int(float(parts[2])) if len(parts) > 2 and parts[2].strip() else None,
                    "p_percent": float(parts[3]) if len(parts) > 3 and parts[3].strip() else None,
                }
            except Exception as e:
                logger.warning(f"Error parsing tuple metric_block '{mb_value}': {e}")
                return None
        # Formato JSON
        try:
            return json.loads(mb_value)
        except Exception as e:
            logger.warning(f"Error parsing JSON metric_block '{mb_value[:30]}': {e}")
            return None
    # Tuple Python já parsed
    if isinstance(mb_value, tuple):
        try:
            return {
                "dep": float(mb_value[0]) if mb_value[0] is not None else None,
                "ac": float(mb_value[1]) if len(mb_value) > 1 and mb_value[1] is not None else None,
                "deca": int(mb_value[2]) if len(mb_value) > 2 and mb_value[2] is not None else None,
                "p_percent": float(mb_value[3]) if len(mb_value) > 3 and mb_value[3] is not None else None,
            }
        except Exception as e:
            logger.warning(f"Error parsing tuple: {e}")
            return None
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
        eval_dict = eval_to_dict(latest_eval)
        result["evaluations"] = [eval_dict]
        # Helper fields for the list view
        result["latest_eval"] = eval_dict
    else:
        result["latest_eval"] = None

    return result


def eval_to_dict(e: GeneticsGeneticEvaluation) -> dict:
    # Basic metrics mapping for frontend backward compatibility
    metrics = e.metrics if isinstance(e.metrics, dict) else {}
    if isinstance(e.metrics, str):
        try:
            metrics = json.loads(e.metrics)
        except:
            metrics = {}

    # Compatibility mapping: map platform-specific names to standard frontend fields
    pn = None
    pd = None
    ps = None
    
    if e.fonte_origem == "PMGZ":
        pn = metrics.get("PN-EDg")
        pd = metrics.get("PD-EDg")
        ps = metrics.get("PS-EDg")
    elif e.fonte_origem == "ANCP":
        pn = metrics.get("DPN")
        pd = metrics.get("DP210")
        ps = metrics.get("DP450")
    elif e.fonte_origem == "GENEPLUS":
        pn = metrics.get("PN")
        pd = metrics.get("PD")
        ps = metrics.get("PS")

    return {
        "id": str(e.id),
        "safra": e.safra,
        "fonte_origem": e.fonte_origem,
        "iabczg": float(e.indice_principal) if e.indice_principal else (float(e.iabczg) if hasattr(e, 'iabczg') and e.iabczg else None),
        "deca_index": e.rank_principal if e.rank_principal else (e.deca_index if hasattr(e, 'deca_index') else None),
        "metrics": metrics,
        "pn": pn,
        "pd": pd,
        "ps": ps,
        # Legacy fields (returning None or mapping if possible)
        "pa": metrics.get("PA-EDg") if e.fonte_origem == "PMGZ" else None,
        "pm": metrics.get("PM-EMg") if e.fonte_origem == "PMGZ" else None,
        "ipp": metrics.get("IPPg"),
        "stay": metrics.get("STAYg"),
        "pe_365": metrics.get("PE-365g"),
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

        # Médias de pesos: usa o campo metrics (JSONB)
        # Tenta pegar PD (Desmama) e PS (Sobreano) dependendo da fonte
        p210 = db.execute(
            text("""
                SELECT AVG(
                    CASE 
                        WHEN fonte_origem = 'PMGZ' THEN (metrics->'PD-EDg'->>'dep')::numeric
                        WHEN fonte_origem = 'ANCP' THEN (metrics->'DP210'->>'dep')::numeric
                        ELSE NULL
                    END
                )
                FROM genetics.genetic_evaluations
                WHERE animal_id = ANY(:ids)
            """),
            {"ids": animal_ids}
        ).scalar()
        
        # P365 (Ano)
        p365 = db.execute(
            text("""
                SELECT AVG(
                    CASE 
                        WHEN fonte_origem = 'PMGZ' THEN (metrics->'PA-EDg'->>'dep')::numeric
                        WHEN fonte_origem = 'ANCP' THEN (metrics->'DP365'->>'dep')::numeric
                        ELSE NULL
                    END
                )
                FROM genetics.genetic_evaluations
                WHERE animal_id = ANY(:ids)
            """),
            {"ids": animal_ids}
        ).scalar()

        # P450 (Sobreano)
        p450 = db.execute(
            text("""
                SELECT AVG(
                    CASE 
                        WHEN fonte_origem = 'PMGZ' THEN (metrics->'PS-EDg'->>'dep')::numeric
                        WHEN fonte_origem = 'ANCP' THEN (metrics->'DP450'->>'dep')::numeric
                        ELSE NULL
                    END
                )
                FROM genetics.genetic_evaluations
                WHERE animal_id = ANY(:ids)
            """),
            {"ids": animal_ids}
        ).scalar()

        avg_p210 = round(float(p210), 2) if p210 else None
        avg_p365 = round(float(p365), 2) if p365 else None
        avg_p450 = round(float(p450), 2) if p450 else None

    if current_user.role == "admin":
        total_farms = db.query(GeneticsFarm).count()
    else:
        total_farms = 1 if current_user.id_farm else 0

    from backend.models import Upload
    from datetime import timedelta, timezone
    thirty_days_ago = __import__('datetime').datetime.now(timezone.utc) - timedelta(days=30)
    uploads_query = db.query(Upload).filter(Upload.data_upload >= thirty_days_ago)
    if current_user.role != "admin" and current_user.id_farm:
        uploads_query = uploads_query.filter(Upload.id_farm == str(current_user.id_farm))
    recent_uploads = uploads_query.count()

    return {
        "total_animals": total_animals,
        "total_farms": total_farms,
        "recent_uploads": recent_uploads,
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


@router.delete("/bulk", status_code=204)
def bulk_delete_animals(
    animal_ids: list[str] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exclui múltiplos animais e suas avaliações genéticas."""
    if not animal_ids:
        raise HTTPException(status_code=400, detail="Nenhum ID de animal fornecido")
    
    import uuid as _uuid
    try:
        uuids = [_uuid.UUID(aid) for aid in animal_ids]
    except ValueError:
        raise HTTPException(status_code=400, detail="Um ou mais IDs são inválidos")
    
    # Buscar animais para verificar permissão
    animals = db.query(GeneticsAnimal).filter(GeneticsAnimal.id.in_(uuids)).all()
    if not animals:
        raise HTTPException(status_code=404, detail="Animais não encontrados")
    
    # Verificar permissão
    for animal in animals:
        if current_user.role != "admin" and str(animal.farm_id) != str(current_user.id_farm):
            raise HTTPException(status_code=403, detail=f"Acesso negado para o animal {animal.rgn}")
    
    # Excluir avaliações primeiro
    db.query(GeneticsGeneticEvaluation).filter(GeneticsGeneticEvaluation.animal_id.in_(uuids)).delete(synchronize_session=False)
    
    # Excluir animais
    db.query(GeneticsAnimal).filter(GeneticsAnimal.id.in_(uuids)).delete(synchronize_session=False)
    
    db.commit()
    return None


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