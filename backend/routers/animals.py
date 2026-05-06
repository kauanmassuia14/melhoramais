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

    # Mapear id_farm para genetics se necessário
    if current_user.role != "admin" and current_user.id_farm:
        from backend.models import Farm as SilverFarm
        silver_farm = db.query(SilverFarm).filter(SilverFarm.id_farm == current_user.id_farm).first()
        if silver_farm:
            genetics_farm = db.query(GeneticsFarm).filter(
                GeneticsFarm.nome.ilike(f"%{silver_farm.nome_farm}%")
            ).first()
            if genetics_farm:
                query = query.filter(GeneticsAnimal.farm_id == genetics_farm.id)
    elif farm_id is not None:
        from backend.models import Farm as SilverFarm
        silver_farm = db.query(SilverFarm).filter(SilverFarm.id_farm == farm_id).first()
        if silver_farm:
            genetics_farm = db.query(GeneticsFarm).filter(
                GeneticsFarm.nome.ilike(f"%{silver_farm.nome_farm}%")
            ).first()
            if genetics_farm:
                query = query.filter(GeneticsAnimal.farm_id == genetics_farm.id)

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
            # DEP do genetics
            "pmg_iabc": float(latest_eval.iabczg) if latest_eval and latest_eval.iabczg else None,
            "pmg_pn_dep": parse_metric_block(latest_eval.pn_ed)["dep"] if latest_eval and latest_eval.pn_ed else None,
            "pmg_pd_dep": parse_metric_block(latest_eval.pd_ed)["dep"] if latest_eval and latest_eval.pd_ed else None,
            "pmg_ps_dep": parse_metric_block(latest_eval.ps_ed)["dep"] if latest_eval and latest_eval.ps_ed else None,
            "pmg_aol_dep": parse_metric_block(latest_eval.aol)["dep"] if latest_eval and latest_eval.aol else None,
            "pmg_acab_dep": parse_metric_block(latest_eval.acab)["dep"] if latest_eval and latest_eval.acab else None,
            "pmg_ipp_dep": parse_metric_block(latest_eval.ipp)["dep"] if latest_eval and latest_eval.ipp else None,
            "pmg_stay_dep": parse_metric_block(latest_eval.stay)["dep"] if latest_eval and latest_eval.stay else None,
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