import logging
from typing import Tuple
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from backend.loaders import PMGZLoader
from backend.models_pmgz import AnimalPMGZ
from backend.models import ProcessingLog, Upload, IS_SQLITE
from backend.database import SessionLocal

logger = logging.getLogger(__name__)


class PMGZProcessor:
    """Processador específico para dados PMGZ usando o novo loader."""

    def __init__(self, db: Session, farm_id: int = 1, upload_id: str = None):
        self.db = db
        self.farm_id = farm_id
        self.upload_id = upload_id
        self.upload_log_id = None

    def process_file(
        self, file_content: bytes, filename: str
    ) -> Tuple[pd.DataFrame, ProcessingLog, Upload]:
        """Executa o pipeline completo de processamento PMGZ."""
        log = ProcessingLog(
            id_farm=self.farm_id,
            source_system="PMGZ",
            filename=filename,
            status="processing",
            started_at=datetime.utcnow(),
        )
        self.db.add(log)
        self.db.commit()
        log_id = log.id
        self.upload_log_id = log_id
        upload = None

        try:
            loader = PMGZLoader(farm_id=self.farm_id)
            df = loader.load(file_content, filename)
            logger.info(f'PMGZ carregado: {len(df)} registros')

            inserted, updated, failed = self._upsert_animals(df)

            log.total_rows = len(df)
            log.rows_inserted = inserted
            log.rows_updated = updated
            log.rows_failed = failed
            log.status = "completed"
            log.completed_at = datetime.utcnow()

            if self.upload_id:
                upload = self.db.query(Upload).filter(
                    Upload.upload_id == self.upload_id
                ).first()
                if upload:
                    upload.total_registros = len(df)
                    upload.rows_inserted = inserted
                    upload.rows_updated = updated
                    upload.status = "completed"
                    upload.completed_at = datetime.utcnow()
                    upload.arquivo_nome_original = filename

            self.db.commit()
            return df, log, upload

        except Exception as e:
            self.db.rollback()
            fresh_db = SessionLocal()
            try:
                failed_log = fresh_db.query(ProcessingLog).filter(
                    ProcessingLog.id == log_id
                ).first()
                if failed_log:
                    failed_log.status = "failed"
                    failed_log.error_message = str(e)[:1000]
                    failed_log.completed_at = datetime.utcnow()
                    fresh_db.commit()

                if self.upload_id:
                    failed_upload = fresh_db.query(Upload).filter(
                        Upload.upload_id == self.upload_id
                    ).first()
                    if failed_upload:
                        failed_upload.status = "failed"
                        failed_upload.error_message = str(e)[:1000]
                        failed_upload.completed_at = datetime.utcnow()
                        fresh_db.commit()
            except Exception:
                fresh_db.rollback()
            finally:
                fresh_db.close()
            raise

    def _upsert_animals(self, df: pd.DataFrame) -> Tuple[int, int, int]:
        """UPSERT para tabela animais_pmgz."""
        inserted = 0
        updated = 0
        failed = 0

        existing = self.db.query(AnimalPMGZ).filter(
            AnimalPMGZ.id_farm == self.farm_id
        ).all()
        existing_map = {a.identificacao_animal_rgn: a for a in existing}
        logger.info(f'Animais PMGZ existentes no DB: {len(existing_map)}')

        records = df.to_dict('records')

        for values in records:
            values = {k: (None if pd.isna(v) else v) for k, v in values.items()}
            values['processing_log_id'] = self.upload_log_id
            values['id_farm'] = self.farm_id

            rgn = values.get('identificacao_animal_rgn')
            if not rgn:
                logger.warning(f'Skipping row - sem RGN: {values}')
                failed += 1
                continue

            if rgn in existing_map:
                existing = existing_map[rgn]
                for k, v in values.items():
                    if k not in ('id', 'id_farm', 'identificacao_animal_rgn'):
                        setattr(existing, k, v)
                existing.processing_log_id = self.upload_log_id
                updated += 1
            else:
                animal = AnimalPMGZ(**values)
                self.db.add(animal)
                inserted += 1

        try:
            self.db.commit()
            logger.info(f'PMGZ upsert completo: inserted={inserted}, updated={updated}, failed={failed}')
        except Exception as e:
            self.db.rollback()
            logger.error(f'Falha no commit PMGZ: {e}')
            failed = inserted + updated
            inserted = 0
            updated = 0

        return inserted, updated, failed