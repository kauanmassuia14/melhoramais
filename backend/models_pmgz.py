from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.orm import declarative_base
import os

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
IS_SQLITE = DB_URL.startswith("sqlite")

Base = declarative_base()


def _fk(ref: str):
    if IS_SQLITE:
        parts = ref.split(".")
        if len(parts) == 3:
            return ForeignKey(f"{parts[1]}.{parts[2]}")
    return ForeignKey(ref)


class AnimalPMGZ(Base):
    __tablename__ = "animais_pmgz"
    __table_args__ = (
        UniqueConstraint("id_farm", "identificacao_animal_rgn", name="uix_farm_pmgz_rgn"),
        {"schema": "silver"} if not IS_SQLITE else {},
    )

    id = Column(Integer, primary_key=True, index=True)
    id_farm = Column(Integer, _fk("silver.fazendas.id_farm"), nullable=False, index=True)
    upload_id = Column(String(36), nullable=True, index=True)
    processing_log_id = Column(Integer, _fk("audit.processing_log.id"), nullable=True, index=True)

    # 1. Identificação do Animal
    identificacao_animal_nome = Column(String(255))
    identificacao_animal_serie_rgd = Column(String(50))
    identificacao_animal_rgn = Column(String(50), nullable=False)
    identificacao_animal_sexo = Column(String(1))
    identificacao_animal_nascimento = Column(Date)
    identificacao_indice_iabczg = Column(Float)
    identificacao_indice_deca = Column(Integer)
    identificacao_indice_p_perc = Column(Float)
    identificacao_indice_f_perc = Column(Float)

    # 2. Pedigree (Genealogia) - Pai
    pedigree_pai_nome = Column(String(255))
    pedigree_pai_serie_rgd = Column(String(50))
    pedigree_pai_rgn = Column(String(50))

    # Pedigree - Avô Paterno
    pedigree_avo_paterno_nome = Column(String(255))
    pedigree_avo_paterno_serie_rgd = Column(String(50))
    pedigree_avo_paterno_rgn = Column(String(50))

    # Pedigree - Avó Paterna
    pedigree_avo_paterna_nome = Column(String(255))
    pedigree_avo_paterna_serie_rgd = Column(String(50))
    pedigree_avo_paterna_rgn = Column(String(50))

    # Pedigree - Mãe
    pedigree_mae_nome = Column(String(255))
    pedigree_mae_serie_rgd = Column(String(50))
    pedigree_mae_rgn = Column(String(50))

    # Pedigree - Avô Materno
    pedigree_avo_materno_nome = Column(String(255))
    pedigree_avo_materno_serie_rgd = Column(String(50))
    pedigree_avo_materno_rgn = Column(String(50))

    # Pedigree - Avó Materna
    pedigree_avo_materna_nome = Column(String(255))
    pedigree_avo_materna_serie_rgd = Column(String(50))
    pedigree_avo_materna_rgn = Column(String(50))

    # 3. Características Genéticas: Crescimento
    # PN-EDg
    genetica_crescimento_pn_edg_dep = Column(Float)
    genetica_crescimento_pn_edg_ac_perc = Column(Integer)
    genetica_crescimento_pn_edg_deca = Column(Integer)
    genetica_crescimento_pn_edg_p_perc = Column(Float)

    # PD-EDg
    genetica_crescimento_pd_edg_dep = Column(Float)
    genetica_crescimento_pd_edg_ac_perc = Column(Integer)
    genetica_crescimento_pd_edg_deca = Column(Integer)
    genetica_crescimento_pd_edg_p_perc = Column(Float)

    # PA-EDg
    genetica_crescimento_pa_edg_dep = Column(Float)
    genetica_crescimento_pa_edg_ac_perc = Column(Integer)
    genetica_crescimento_pa_edg_deca = Column(Integer)
    genetica_crescimento_pa_edg_p_perc = Column(Float)

    # PS-EDg
    genetica_crescimento_ps_edg_dep = Column(Float)
    genetica_crescimento_ps_edg_ac_perc = Column(Integer)
    genetica_crescimento_ps_edg_deca = Column(Integer)
    genetica_crescimento_ps_edg_p_perc = Column(Float)

    # PM-EMg
    genetica_crescimento_pm_emg_dep = Column(Float)
    genetica_crescimento_pm_emg_ac_perc = Column(Integer)
    genetica_crescimento_pm_emg_deca = Column(Integer)
    genetica_crescimento_pm_emg_p_perc = Column(Float)

    # 4. Características Genéticas: Reprodutivas
    # IPPg
    genetica_reprodutiva_ippg_dep = Column(Float)
    genetica_reprodutiva_ippg_ac_perc = Column(Integer)
    genetica_reprodutiva_ippg_deca = Column(Integer)
    genetica_reprodutiva_ippg_p_perc = Column(Float)

    # STAYg
    genetica_reprodutiva_stayg_dep = Column(Float)
    genetica_reprodutiva_stayg_ac_perc = Column(Integer)
    genetica_reprodutiva_stayg_deca = Column(Integer)
    genetica_reprodutiva_stayg_p_perc = Column(Float)

    # PE-365g
    genetica_reprodutiva_pe365g_dep = Column(Float)
    genetica_reprodutiva_pe365g_ac_perc = Column(Integer)
    genetica_reprodutiva_pe365g_deca = Column(Integer)
    genetica_reprodutiva_pe365g_p_perc = Column(Float)

    # PE-450g
    genetica_reprodutiva_pe450g_dep = Column(Float)
    genetica_reprodutiva_pe450g_ac_perc = Column(Integer)
    genetica_reprodutiva_pe450g_deca = Column(Integer)
    genetica_reprodutiva_pe450g_p_perc = Column(Float)

    # 5. Características Genéticas: Carcaça
    # AOLg
    genetica_carcaca_aolg_dep = Column(Float)
    genetica_carcaca_aolg_ac_perc = Column(Integer)
    genetica_carcaca_aolg_deca = Column(Integer)
    genetica_carcaca_aolg_p_perc = Column(Float)

    # ACABg
    genetica_carcaca_acabg_dep = Column(Float)
    genetica_carcaca_acabg_ac_perc = Column(Integer)
    genetica_carcaca_acabg_deca = Column(Integer)
    genetica_carcaca_acabg_p_perc = Column(Float)

    # MARg
    genetica_carcaca_marg_dep = Column(Float)
    genetica_carcaca_marg_ac_perc = Column(Integer)
    genetica_carcaca_marg_deca = Column(Integer)
    genetica_carcaca_marg_p_perc = Column(Float)

    # Características Morfológicas
    # Eg
    genetica_morfologica_eg_dep = Column(Float)
    genetica_morfologica_eg_ac_perc = Column(Integer)
    genetica_morfologica_eg_deca = Column(Integer)
    genetica_morfologica_eg_p_perc = Column(Float)

    # Pg
    genetica_morfologica_pg_dep = Column(Float)
    genetica_morfologica_pg_ac_perc = Column(Integer)
    genetica_morfologica_pg_deca = Column(Integer)
    genetica_morfologica_pg_p_perc = Column(Float)

    # Mg
    genetica_morfologica_mg_dep = Column(Float)
    genetica_morfologica_mg_ac_perc = Column(Integer)
    genetica_morfologica_mg_deca = Column(Integer)
    genetica_morfologica_mg_p_perc = Column(Float)

    # 6. Informações de Descendentes e Extras
    descendentes_filhos_quantidade = Column(Integer)
    descendentes_rebanhos_quantidade = Column(Integer)
    descendentes_netos_quantidade = Column(Integer)
    extra_genotipado = Column(Boolean)
    extra_csg = Column(Boolean)

    # 7. Fenótipos e Medidas Reais
    fenotipo_ipp_dias = Column(Integer)
    medida_aol_cm2 = Column(Float)
    medida_acabamento_mm = Column(Float)
    peso_p120_kg = Column(Float)
    peso_p210_kg = Column(Float)
    peso_p365_kg = Column(Float)
    peso_p450_kg = Column(Float)
    medida_pe365_cm = Column(Float)

    # Metadata
    fonte_origem = Column(String(20), default="PMGZ")
    data_processamento = Column(DateTime, default=datetime.utcnow)