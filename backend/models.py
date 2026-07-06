from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, Text, JSON, Enum, func, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import os
import uuid
from datetime import datetime

from sqlalchemy.orm import declarative_base

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
IS_SQLITE = DB_URL.startswith("sqlite")

Base = declarative_base()


def _fk(ref: str):
    """Return ForeignKey, stripping schema prefix for SQLite."""
    if IS_SQLITE:
        parts = ref.split(".")
        if len(parts) == 3:
            return ForeignKey(f"{parts[1]}.{parts[2]}")
    return ForeignKey(ref)


# Legacy Farm model removed (silver schema discontinued)


class Upload(Base):
    __tablename__ = "uploads"
    __table_args__ = ({"schema": "genetics"} if not IS_SQLITE else {})

    upload_id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String(255), nullable=False)
    id_farm = Column(String(36), nullable=False, index=True)
    fonte_origem = Column(String(50), nullable=False)
    arquivo_nome_original = Column(String(255))
    arquivo_hash = Column(String(64))
    total_registros = Column(Integer, default=0)
    rows_inserted = Column(Integer, default=0)
    rows_updated = Column(Integer, default=0)
    status = Column(String(20), default="processing")
    error_message = Column(Text)
    usuario_id = Column(Integer, _fk("genetics.users.id"), nullable=True)
    data_upload = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    usuario = relationship("User", back_populates="uploads")


# Legacy Animal model removed (genetics.animais discontinued)


class ColumnMapping(Base):
    __tablename__ = "column_mapping"
    __table_args__ = (
        UniqueConstraint("source_system", "source_column", name="uix_source_system_column"),
        {"schema": "genetics"} if not IS_SQLITE else {},
    )

    id = Column(Integer, primary_key=True, index=True)
    source_system = Column(String(50), nullable=False)
    source_column = Column(String(100), nullable=False)
    target_column = Column(String(100), nullable=False)
    data_type = Column(String(20), default="float")
    is_required = Column(Boolean, default=False)


class ProcessingLog(Base):
    __tablename__ = "processing_log"
    __table_args__ = ({"schema": "genetics"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    id_farm = Column(String(36), index=True)  # UUID do genetics.farms
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


class RawAnimalData(Base):
    """
    Stores ALL columns from the original file as JSON.
    This is the single source of truth — nothing is discarded.
    """
    __tablename__ = "raw_animal_data"
    __table_args__ = ({"schema": "genetics"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    id_animal = Column(Integer, index=True)  # referência sem FK cross-schema
    id_farm = Column(String(36), nullable=False, index=True)  # UUID do genetics.farms
    source_system = Column(String(50), nullable=False)
    processing_log_id = Column(Integer, index=True)
    raw_data = Column(JSON, nullable=False)  # ALL columns as JSON dict
    created_at = Column(DateTime, default=datetime.utcnow)


class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = ({"schema": "genetics"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    proprietario = Column(String(255), nullable=False, index=True)
    data_nascimento = Column(String(20))
    fazenda_empresa = Column(String(255))
    cnpj_cpf = Column(String(100))
    contato = Column(String(255))
    endereco = Column(Text)
    municipio = Column(String(100))
    uf = Column(String(20))
    cep = Column(String(50))
    endereco_correspondencia = Column(Text)
    fones = Column(String(255))
    coordenador = Column(String(100))
    gado = Column(String(20))
    rebanho = Column(String(100))
    software = Column(String(100))
    programa_melhoramento = Column(String(100))
    nome_financeiro = Column(String(255))
    whatsapp_financeiro = Column(String(50))
    email = Column(String(255))
    endereco_financeiro = Column(Text)
    contrato = Column(String(100))
    nf = Column(String(10))
    venc_boleto = Column(String(20))
    observacoes = Column(Text)
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    __table_args__ = ({"schema": "genetics"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    id_farm = Column(String(36), index=True) # UUID da fazenda no genetics
    role = Column(String(20), default="user")  # admin, user, viewer
    ativo = Column(Boolean, default=True)
    ultimo_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    uploads = relationship("Upload", back_populates="usuario")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = ({"schema": "genetics"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, _fk("genetics.users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")  # info, success, warning, error
    is_read = Column(Boolean, default=False)
    link = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================
# GENETICS SCHEMA MODELS (NOVO)
# ============================================

class GeneticsFarm(Base):
    __tablename__ = "farms"
    __table_args__ = {"schema": "genetics"} if not IS_SQLITE else {}

    id = Column(UUID(as_uuid=True), primary_key=True)
    nome = Column(String(255))
    dono_fazenda = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    animals = relationship("GeneticsAnimal", back_populates="farm")


class GeneticsAnimal(Base):
    __tablename__ = "animals"
    __table_args__ = (
        UniqueConstraint("farm_id", "rgn", "serie", name="uix_farm_rgn_serie"),
        {"schema": "genetics"} if not IS_SQLITE else {},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), _fk("genetics.farms.id"), nullable=False)
    nome = Column(String(255))
    serie = Column(String(50))
    rgn = Column(String(50), nullable=False)
    sexo = Column(String(1))
    raca = Column(String(100))
    nascimento = Column(Date)
    genotipado = Column(Boolean, default=False)
    csg = Column(Boolean, default=False)
    sire_id = Column(UUID(as_uuid=True), nullable=True)
    dam_id = Column(UUID(as_uuid=True), nullable=True)
    upload_id = Column(String(36), index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    farm = relationship("GeneticsFarm", back_populates="animals")
    genetic_evaluations = relationship("GeneticsGeneticEvaluation", back_populates="animal")


class GeneticsGeneticEvaluation(Base):
    __tablename__ = "genetic_evaluations"
    __table_args__ = {"schema": "genetics"} if not IS_SQLITE else {}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    animal_id = Column(UUID(as_uuid=True), _fk("genetics.animals.id"), nullable=False)
    farm_id = Column(UUID(as_uuid=True), _fk("genetics.farms.id"), nullable=False)
    safra = Column(Integer)
    fonte_origem = Column(String(50))  # 'PMGZ', 'ANCP', 'GENEPLUS'
    data_referencia = Column(Date)

    # Main Indices
    indice_principal = Column(Numeric(10, 4))
    rank_principal = Column(Integer)
    percentil_principal = Column(Numeric(10, 4))

    # Metrics JSONB: { "PN-EDg": { "dep": 0.5, "acc": 80, "rank": 1, "perc": 2.5 } }
    metrics = Column(JSONB if not IS_SQLITE else JSON, nullable=False, server_default='{}')

    # Progeny Stats: { "NF120": 10, "NR120": 2 }
    progeny_stats = Column(JSONB if not IS_SQLITE else JSON, nullable=False, server_default='{}')

    # Phenotypes: { "peso_desmama": 210.5 }
    phenotypes = Column(JSONB if not IS_SQLITE else JSON, nullable=False, server_default='{}')

    upload_id = Column(String(36))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    animal = relationship("GeneticsAnimal", back_populates="genetic_evaluations")


class DashboardStatsCache(Base):
    __tablename__ = "dashboard_stats_cache"
    __table_args__ = ({"schema": "genetics"} if not IS_SQLITE else {})

    farm_id = Column(String(36), primary_key=True)  # UUID or 'ALL'
    stats_v2 = Column(JSONB if not IS_SQLITE else Text)
    analytics = Column(JSONB if not IS_SQLITE else Text)
    platform_comparison = Column(JSONB if not IS_SQLITE else Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
