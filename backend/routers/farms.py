from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from backend.models import Farm, User
from backend.database import get_db
from backend.schemas import (
    FarmCreate, FarmUpdate, FarmResponse,
)
from backend.auth.dependencies import get_current_user, require_role


router = APIRouter(prefix="/farms", tags=["Farms"])


@router.post("", response_model=FarmResponse, status_code=201)
def create_farm(
    farm: FarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    db_farm = Farm(**farm.model_dump())
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return db_farm


@router.get("", response_model=List[FarmResponse])
def list_farms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return db.query(Farm).all()
    if current_user.id_farm:
        return db.query(Farm).filter(Farm.id_farm == current_user.id_farm).all()
    return []


@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm = db.query(Farm).filter(Farm.id_farm == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if current_user.role != "admin" and current_user.id_farm != farm_id:
        raise HTTPException(status_code=403, detail="Access denied to this farm")
    return farm


@router.put("/{farm_id}", response_model=FarmResponse)
def update_farm(
    farm_id: int,
    farm: FarmUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin" and current_user.id_farm != farm_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db_farm = db.query(Farm).filter(Farm.id_farm == farm_id).first()
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
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    db_farm = db.query(Farm).filter(Farm.id_farm == farm_id).first()
    if not db_farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    db.delete(db_farm)
    db.commit()
    return {"message": "Farm deleted successfully"}