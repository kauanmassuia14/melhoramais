from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from backend.models import Farm, GeneticsFarm, User
from backend.database import get_db
from backend.schemas import (
    FarmCreate, FarmUpdate, FarmResponse, FarmResponseFromGenetics,
)
from backend.auth.dependencies import get_current_user, require_role


router = APIRouter(prefix="/farms", tags=["Farms"])


@router.post("", response_model=FarmResponseFromGenetics, status_code=201)
def create_farm(
    farm: FarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    import uuid
    db_farm = GeneticsFarm(
        id=uuid.uuid4(),
        nome=farm.nome_farm,
        documento=farm.cnpj,
    )
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return {
        "id_farm": str(db_farm.id),
        "nome_farm": db_farm.nome,
        "cnpj": db_farm.documento,
        "responsavel": None,
        "email": None,
        "created_at": db_farm.created_at,
    }


@router.get("", response_model=List[FarmResponseFromGenetics])
def list_farms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farms = db.query(GeneticsFarm).all()
    return [
        {
            "id_farm": str(f.id),
            "nome_farm": f.nome,
            "cnpj": f.documento,
            "responsavel": None,
            "email": None,
            "created_at": f.created_at,
        }
        for f in farms
    ]


@router.get("/{farm_id}", response_model=FarmResponseFromGenetics)
def get_farm(
    farm_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    try:
        farm_uuid = uuid.UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid farm ID format")

    farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    return {
        "id_farm": str(farm.id),
        "nome_farm": farm.nome,
        "cnpj": farm.documento,
        "responsavel": None,
        "email": None,
        "created_at": farm.created_at,
    }


@router.put("/{farm_id}", response_model=FarmResponseFromGenetics)
def update_farm(
    farm_id: str,
    farm: FarmUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    try:
        farm_uuid = uuid.UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid farm ID format")

    db_farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
    if not db_farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    if farm.nome_farm:
        db_farm.nome = farm.nome_farm
    if farm.cnpj:
        db_farm.documento = farm.cnpj
    if farm.responsavel:
        pass
    if farm.email:
        pass

    db.commit()
    db.refresh(db_farm)

    return {
        "id_farm": str(db_farm.id),
        "nome_farm": db_farm.nome,
        "cnpj": db_farm.documento,
        "responsavel": None,
        "email": None,
        "created_at": db_farm.created_at,
    }


@router.delete("/{farm_id}")
def delete_farm(
    farm_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    import uuid
    try:
        farm_uuid = uuid.UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid farm ID format")

    farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    from sqlalchemy import text
    animal_ids = db.execute(
        text("SELECT id FROM genetics.animals WHERE farm_id = :farm_id"),
        {"farm_id": str(farm_uuid)}
    ).fetchall()
    animal_ids = [a[0] for a in animal_ids]

    if animal_ids:
        db.execute(
            text("DELETE FROM genetics.genetic_evaluations WHERE animal_id = ANY(:ids)"),
            {"ids": animal_ids}
        )
        db.execute(
            text("DELETE FROM genetics.animals WHERE farm_id = :farm_id"),
            {"farm_id": str(farm_uuid)}
        )

    db.delete(farm)
    db.commit()
    return {"message": "Farm deleted successfully"}