"""
NOVOS MODELOS NORMALIZADOS v2

Estrutura:
- AnimalBase: dados básicos do animal (identificação, genealogia 1-4 gerações)
- PlatformData: dados por plataforma (ANCP, GENEPLUS, PMGZ) em tabelas separadas
- AnimalSnapshot: histórico de versões
- AnimalAudit: log de alterações
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, Text, JSON, Enum
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from sqlalchemy.orm import declarative_base
import os

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


class AnimalBase(Base):
    """
    Dados básicos do animal - ONLY identificador e genealogia.
    Sem dados de benchmarking (isso vai em PlatformData).
    """
    __tablename__ = "animal_base"
    __table_args__ = (
        UniqueConstraint("id_farm", "rgn_animal", name="uix_farm_rgn_base"),
        {"schema": "silver"} if not IS_SQLITE else {},
    )

    id = Column(Integer, primary_key=True, index=True)
    id_farm = Column(Integer, _fk("silver.fazendas.id_farm"), nullable=False, index=True)
    upload_id = Column(String(36), _fk("silver.uploads.upload_id"), nullable=True, index=True)
    
    # Identificação
    rgn_animal = Column(String(50), nullable=False)
    nome_animal = Column(String(255))
    raca = Column(String(50))
    sexo = Column(String(1))
    data_nascimento = Column(Date)
    
    # Genealogy - 1ª geração
    mae_rgn = Column(String(50))
    pai_rgn = Column(String(50))
    
    # Genealogy - 2ª geração (avós)
    avo_paterno_rgn = Column(String(50))
    avo_paterno_mae_rgn = Column(String(50))
    avo_materno_rgn = Column(String(50))
    avo_materno_mae_rgn = Column(String(50))
    
    # Genealogy - 3ª geração (bisavós)
    bisavo_paterno_pai_rgn = Column(String(50))
    bisavo_paterno_mae_pai_rgn = Column(String(50))
    bisavo_materno_pai_rgn = Column(String(50))
    bisavo_materno_mae_pai_rgn = Column(String(50))
    bisavo_paterno_mae_rgn = Column(String(50))
    bisavo_paterno_mae_mae_rgn = Column(String(50))
    bisavo_materno_mae_rgn = Column(String(50))
    bisavo_materno_mae_mae_rgn = Column(String(50))
    
    # Genealogy - 4ª geração (trisavós)
    trisavo_paterno_pai_rgn = Column(String(50))
    trisavo_paterno_mae_pai_rgn = Column(String(50))
    trisavo_materno_pai_rgn = Column(String(50))
    trisavo_materno_mae_pai_rgn = Column(String(50))
    trisavo_paterno_mae_rgn = Column(String(50))
    trisavo_paterno_mae_mae_rgn = Column(String(50))
    trisavo_materno_mae_rgn = Column(String(50))
    trisavo_materno_mae_mae_rgn = Column(String(50))
    
    # Pesos básicos (não são DEPs)
    peso_nascimento = Column(Float)
    peso_final = Column(Float)
    
    # Medidas corporais
    altura = Column(Float)
    circumference = Column(Float)
    
    # Reprodução
    im_idade_primeiro_parto = Column(Float)
    intervalo_partos = Column(Float)
    dias_gestacao = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    farm = relationship("Farm", foreign_keys=[id_farm])
    uploads = relationship("Upload", back_populates="animais_base")
    platform_data = relationship("AnimalPlatformData", back_populates="animal_base", cascade="all, delete-orphan")


class AnimalPlatformData(Base):
    """
    dados de benchmarking POR PLATAFORMA.
    Uma linha por animal + plataforma (ANCP, GENEPLUS, PMGZ).
    """
    __tablename__ = "animal_platform_data"
    __table_args__ = (
        UniqueConstraint("animal_base_id", "platform", name="uix_animal_platform"),
        {"schema": "silver"} if not IS_SQLITE else {},
    )

    id = Column(Integer, primary_key=True, index=True)
    animal_base_id = Column(Integer, _fk("silver.animal_base.id"), nullable=False, index=True)
    platform = Column(String(20), nullable=False)  # ANCP, GENEPLUS, PMGZ
    
    # Fonte original do dado
    fonte_origem = Column(String(50))
    data_processamento = Column(DateTime, default=datetime.utcnow)
    
    # ==================== BENCHMARK INDICES ====================
    # Índice principal da plataforma
    idx_principal = Column(Float)  # IQG (Geneplus), IABC (PMGZ), MG (ANCP)
    idx_principal_ac = Column(Float)  # Accuracy
    
    # Pesos maternal
    idx_maternal = Column(Float)
    idx_maternal_ac = Column(Float)
    
    # Peso
    idx_peso = Column(Float)
    idx_peso_ac = Column(Float)
    
    # Sobreano
    idx_sobreano = Column(Float)
    idx_sobreano_ac = Column(Float)
    
    # Eficiência
    idx_eficiencia = Column(Float)
    
    # AOL
    idx_aol = Column(Float)
    
    # Gordura
    idx_gordura = Column(Float)
    
    # Sexo hack
    idx_sexo_hack = Column(Float)
    
    # Produção prioritária 30
    idx_pp30 = Column(Float)
    
    # ==================== DEP INDIVIDUAIS ====================
    # DEP Peso Nascimento
    dep_pn = Column(Float)
    dep_pn_ac = Column(Float)
    
    # DEP Peso Desmama (210)
    dep_p210 = Column(Float)
    dep_p210_ac = Column(Float)
    
    # DEP Peso Ano (365)
    dep_p365 = Column(Float)
    dep_p365_ac = Column(Float)
    
    # DEP Peso Sobreano (450)
    dep_p450 = Column(Float)
    dep_p450_ac = Column(Float)
    
    # DEP Total Maternal (TMD/PM)
    dep_tm = Column(Float)
    dep_tm_ac = Column(Float)
    
    # Stayability
    dep_stay = Column(Float)
    dep_stay_ac = Column(Float)
    
    # DEP Perímetro Escrotal
    dep_pe = Column(Float)
    dep_pe_ac = Column(Float)
    
    # DEP AOL
    dep_aol = Column(Float)
    dep_aol_ac = Column(Float)
    
    # DEP ACAB (Acabamento)
    dep_acab = Column(Float)
    dep_acab_ac = Column(Float)
    
    # DEP IPP (Idade Primeiro Parto)
    dep_ipp = Column(Float)
    dep_ipp_ac = Column(Float)
    
    # DEP 3P (Produção Prioritária)
    dep_3p = Column(Float)
    
    # DEP IPP (Indice producaoprioritaria)
    dep_ppp = Column(Float)
    
    # ==================== DEMAIS DEP ====================
    # PMGZ specific
    pmg_deca = Column(String(10))
    pmg_deca_pn = Column(String(10))
    pmg_deca_p12 = Column(String(10))
    pmg_deca_ps = Column(String(10))
    pmg_deca_stay = Column(String(10))
    pmg_deca_pe = Column(String(10))
    pmg_deca_aol = Column(String(10))
    
    # Meta genes
    pmg_meta_p = Column(Float)
    pmg_meta_m = Column(Float)
    pmg_meta_t = Column(Float)
    
    # Dados origem (JSON raw)
    raw_data = Column(JSON)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    animal_base = relationship("AnimalBase", back_populates="platform_data")


class AnimalSnapshot(Base):
    """
    Histórico de versões dos dados do animal.
    Usado para audit e para rollback se necessário.
    """
    __tablename__ = "animal_snapshot"
    __table_args__ = ({"schema": "silver"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    animal_base_id = Column(Integer, _fk("silver.animal_base.id"), nullable=False, index=True)
    platform = Column(String(20))  # Se null, é snapshot base
    
    version = Column(Integer, nullable=False)
    snapshot_data = Column(JSON, nullable=False)  # Dados completos nessa versão
    
    created_at = Column(DateTime, default=datetime.utcnow)
    upload_id = Column(String(36), _fk("silver.uploads.upload_id"))
    motivo = Column(String(255))  # "import", "correcao", "manual", etc
    
    __table_args__ = (
        UniqueConstraint("animal_base_id", "version", name="uix_animal_version"),
        {"schema": "silver"} if not IS_SQLITE else {},
    )


class AnimalAudit(Base):
    """
    Log de alterações granular.
   tracking de mudanças específicas (não apenas snapshot full).
    """
    __tablename__ = "animal_audit"
    __table_args__ = ({"schema": "audit"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    animal_base_id = Column(Integer, _fk("silver.animal_base.id"), nullable=False, index=True)
    platform = Column(String(20))  # null se change é na base
    
    campo = Column(String(100), nullable=False)
    valor_anterior = Column(JSON)
    valor_novo = Column(JSON)
    
    user_id = Column(Integer, _fk("silver.usuarios.id"))
    upload_id = Column(String(36), _fk("silver.uploads.upload_id"))
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)