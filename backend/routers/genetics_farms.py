from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import uuid

from backend.models import GeneticsFarm, User
from backend.database import get_db
from backend.schemas import GeneticsFarmCreate, GeneticsFarmUpdate, GeneticsFarmResponse
from backend.auth.dependencies import get_current_user, require_role


router = APIRouter(prefix="/genetics/farms", tags=["Genetics Farms"])


@router.post("", response_model=GeneticsFarmResponse, status_code=201)
def create_farm(
    farm: GeneticsFarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    db_farm = GeneticsFarm(
        id=uuid.uuid4(),
        nome=farm.nome,
        dono_fazenda=farm.dono_fazenda,
    )
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return db_farm


@router.get("", response_model=List[GeneticsFarmResponse])
def list_farms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return db.query(GeneticsFarm).all()
    if current_user.id_farm:
        return db.query(GeneticsFarm).all()
    return []


@router.get("/{farm_id}", response_model=GeneticsFarmResponse)
def get_farm(
    farm_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        farm_uuid = uuid.UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid farm ID format")

    farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.put("/{farm_id}", response_model=GeneticsFarmResponse)
def update_farm(
    farm_id: str,
    farm: GeneticsFarmUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        farm_uuid = uuid.UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid farm ID format")

    db_farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
    if not db_farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    update_data = farm.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_farm, key, value)

    db.commit()
    db.refresh(db_farm)
    return db_farm


@router.delete("/{farm_id}")
def delete_farm(
    farm_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    try:
        farm_uuid = uuid.UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid farm ID format")

    farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

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