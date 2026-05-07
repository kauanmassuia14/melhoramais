from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, Text, JSON, Enum, func, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
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

    # Removido: animais - não usamos mais silver.animais
    processing_logs = relationship("ProcessingLog", back_populates="farm")
    uploads = relationship("Upload", back_populates="farm")


class Upload(Base):
    __tablename__ = "uploads"
    __table_args__ = ({"schema": "silver"} if not IS_SQLITE else {})

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
    usuario_id = Column(Integer, _fk("silver.usuarios.id"), nullable=True)
    data_upload = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    usuario = relationship("User", back_populates="uploads")
    animais = relationship("Animal", back_populates="upload")


class Animal(Base):
    __tablename__ = "animais"
    __table_args__ = (
        UniqueConstraint("id_farm", "rgn_animal", name="uix_farm_rgn"),
        {"schema": "silver"} if not IS_SQLITE else {},
    )

    id_animal = Column(Integer, primary_key=True, index=True)
    id_farm = Column(Integer, _fk("silver.fazendas.id_farm"), nullable=False, index=True)
    upload_id = Column(String(36), _fk("silver.uploads.upload_id"), nullable=True, index=True)
    processing_log_id = Column(Integer, _fk("audit.processing_log.id"), nullable=True, index=True)
    rgn_animal = Column(String(50), nullable=False)
    nome_animal = Column(String(255))
    raca = Column(String(50))
    sexo = Column(String(1))
    data_nascimento = Column(Date)

    # Genealogy - 1ª geração
    mae_rgn = Column(String(50))
    pai_rgn = Column(String(50))

    # Genealogy - 2ª geração (avos)
    avo_paterno_rgn = Column(String(50))  # Avô paterno
    avo_paterno_mae_rgn = Column(String(50))  # Avó paterna
    avo_materno_rgn = Column(String(50))  # Avô materno
    avo_materno_mae_rgn = Column(String(50))  # Avó materna

    # Genealogy - 3ª geração (bisavôs)
    bisavo_paterno_pai_rgn = Column(String(50))  # Bisavô paterno do pai
    bisavo_paterno_mae_pai_rgn = Column(String(50))  # Bisavó paterna do pai
    bisavo_materno_pai_rgn = Column(String(50))  # Bisavô materno do pai
    bisavo_materno_mae_pai_rgn = Column(String(50))  # Bisavó materna do pai
    bisavo_paterno_mae_rgn = Column(String(50))  # Bisavô paterno da mãe
    bisavo_paterno_mae_mae_rgn = Column(String(50))  # Bisavó paterna da mãe
    bisavo_materno_mae_rgn = Column(String(50))  # Bisavô materno da mãe
    bisavo_materno_mae_mae_rgn = Column(String(50))  # Bisavó materna da mãe

    # Genealogy - 4ª geração (trisavôs)
    trisavo_paterno_pai_rgn = Column(String(50))
    trisavo_paterno_mae_pai_rgn = Column(String(50))
    trisavo_materno_pai_rgn = Column(String(50))
    trisavo_materno_mae_pai_rgn = Column(String(50))
    trisavo_paterno_mae_rgn = Column(String(50))
    trisavo_paterno_mae_mae_rgn = Column(String(50))
    trisavo_materno_mae_rgn = Column(String(50))
    trisavo_materno_mae_mae_rgn = Column(String(50))

    # Pesos
    p210_peso_desmama = Column(Float)
    p365_peso_ano = Column(Float)
    p450_peso_sobreano = Column(Float)
    peso_nascimento = Column(Float)
    peso_final = Column(Float)

    # Medidas
    pe_perimetro_escrotal = Column(Float)
    a_area_olho_lombo = Column(Float)
    eg_espessura_gordura = Column(Float)
    altura = Column(Float)
    circumference = Column(Float)

    # Reprodução
    im_idade_primeiro_parto = Column(Float)
    intervalo_partos = Column(Float)
    dias_gestacao = Column(Float)

    # ==================== ANCP ====================
    # Benchmarking - ANCP ( DEP )
    anc_mg = Column(Float)   # Média Genética
    anc_te = Column(Float)   # Tamanho
    anc_m = Column(Float)    # Maternidade
    anc_p = Column(Float)    # Peso
    anc_dp = Column(Float)   # Desvio Padrão
    anc_sp = Column(Float)   # Sobreano
    anc_e = Column(Float)    # Eficiência
    anc_sao = Column(Float)  # Área Olho Lombo
    anc_leg = Column(Float)  # Legume (gordura)
    anc_sh = Column(Float)   # Sexo Hack
    anc_pp30 = Column(Float) # Produção Prioritária 30

    # Direct Predicted (DEP) - ANCP
    anc_dipp = Column(Float)   # DEP IPP
    anc_d3p = Column(Float)    # DEP 3P
    anc_dstay = Column(Float)   # DEP Stayability
    anc_dpn = Column(Float)    # DEP Peso Nascimento
    anc_dp12 = Column(Float)   # DEP Peso 12 meses
    anc_dpe = Column(Float)   # DEP PE
    anc_daol = Column(Float)  # DEP AOL
    anc_dacab = Column(Float)  # DEP ACAB

    # AC (Accuracy) - ANCP
    anc_ac_mg = Column(Float)
    anc_ac_te = Column(Float)
    anc_ac_m = Column(Float)
    anc_ac_p = Column(Float)

    # ==================== GENEPLUS ====================
    # Benchmarking - Geneplus
    gen_iqg = Column(Float)    # Índice Qualidade Genética
    gen_pmm = Column(Float)  # Peso Maternidade
    gen_p = Column(Float)     # Peso
    gen_dp = Column(Float)    # Desvio Padrão
    gen_sp = Column(Float)    # Sobreano
    gen_e = Column(Float)     # Eficiência
    gen_sao = Column(Float)   # Área Olho Lombo
    gen_leg = Column(Float)   # Legume (gordura)
    gen_sh = Column(Float)    # Sexo Hack
    gen_pp30 = Column(Float)  # Produção Prioritária 30

    # Direct Predicted - Geneplus
    gen_pn = Column(Float)     # PN (Peso Nascimento)
    gen_p120 = Column(Float)   # P120 (Peso 120 dias)
    gen_tmd = Column(Float)    # TMD (Total Maternal)
    gen_pd = Column(Float)     # PD (Peso Desmama)
    gen_tm120 = Column(Float) # TM120 (Total Maternal 120)
    gen_ps = Column(Float)     # PS (Peso Sobreano)
    gen_gpd = Column(Float)    # GPD (Ganho Pós-Desmama)
    gen_cfd = Column(Float)   # CFD (Confecção)
    gen_cfs = Column(Float)   # CFS (Confecção Sobreano)
    gen_hp_stay = Column(Float) # Stayability
    gen_rd = Column(Float)    # RD (Resposta Digestão)
    gen_egs = Column(Float)   # EGS (Espessura Gordura Sub cutânea)
    gen_acab = Column(Float)  # ACAB (Área de Olho de Lobo Adjusted)
    gen_mar = Column(Float)   # MAR (Musculatura)

    # AC - Geneplus
    gen_ac_iqg = Column(Float)
    gen_ac_pmm = Column(Float)
    gen_ac_p = Column(Float)

    # ==================== PMGZ ====================
    # Benchmarking - PMGZ
    pmg_iabc = Column(Float)    # Índice ABCZ
    pmg_zpmm = Column(Float)  # Zootecnia Peso Materno
    pmg_p = Column(Float)    # Peso
    pmg_dp = Column(Float)   # Desvio Padrão
    pmg_sp = Column(Float)    # Sobreano
    pmg_e = Column(Float)     # Eficiência
    pmg_sao = Column(Float)   # Área Olho Lombo
    pmg_leg = Column(Float)   # Legume (gordura)
    pmg_sh = Column(Float)    # Sexo Hack
    pmg_pp30 = Column(Float)   # Produção Prioritária 30

    # Direct Predicted - PMGZ
    pmg_pn = Column(Float)     # PN-EDg (Peso Nascimento)
    pmg_pa = Column(Float)     # PA-EDg (Peso Ao Nascer)
    pmg_ps = Column(Float)     # PS-EDg (Peso Sobreano)
    pmg_pm = Column(Float)    # PM-EMg (Peso Maternal)
    pmg_ipp = Column(Float)   # IPPg (Idade Primeiro Parto)
    pmg_stay = Column(Float)   # Stay (Stayability)
    pmg_pe = Column(Float)    # PE-365g (PE)
    pmg_aol = Column(Float)   # AOLg (Área Olho Lobo)
    pmg_acab = Column(Float)  # ACABg (Acabamento)
    pmg_mar = Column(Float)   # MARg (Maciez)

    # DECA - PMGZ
    pmg_deca = Column(String(10))
    pmg_deca_pn = Column(String(10))
    pmg_deca_p12 = Column(String(10))
    pmg_deca_ps = Column(String(10))
    pmg_deca_stay = Column(String(10))
    pmg_deca_pe = Column(String(10))
    pmg_deca_aol = Column(String(10))

    # Meta genes - PMGZ
    pmg_meta_p = Column(Float)
    pmg_meta_m = Column(Float)
    pmg_meta_t = Column(Float)

    # AC - PMGZ
    pmg_ac_iabc = Column(Float)
    pmg_ac_p = Column(Float)
    pmg_ac_m = Column(Float)

    # ==================== PMGZ EXPANDIDO (Cavafunda) ====================
    
    # ANIMAL - dados básicos
    pmg_serie_rgd = Column(String(50))
    pmg_p_percent = Column(Float)
    pmg_f_percent = Column(Float)
    
    # Genealogia expandida
    # PAI
    pai_nome = Column(String(255))
    pai_serie_rgd = Column(String(50))
    # avô paterno (já existe)
    # avó paterna (já existe)
    # MÃE
    mae_nome = Column(String(255))
    mae_serie_rgd = Column(String(50))
    # avô materno (já existe)
    # avó materna (já existe)
    
    # CARACTERÍSTICAS DE CRESCIMENTO - cada um com DEP, AC%, DECA, P%
    # PN-EDg (Peso Nascimento)
    pmg_pn_dep = Column(Float)
    pmg_pn_ac = Column(Float)
    pmg_pn_deca = Column(String(10))
    pmg_pn_p_percent = Column(Float)
    
    # PD-EDg (Peso Desmama)
    pmg_pd_dep = Column(Float)
    pmg_pd_ac = Column(Float)
    pmg_pd_deca = Column(String(10))
    pmg_pd_p_percent = Column(Float)
    
    # PA-EDg (Peso Ano)
    pmg_pa_dep = Column(Float)
    pmg_pa_ac = Column(Float)
    pmg_pa_deca = Column(String(10))
    pmg_pa_p_percent = Column(Float)
    
    # PS-EDg (Peso Sobreano)
    pmg_ps_dep = Column(Float)
    pmg_ps_ac = Column(Float)
    pmg_ps_deca = Column(String(10))
    pmg_ps_p_percent = Column(Float)
    
    # CARACTERÍSTICAS MATERNAS
    # PM-EMg (Peso Fase Materna)
    pmg_pm_dep = Column(Float)
    pmg_pm_ac = Column(Float)
    pmg_pm_deca = Column(String(10))
    pmg_pm_p_percent = Column(Float)
    
    # CARACTERÍSTICAS REPRODUTIVAS
    # IPPg
    pmg_ipp_dep = Column(Float)
    pmg_ipp_ac = Column(Float)
    pmg_ipp_deca = Column(String(10))
    pmg_ipp_p_percent = Column(Float)
    
    # STAYg
    pmg_stay_dep = Column(Float)
    pmg_stay_ac = Column(Float)
    pmg_stay_deca = Column(String(10))
    pmg_stay_p_percent = Column(Float)
    
    # PE-365g
    pmg_pe365_dep = Column(Float)
    pmg_pe365_ac = Column(Float)
    pmg_pe365_deca = Column(String(10))
    pmg_pe365_p_percent = Column(Float)
    
    # PSNg (Precocidade Sexual)
    pmg_psn_dep = Column(Float)
    pmg_psn_ac = Column(Float)
    pmg_psn_deca = Column(String(10))
    pmg_psn_p_percent = Column(Float)
    
    # CARACTERÍSTICAS DE CARCAÇA
    # AOLg
    pmg_aol_dep = Column(Float)
    pmg_aol_ac = Column(Float)
    pmg_aol_deca = Column(String(10))
    pmg_aol_p_percent = Column(Float)
    
    # ACABg
    pmg_acab_dep = Column(Float)
    pmg_acab_ac = Column(Float)
    pmg_acab_deca = Column(String(10))
    pmg_acab_p_percent = Column(Float)
    
    # MARg
    pmg_mar_dep = Column(Float)
    pmg_mar_ac = Column(Float)
    pmg_mar_deca = Column(String(10))
    pmg_mar_p_percent = Column(Float)
    
    # CARACTERÍSTICAS MORFOLÓGICAS
    # Eg (Estrutura)
    pmg_eg_dep = Column(Float)
    pmg_eg_ac = Column(Float)
    pmg_eg_deca = Column(String(10))
    pmg_eg_p_percent = Column(Float)
    
    # Pg (Precocidade)
    pmg_p_dep = Column(Float)
    pmg_p_ac = Column(Float)
    pmg_p_deca = Column(String(10))
    pmg_p_p_percent = Column(Float)
    
    # Mg (Musculosidade)
    pmg_m_dep = Column(Float)
    pmg_m_ac = Column(Float)
    pmg_m_deca = Column(String(10))
    pmg_m_p_percent = Column(Float)
    
    # PESOS (colunas simples)
    p120_peso_120 = Column(Float)
    
    # INFORMAÇÕES DE DESCENDENTES
    # P120
    desc_p120_filhos = Column(Integer)
    desc_p120_rebanhos = Column(Integer)
    # P210
    desc_p210_filhos = Column(Integer)
    desc_p210_rebanhos = Column(Integer)
    # P365
    desc_p365_filhos = Column(Integer)
    desc_p365_rebanhos = Column(Integer)
    # P450
    desc_p450_filhos = Column(Integer)
    desc_p450_rebanhos = Column(Integer)
    # P120 NETOS
    desc_p120_netosc = Column(Integer)
    desc_p120_netosc_rebanhos = Column(Integer)
    # P210 NETOS
    desc_p210_netosc = Column(Integer)
    desc_p210_netosc_rebanhos = Column(Integer)
    # PE365
    desc_pe365_filhos = Column(Integer)
    desc_pe365_rebanhos = Column(Integer)
    # STAY
    desc_stay_filhos = Column(Integer)
    desc_stay_rebanhos = Column(Integer)
    # IPP
    desc_ipp_filhos = Column(Integer)
    desc_ipp_rebanhos = Column(Integer)
    # AOL
    desc_aol_filhos = Column(Integer)
    desc_aol_rebanhos = Column(Integer)
    # ACAB
    desc_acab_filhos = Column(Integer)
    desc_acab_rebanhos = Column(Integer)
    
    # INFORMAÇÕES EXTRAS
    genotipado = Column(Boolean)
    csg = Column(Boolean)

    fonte_origem = Column(String(50))
    data_processamento = Column(DateTime, default=datetime.utcnow)

    upload = relationship("Upload", back_populates="animais")


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


