from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import io
import asyncio
import uuid

from backend.models import Upload, User, GeneticsFarm, Animal
from backend.database import get_db
from backend.schemas import (
    UploadCreate, UploadResponse, UploadWithAnimalsResponse,
)
from backend.auth.dependencies import get_current_user, require_role
from backend.processor import GeneticDataProcessor


router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post("", response_model=UploadResponse, status_code=201)
def create_upload(
    upload: UploadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        farm_uuid = uuid.UUID(upload.id_farm)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid farm ID format")
    
    if current_user.role != "admin" and str(current_user.id_farm) != upload.id_farm:
        raise HTTPException(status_code=403, detail="Access denied to this farm")
    
    farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    db_upload = Upload(
        nome=upload.nome,
        id_farm=upload.id_farm,
        fonte_origem=upload.fonte_origem,
        arquivo_nome_original=upload.arquivo_nome_original,
        arquivo_hash=upload.arquivo_hash,
        usuario_id=current_user.id,
        status="processing",
    )
    db.add(db_upload)
    db.commit()
    db.refresh(db_upload)
    return db_upload


@router.get("", response_model=List[UploadResponse])
def list_uploads(
    farm_id: Optional[str] = Query(None),
    fonte_origem: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Upload)
    
    if current_user.role != "admin" and current_user.id_farm:
        query = query.filter(Upload.id_farm == str(current_user.id_farm))
    elif farm_id:
        query = query.filter(Upload.id_farm == farm_id)
    
    if fonte_origem:
        query = query.filter(Upload.fonte_origem == fonte_origem)
    if status:
        query = query.filter(Upload.status == status)
    
    return query.order_by(Upload.data_upload.desc()).offset(offset).limit(limit).all()


@router.get("/{upload_id}", response_model=UploadWithAnimalsResponse)
def get_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    if current_user.role != "admin" and str(current_user.id_farm) != upload.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    farm = None
    farm_nome = "Unknown"
    if upload.id_farm:
        try:
            farm_uuid = uuid.UUID(upload.id_farm)
            farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
            if farm:
                farm_nome = farm.nome
        except ValueError:
            pass
    
    from backend.models import Animal
    animais = (
        db.query(Animal)
        .filter(Animal.upload_id == upload_id)
        .order_by(Animal.id_animal.desc())
        .limit(100)
        .all()
    )
    
    total_animais = db.query(Animal).filter(Animal.upload_id == upload_id).count()
    
    from backend.schemas import AnimalResponse
    return UploadWithAnimalsResponse(
        upload=UploadResponse.model_validate(upload),
        farm_nome=farm_nome,
        animais_preview=[AnimalResponse.model_validate(a) for a in animais],
        total_animais=total_animais,
    )


@router.delete("/{upload_id}", status_code=204)
def delete_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    if current_user.role != "admin" and str(current_user.id_farm) != upload.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from backend.models import Animal, RawAnimalData
    
    # Get animal IDs before deletion
    animais_ids = [a.id_animal for a in db.query(Animal.id_animal).filter(Animal.upload_id == upload_id).all()]
    
    # Delete raw animal data
    if animais_ids:
        db.query(RawAnimalData).filter(RawAnimalData.id_animal.in_(animais_ids)).delete(synchronize_session=False)

    # Delete animals
    db.query(Animal).filter(Animal.upload_id == upload_id).delete(synchronize_session=False)
    
    # Delete genetics.animals and genetics.genetic_evaluations
    genetics_animals = db.execute(
        text("SELECT id FROM genetics.animals WHERE upload_id = :upload_id"),
        {"upload_id": upload_id}
    ).fetchall()
    
    if genetics_animals:
        animal_ids = [a[0] for a in genetics_animals]
        db.execute(
            text("DELETE FROM genetics.genetic_evaluations WHERE animal_id = ANY(:animal_ids)"),
            {"animal_ids": animal_ids}
        )
        db.execute(
            text("DELETE FROM genetics.animals WHERE upload_id = :upload_id"),
            {"upload_id": upload_id}
        )
    
    # Delete upload
    db.delete(upload)
    db.commit()
    
    return {"message": "Upload and associated data deleted successfully"}