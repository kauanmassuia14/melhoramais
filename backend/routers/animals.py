from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from backend.models import Animal, User
from backend.database import get_db
from backend.schemas import AnimalResponse
from backend.auth.dependencies import get_current_user


router = APIRouter(prefix="/animals", tags=["Animals"])


@router.get("", response_model=List[AnimalResponse])
def list_animals(
    farm_id: Optional[int] = Query(None),
    source: Optional[str] = Query(None),
    raca: Optional[str] = Query(None),
    sexo: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Animal)

    if current_user.role != "admin" and current_user.id_farm:
        query = query.filter(Animal.id_farm == current_user.id_farm)
    elif farm_id is not None:
        query = query.filter(Animal.id_farm == farm_id)

    if source:
        query = query.filter(Animal.fonte_origem == source)
    if raca:
        query = query.filter(Animal.raca == raca)
    if sexo:
        query = query.filter(Animal.sexo == sexo)
    if search:
        query = query.filter(
            (Animal.rgn_animal.ilike(f"%{search}%"))
            | (Animal.nome_animal.ilike(f"%{search}%"))
        )

    return query.offset(offset).limit(limit).all()


@router.get("/{animal_id}", response_model=AnimalResponse)
def get_animal(
    animal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    animal = db.query(Animal).filter(Animal.id_animal == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    if current_user.role != "admin" and current_user.id_farm != animal.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    return animal