class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = ({"schema": "silver"} if not IS_SQLITE else {})

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
    uploads = relationship("Upload", back_populates="usuario")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = ({"schema": "silver"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, _fk("silver.usuarios.id"), nullable=False, index=True)
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
    __table_args__ = {"schema": "genetics"} if not IS_SQLITE else {}

    id = Column(UUID(as_uuid=True), primary_key=True)
    farm_id = Column(UUID(as_uuid=True), _fk("genetics.farms.id"), nullable=False)
    nome = Column(String(255))
    serie = Column(String(50))
    rgn = Column(String(50), nullable=False)
    sexo = Column(String(1))
    nascimento = Column(Date)
    genotipado = Column(Boolean)
    csg = Column(Boolean)
    sire_id = Column(UUID(as_uuid=True))
    dam_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    farm = relationship("GeneticsFarm", back_populates="animals")
    genetic_evaluations = relationship("GeneticsGeneticEvaluation", back_populates="animal")


class GeneticsGeneticEvaluation(Base):
    __tablename__ = "genetic_evaluations"
    __table_args__ = {"schema": "genetics"} if not IS_SQLITE else {}

    id = Column(UUID(as_uuid=True), primary_key=True)
    animal_id = Column(UUID(as_uuid=True), _fk("genetics.animals.id"), nullable=False)
    farm_id = Column(UUID(as_uuid=True), _fk("genetics.farms.id"), nullable=False)
    safra = Column(Integer)
    fonte_origem = Column(String(50))
    iabczg = Column(Numeric(10, 4))
    deca_index = Column(Integer)

    # DEP armazenar como JSON string
    pn_ed = Column(Text)
    pd_ed = Column(Text)
    pa_ed = Column(Text)
    ps_ed = Column(Text)
    pm_em = Column(Text)
    ipp = Column(Text)
    stay = Column(Text)
    pe_365 = Column(Text)
    psn = Column(Text)
    aol = Column(Text)
    acab = Column(Text)
    marmoreio = Column(Text)
    eg = Column(Text)
    pg = Column(Text)
    mg = Column(Text)

    fenotipo_aol = Column(Numeric(10, 4))
    fenotipo_acab = Column(Numeric(10, 4))
    fenotipo_ipp = Column(Numeric(10, 4))
    fenotipo_stay = Column(Numeric(10, 4))

    p120_info = Column(Text)
    p210_info = Column(Text)
    p365_info = Column(Text)
    p450_info = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    animal = relationship("GeneticsAnimal", back_populates="genetic_evaluations")
