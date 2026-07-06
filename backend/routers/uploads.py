from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import io
import asyncio
import uuid
import logging

from backend.models import (
    Upload, User, GeneticsFarm, Animal, ColumnMapping, ProcessingLog, RawAnimalData
)
from backend.database import get_db
from backend.schemas import (
    UploadCreate, UploadResponse, UploadWithAnimalsResponse,
    ColumnMappingCreate, ColumnMappingUpdate, ColumnMappingResponse,
    ProcessingLogResponse, AnimalResponse
)
from backend.auth.dependencies import get_current_user, require_role
from backend.processor import GeneticDataProcessor

logger = logging.getLogger(__name__)

# APIRouter without a prefix so we can register /uploads and /process-genetic-data, /mappings, /logs exactly as they were.
router = APIRouter(tags=["Uploads & Processing"])


# ==============================================================================
# Process Genetic Data
# ==============================================================================
@router.post("/process-genetic-data")
async def process_genetic_data(
    source_system: str = Form(...),
    file: UploadFile = File(...),
    farm_id: str = Form(default=None),
    upload_id: str = Form(default=None),
    download_excel: bool = Form(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "user")),
):
    effective_farm_id = farm_id
    if current_user.role != "admin" and current_user.id_farm:
        effective_farm_id = str(current_user.id_farm)
    
    if upload_id:
        upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        if upload.id_farm != effective_farm_id:
            raise HTTPException(status_code=403, detail="Upload does not belong to this farm")
        if upload.status == "completed":
            raise HTTPException(status_code=400, detail="Upload already processed")

    if not effective_farm_id:
        raise HTTPException(status_code=400, detail="farm_id is required")

    try:
        content = await file.read()
        processor = GeneticDataProcessor(db, farm_id=effective_farm_id, upload_id=upload_id)

        # Run heavy processing in executor thread
        loop = asyncio.get_event_loop()
        df_cleaned, log, upload = await loop.run_in_executor(
            None, 
            processor.process_file, 
            content, 
            file.filename or f"upload_{source_system}", 
            source_system
        )
        
        if log is not None:
            inserted = log.rows_inserted or 0
            updated = log.rows_updated or 0
            failed = log.rows_failed or 0
        elif upload is not None:
            inserted = upload.rows_inserted or 0
            updated = upload.rows_updated or 0
            failed = 0
        else:
            inserted, updated, failed = 0, 0, 0
        
        logger.info(f"Processamento concluído: {len(df_cleaned)} linhas, inserted={inserted}, updated={updated}, failed={failed}")
        
        # Invalidate dashboard cache
        try:
            db.execute(
                text("DELETE FROM genetics.dashboard_stats_cache WHERE farm_id = :fid OR farm_id = 'ALL'"),
                {"fid": str(effective_farm_id)}
            )
            db.commit()
            logger.info(f"Cache do dashboard invalidado com sucesso para a fazenda {effective_farm_id} e ALL")
        except Exception as cache_err:
            logger.error(f"Erro ao invalidar cache do dashboard: {cache_err}")

        if download_excel:
            excel_data = await loop.run_in_executor(
                None,
                processor.generate_formatted_excel,
                df_cleaned
            )

            return StreamingResponse(
                io.BytesIO(excel_data),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=output_tratado_{source_system}.xlsx",
                    "Access-Control-Expose-Headers": "Content-Disposition"
                },
            )
        else:
            return {
                "status": "success",
                "message": "File processed successfully",
                "inserted": inserted,
                "updated": updated,
                "failed": failed,
                "upload_id": upload_id or (upload.upload_id if upload else None)
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# Column Mappings CRUD
# ==============================================================================
@router.get("/mappings", response_model=List[ColumnMappingResponse])
def list_mappings(
    source_system: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ColumnMapping)
    if source_system:
        query = query.filter(ColumnMapping.source_system == source_system)
    return query.all()


@router.post("/mappings", response_model=ColumnMappingResponse, status_code=201)
def create_mapping(
    mapping: ColumnMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    db_mapping = ColumnMapping(**mapping.model_dump())
    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)
    return db_mapping


@router.put("/mappings/{mapping_id}", response_model=ColumnMappingResponse)
def update_mapping(
    mapping_id: int,
    mapping: ColumnMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    db_mapping = db.query(ColumnMapping).filter(ColumnMapping.id == mapping_id).first()
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    update_data = mapping.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_mapping, key, value)
    
    db.commit()
    db.refresh(db_mapping)
    return db_mapping


@router.delete("/mappings/{mapping_id}", status_code=204)
def delete_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    mapping = db.query(ColumnMapping).filter(ColumnMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    db.delete(mapping)
    db.commit()


# ==============================================================================
# Processing Logs
# ==============================================================================
@router.get("/logs", response_model=List[ProcessingLogResponse])
def list_logs(
    farm_id: Optional[int] = Query(None),
    source_system: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ProcessingLog)
    if current_user.role != "admin" and current_user.id_farm:
        query = query.filter(ProcessingLog.id_farm == current_user.id_farm)
    elif farm_id:
        query = query.filter(ProcessingLog.id_farm == farm_id)
    if source_system:
        query = query.filter(ProcessingLog.source_system == source_system)
    return query.order_by(ProcessingLog.started_at.desc()).limit(limit).all()


@router.delete("/logs", status_code=204)
def delete_logs(
    log_ids: List[int] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not log_ids:
        raise HTTPException(status_code=400, detail="No log IDs provided")
    
    logs = db.query(ProcessingLog).filter(ProcessingLog.id.in_(log_ids)).all()
    if not logs:
        raise HTTPException(status_code=404, detail="Logs not found")
    
    for log in logs:
        if current_user.role != "admin" and log.id_farm != current_user.id_farm:
            raise HTTPException(status_code=403, detail=f"Access denied to log {log.id}")
    
    for log in logs:
        log_id = log.id
        
        # Find upload associated with this log via animals
        upload_ids = db.query(Animal.upload_id).filter(
            Animal.id_farm == log.id_farm,
            Animal.processing_log_id == log_id,
            Animal.upload_id.isnot(None)
        ).distinct().all()
        upload_ids = [u[0] for u in upload_ids if u[0]]
        
        db.query(RawAnimalData).filter(
            RawAnimalData.processing_log_id == log_id
        ).delete(synchronize_session=False)
        
        animais = db.query(Animal).filter(
            Animal.id_farm == log.id_farm,
            Animal.processing_log_id == log_id
        ).all()
        animais_ids = [a.id_animal for a in animais]
        
        if animais_ids:
            db.query(RawAnimalData).filter(RawAnimalData.id_animal.in_(animais_ids)).delete(synchronize_session=False)
        
        db.query(Animal).filter(
            Animal.id_farm == log.id_farm,
            Animal.processing_log_id == log_id
        ).delete(synchronize_session=False)
        
        if upload_ids:
            for upload_id in upload_ids:
                upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
                if upload:
                    db.delete(upload)
        
        db.delete(log)
    db.commit()

    # Invalidate dashboard cache
    try:
        for log in logs:
            db.execute(
                text("DELETE FROM genetics.dashboard_stats_cache WHERE farm_id = :fid OR farm_id = 'ALL'"),
                {"fid": str(log.id_farm)}
            )
        db.commit()
    except Exception as cache_err:
        logger.error(f"Erro ao invalidar cache apos delete_logs: {cache_err}")

    return {"message": f"{len(logs)} logs and associated data deleted successfully"}


@router.delete("/logs/{log_id}", status_code=204)
def delete_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(ProcessingLog).filter(ProcessingLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    if current_user.role != "admin" and log.id_farm != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.query(RawAnimalData).filter(
        RawAnimalData.processing_log_id == log_id
    ).delete(synchronize_session=False)
    
    upload_ids = db.query(Animal.upload_id).filter(
        Animal.id_farm == log.id_farm,
        Animal.processing_log_id == log_id,
        Animal.upload_id.isnot(None)
    ).distinct().all()
    upload_ids = [u[0] for u in upload_ids if u[0]]
    
    animais = db.query(Animal).filter(
        Animal.id_farm == log.id_farm,
        Animal.processing_log_id == log_id
    ).all()
    animais_ids = [a.id_animal for a in animais]
    
    if animais_ids:
        db.query(RawAnimalData).filter(RawAnimalData.id_animal.in_(animais_ids)).delete(synchronize_session=False)
    
    db.query(Animal).filter(
        Animal.id_farm == log.id_farm,
        Animal.processing_log_id == log_id
    ).delete(synchronize_session=False)
    
    if upload_ids:
        for upload_id in upload_ids:
            upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
            if upload:
                db.delete(upload)
    
    if upload_ids:
        for upload_id in upload_ids:
            animals = db.execute(
                text("SELECT id FROM genetics.animals WHERE upload_id = :upload_id"),
                {"upload_id": upload_id}
            ).fetchall()
            
            if animals:
                animal_ids = [a[0] for a in animals]
                db.execute(
                    text("DELETE FROM genetics.genetic_evaluations WHERE animal_id = ANY(:animal_ids)"),
                    {"animal_ids": animal_ids}
                )
                db.execute(
                    text("DELETE FROM genetics.animals WHERE upload_id = :upload_id"),
                    {"upload_id": upload_id}
                )
    
    db.delete(log)
    db.commit()

    # Invalidate dashboard cache
    try:
        db.execute(
            text("DELETE FROM genetics.dashboard_stats_cache WHERE farm_id = :fid OR farm_id = 'ALL'"),
            {"fid": str(log.id_farm)}
        )
        db.commit()
    except Exception as cache_err:
        logger.error(f"Erro ao invalidar cache apos delete_log: {cache_err}")

    return {"message": "Log and associated data deleted successfully"}


# ==============================================================================
# Uploads API
# ==============================================================================
@router.post("/uploads", response_model=UploadResponse, status_code=201)
def create_upload(
    upload: UploadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin" and current_user.id_farm != upload.id_farm:
        raise HTTPException(status_code=403, detail="Access denied to this farm")
    
    try:
        farm_uuid = uuid.UUID(upload.id_farm)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid farm ID format")
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


@router.get("/uploads", response_model=List[UploadResponse])
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


@router.get("/uploads/{upload_id}", response_model=UploadWithAnimalsResponse)
def get_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    if current_user.role != "admin" and upload.id_farm != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    farm_nome = "Unknown"
    if upload.id_farm:
        try:
            farm_uuid = uuid.UUID(upload.id_farm)
            farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
            if farm:
                farm_nome = farm.nome
        except (ValueError, AttributeError):
            pass
    
    animais = (
        db.query(Animal)
        .filter(Animal.upload_id == upload_id)
        .order_by(Animal.id_animal.desc())
        .limit(100)
        .all()
    )
    
    total_animais = db.query(Animal).filter(Animal.upload_id == upload_id).count()
    
    return UploadWithAnimalsResponse(
        upload=UploadResponse.model_validate(upload),
        farm_nome=farm_nome,
        animais_preview=[AnimalResponse.model_validate(a) for a in animais],
        total_animais=total_animais,
    )


@router.delete("/uploads/{upload_id}", status_code=204)
def delete_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    if current_user.role != "admin" and upload.id_farm != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 1. Try to delete legacy data safely
    try:
        animais_ids = [a.id_animal for a in db.query(Animal.id_animal).filter(Animal.upload_id == upload_id).all()]
        if animais_ids:
            db.query(RawAnimalData).filter(RawAnimalData.id_animal.in_(animais_ids)).delete(synchronize_session=False)
        db.query(Animal).filter(Animal.upload_id == upload_id).delete(synchronize_session=False)
        db.flush()
    except Exception as e:
        logger.warning(f"Bypassing legacy silver animal deletion because table doesn't exist: {e}")
        db.rollback()
        upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found after transaction rollback")
    
    # 2. Delete genetics.animals and genetics.genetic_evaluations
    try:
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
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting genetics data: {e}")
        raise HTTPException(status_code=500, detail=f"Database error deleting genetics data: {str(e)}")
    
    # 3. Delete upload entry
    try:
        db.delete(upload)
        db.commit()

        # Invalidate cache
        try:
            db.execute(
                text("DELETE FROM genetics.dashboard_stats_cache WHERE farm_id = :fid OR farm_id = 'ALL'"),
                {"fid": str(upload.id_farm)}
            )
            db.commit()
        except Exception as cache_err:
            logger.error(f"Erro ao invalidar cache apos delete_upload: {cache_err}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error finalizing upload deletion: {e}")
        raise HTTPException(status_code=500, detail=f"Database error during commit: {str(e)}")
    
    return {"message": "Upload and associated data deleted successfully"}


@router.delete("/uploads/{upload_id}/genetics", status_code=200)
def delete_upload_genetics(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    if current_user.role != "admin" and upload.id_farm != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    animals = db.execute(
        text("SELECT id FROM genetics.animals WHERE upload_id = :upload_id"),
        {"upload_id": upload_id}
    ).fetchall()
    
    animal_ids = [a[0] for a in animals]
    
    if animal_ids:
        db.execute(
            text("DELETE FROM genetics.genetic_evaluations WHERE animal_id = ANY(:animal_ids)"),
            {"animal_ids": animal_ids}
        )
        db.execute(
            text("DELETE FROM genetics.animals WHERE upload_id = :upload_id"),
            {"upload_id": upload_id}
        )
    
    db.commit()
    
    # Invalidate cache
    try:
        db.execute(
            text("DELETE FROM genetics.dashboard_stats_cache WHERE farm_id = :fid OR farm_id = 'ALL'"),
            {"fid": str(upload.id_farm)}
        )
        db.commit()
    except Exception as cache_err:
        logger.error(f"Erro ao invalidar cache apos delete_upload_genetics: {cache_err}")
    
    return {"message": f"Deleted {len(animal_ids)} genetics animals and their evaluations"}