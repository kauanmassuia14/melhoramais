from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Any
import json

from backend.models import GeneticsAnimal, GeneticsGeneticEvaluation, User
from backend.database import get_db
from backend.auth.dependencies import get_current_user


router = APIRouter(prefix="/animals", tags=["Animals"])


def parse_metric_block(mb_text: Optional[str]) -> Optional[dict]:
    if not mb_text:
        return None
    try:
        return json.loads(mb_text)
    except:
        return None


@router.get("")
def list_animals(
    farm_id: Optional[int] = Query(None),
    source: Optional[str] = Query(None),
    sexo: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.models import GeneticsFarm
    from sqlalchemy import func, cast, String
    
    query = db.query(GeneticsAnimal)

    # Filtrar por farm usando UUID diretamente (genetics schema)
    if current_user.role != "admin" and current_user.id_farm:
        import uuid as _uuid
        try:
            farm_uuid = _uuid.UUID(str(current_user.id_farm))
            query = query.filter(GeneticsAnimal.farm_id == farm_uuid)
        except (ValueError, AttributeError):
            pass
    elif farm_id is not None:
        # farm_id pode ser passado como UUID string na query param
        import uuid as _uuid
        try:
            farm_uuid = _uuid.UUID(str(farm_id))
            query = query.filter(GeneticsAnimal.farm_id == farm_uuid)
        except (ValueError, AttributeError):
            pass

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
        # Buscar última avaliação
        eval_query = db.query(GeneticsGeneticEvaluation).filter(
            GeneticsGeneticEvaluation.animal_id == a.id
        )
        if source:
            eval_query = eval_query.filter(GeneticsGeneticEvaluation.fonte_origem == source)
        
        latest_eval = eval_query.order_by(GeneticsGeneticEvaluation.safra.desc()).first()
        
        metrics = latest_eval.metrics or {}
        if isinstance(metrics, str):
            try: metrics = json.loads(metrics)
            except: metrics = {}

        # Helper para extrair DEP de blocos PMGZ ou ANCP
        def get_dep(key_pmgz, key_ancp):
            m = metrics.get(key_pmgz) or metrics.get(key_ancp)
            return m.get("dep") if m else None

        result = {
            "id_animal": 0,  # Legacy field
            "id_farm": current_user.id_farm or 0,
            "rgn_animal": a.rgn,
            "nome_animal": a.nome,
            "sexo": a.sexo,
            "data_nascimento": a.nascimento.isoformat() if a.nascimento else None,
            "fonte_origem": latest_eval.fonte_origem if latest_eval else None,
            "genotipado": a.genotipado,
            "csg": a.csg,
            # DEP do genetics (Mapeia para os campos esperados pelo front legado)
            "pmg_iabc": float(latest_eval.indice_principal) if latest_eval and latest_eval.indice_principal else None,
            "pmg_pn_dep": get_dep("PN-EDg", "DPN"),
            "pmg_pd_dep": get_dep("PD-EDg", "DP210"),
            "pmg_ps_dep": get_dep("PS-EDg", "DP450"),
            "pmg_aol_dep": get_dep("AOLg", "DAOL"),
            "pmg_acab_dep": get_dep("ACABg", "DACAB"),
            "pmg_ipp_dep": get_dep("IPPg", "DIPP"),
            "pmg_stay_dep": get_dep("STAYg", "DSTAY"),
        }
        results.append(result)

    return results


@router.get("/{animal_id}")
def get_animal(
    animal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Este endpoint espera animal_id como UUID agora
    raise HTTPException(status_code=404, detail="Use /v2/animals/{id} for genetics data")