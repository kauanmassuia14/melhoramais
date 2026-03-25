from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, Text, JSON
from sqlalchemy.orm import relationship
import os
from datetime import datetime

from sqlalchemy.orm import declarative_base

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
IS_SQLITE = DB_URL.startswith("sqlite")

Base = declarative_base()


def _fk(ref: str):
    """Return ForeignKey, stripping schema prefix for SQLite."""
    if IS_SQLITE:
        # silver.fazendas.id_farm -> fazendas.id_farm
        parts = ref.split(".")
        if len(parts) == 3:
            return ForeignKey(f"{parts[1]}.{parts[2]}")
    return ForeignKey(ref)


class Farm(Base):
    __tablename__ = "fazendas"
    __table_args__ = ({"schema": "silver"} if not IS_SQLITE else {})

    id_farm = Column(Integer, primary_key=True, index=True)
    nome_farm = Column(String(255), nullable=False)
    cnpj = Column(String(20), unique=True)
    responsavel = Column(String(255))
    email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    animais = relationship("Animal", back_populates="farm")
    processing_logs = relationship("ProcessingLog", back_populates="farm")


class Animal(Base):
    __tablename__ = "animais"
    __table_args__ = (
        UniqueConstraint("id_farm", "rgn_animal", name="uix_farm_rgn"),
        {"schema": "silver"} if not IS_SQLITE else {},
    )

    id_animal = Column(Integer, primary_key=True, index=True)
    id_farm = Column(Integer, _fk("silver.fazendas.id_farm"), nullable=False, index=True)
    rgn_animal = Column(String(50), nullable=False)
    nome_animal = Column(String(255))
    raca = Column(String(50))
    sexo = Column(String(1))
    data_nascimento = Column(Date)
    mae_rgn = Column(String(50))
    pai_rgn = Column(String(50))

    p210_peso_desmama = Column(Float)
    p365_peso_ano = Column(Float)
    p450_peso_sobreano = Column(Float)
    pe_perimetro_escrotal = Column(Float)
    a_area_olho_lombo = Column(Float)
    eg_espessura_gordura = Column(Float)
    im_idade_primeiro_parto = Column(Float)

    fonte_origem = Column(String(50))
    data_processamento = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm", back_populates="animais")


class ColumnMapping(Base):
    __tablename__ = "column_mapping"
    __table_args__ = (
        UniqueConstraint("source_system", "source_column", name="uix_source_system_column"),
        {"schema": "silver"} if not IS_SQLITE else {},
    )

    id = Column(Integer, primary_key=True, index=True)
    source_system = Column(String(50), nullable=False)
    source_column = Column(String(100), nullable=False)
    target_column = Column(String(100), nullable=False)
    data_type = Column(String(20), default="float")
    is_required = Column(Boolean, default=False)


class ProcessingLog(Base):
    __tablename__ = "processing_log"
    __table_args__ = ({"schema": "audit"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    id_farm = Column(Integer, _fk("silver.fazendas.id_farm"), index=True)
    source_system = Column(String(50), nullable=False)
    filename = Column(String(255))
    total_rows = Column(Integer, default=0)
    rows_inserted = Column(Integer, default=0)
    rows_updated = Column(Integer, default=0)
    rows_failed = Column(Integer, default=0)
    status = Column(String(20), default="processing")
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    farm = relationship("Farm", back_populates="processing_logs")


class RawAnimalData(Base):
    """
    Stores ALL columns from the original file as JSON.
    This is the single source of truth — nothing is discarded.
    """
    __tablename__ = "raw_animal_data"
    __table_args__ = ({"schema": "silver"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    id_animal = Column(Integer, _fk("silver.animais.id_animal"), index=True)
    id_farm = Column(Integer, _fk("silver.fazendas.id_farm"), nullable=False, index=True)
    source_system = Column(String(50), nullable=False)
    processing_log_id = Column(Integer, _fk("audit.processing_log.id"))
    raw_data = Column(JSON, nullable=False)  # ALL columns as JSON dict
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "usuarios"
    __table_args__ = ({"schema": "silver"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    id_farm = Column(Integer, _fk("silver.fazendas.id_farm"), index=True)
    role = Column(String(20), default="user")  # admin, user, viewer
    ativo = Column(Boolean, default=True)
    ultimo_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm", foreign_keys=[id_farm])
