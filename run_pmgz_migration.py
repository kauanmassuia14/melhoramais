#!/usr/bin/env python3
"""Script para criar a tabela animais_pmgz no banco de produção via SQL direto."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine
from sqlalchemy import text

ddl_tabela = """
CREATE TABLE IF NOT EXISTS silver.animais_pmgz (
    id SERIAL PRIMARY KEY,
    id_farm INTEGER NOT NULL,
    upload_id VARCHAR(36),
    processing_log_id INTEGER,

    -- Identificação do Animal
    identificacao_animal_nome VARCHAR(255),
    identificacao_animal_serie_rgd VARCHAR(50),
    identificacao_animal_rgn VARCHAR(50) NOT NULL,
    identificacao_animal_sexo CHAR(1),
    identificacao_animal_nascimento DATE,
    identificacao_indice_iabczg DOUBLE PRECISION,
    identificacao_indice_deca INTEGER,
    identificacao_indice_p_perc DOUBLE PRECISION,
    identificacao_indice_f_perc DOUBLE PRECISION,

    -- Pedigree - Pai
    pedigree_pai_nome VARCHAR(255),
    pedigree_pai_serie_rgd VARCHAR(50),
    pedigree_pai_rgn VARCHAR(50),

    -- Pedigree - Avô Paterno
    pedigree_avo_paterno_nome VARCHAR(255),
    pedigree_avo_paterno_serie_rgd VARCHAR(50),
    pedigree_avo_paterno_rgn VARCHAR(50),

    -- Pedigree - Avó Paterna
    pedigree_avo_paterna_nome VARCHAR(255),
    pedigree_avo_paterna_serie_rgd VARCHAR(50),
    pedigree_avo_paterna_rgn VARCHAR(50),

    -- Pedigree - Mãe
    pedigree_mae_nome VARCHAR(255),
    pedigree_mae_serie_rgd VARCHAR(50),
    pedigree_mae_rgn VARCHAR(50),

    -- Pedigree - Avô Materno
    pedigree_avo_materno_nome VARCHAR(255),
    pedigree_avo_materno_serie_rgd VARCHAR(50),
    pedigree_avo_materno_rgn VARCHAR(50),

    -- Pedigree - Avó Materna
    pedigree_avo_materna_nome VARCHAR(255),
    pedigree_avo_materna_serie_rgd VARCHAR(50),
    pedigree_avo_materna_rgn VARCHAR(50),

    -- Crescimento - PN-EDg
    genetica_crescimento_pn_edg_dep DOUBLE PRECISION,
    genetica_crescimento_pn_edg_ac_perc INTEGER,
    genetica_crescimento_pn_edg_deca INTEGER,
    genetica_crescimento_pn_edg_p_perc DOUBLE PRECISION,

    -- Crescimento - PD-EDg
    genetica_crescimento_pd_edg_dep DOUBLE PRECISION,
    genetica_crescimento_pd_edg_ac_perc INTEGER,
    genetica_crescimento_pd_edg_deca INTEGER,
    genetica_crescimento_pd_edg_p_perc DOUBLE PRECISION,

    -- Crescimento - PA-EDg
    genetica_crescimento_pa_edg_dep DOUBLE PRECISION,
    genetica_crescimento_pa_edg_ac_perc INTEGER,
    genetica_crescimento_pa_edg_deca INTEGER,
    genetica_crescimento_pa_edg_p_perc DOUBLE PRECISION,

    -- Crescimento - PS-EDg
    genetica_crescimento_ps_edg_dep DOUBLE PRECISION,
    genetica_crescimento_ps_edg_ac_perc INTEGER,
    genetica_crescimento_ps_edg_deca INTEGER,
    genetica_crescimento_ps_edg_p_perc DOUBLE PRECISION,

    -- Crescimento - PM-EMg
    genetica_crescimento_pm_emg_dep DOUBLE PRECISION,
    genetica_crescimento_pm_emg_ac_perc INTEGER,
    genetica_crescimento_pm_emg_deca INTEGER,
    genetica_crescimento_pm_emg_p_perc DOUBLE PRECISION,

    -- Reprodutivas - IPPg
    genetica_reprodutiva_ippg_dep DOUBLE PRECISION,
    genetica_reprodutiva_ippg_ac_perc INTEGER,
    genetica_reprodutiva_ippg_deca INTEGER,
    genetica_reprodutiva_ippg_p_perc DOUBLE PRECISION,

    -- Reprodutivas - STAYg
    genetica_reprodutiva_stayg_dep DOUBLE PRECISION,
    genetica_reprodutiva_stayg_ac_perc INTEGER,
    genetica_reprodutiva_stayg_deca INTEGER,
    genetica_reprodutiva_stayg_p_perc DOUBLE PRECISION,

    -- Reprodutivas - PE-365g
    genetica_reprodutiva_pe365g_dep DOUBLE PRECISION,
    genetica_reprodutiva_pe365g_ac_perc INTEGER,
    genetica_reprodutiva_pe365g_deca INTEGER,
    genetica_reprodutiva_pe365g_p_perc DOUBLE PRECISION,

    -- Reprodutivas - PE-450g
    genetica_reprodutiva_pe450g_dep DOUBLE PRECISION,
    genetica_reprodutiva_pe450g_ac_perc INTEGER,
    genetica_reprodutiva_pe450g_deca INTEGER,
    genetica_reprodutiva_pe450g_p_perc DOUBLE PRECISION,

    -- Carcaça - AOLg
    genetica_carcaca_aolg_dep DOUBLE PRECISION,
    genetica_carcaca_aolg_ac_perc INTEGER,
    genetica_carcaca_aolg_deca INTEGER,
    genetica_carcaca_aolg_p_perc DOUBLE PRECISION,

    -- Carcaça - ACABg
    genetica_carcaca_acabg_dep DOUBLE PRECISION,
    genetica_carcaca_acabg_ac_perc INTEGER,
    genetica_carcaca_acabg_deca INTEGER,
    genetica_carcaca_acabg_p_perc DOUBLE PRECISION,

    -- Carcaça - MARg
    genetica_carcaca_marg_dep DOUBLE PRECISION,
    genetica_carcaca_marg_ac_perc INTEGER,
    genetica_carcaca_marg_deca INTEGER,
    genetica_carcaca_marg_p_perc DOUBLE PRECISION,

    -- Morfológicas - Eg
    genetica_morfologica_eg_dep DOUBLE PRECISION,
    genetica_morfologica_eg_ac_perc INTEGER,
    genetica_morfologica_eg_deca INTEGER,
    genetica_morfologica_eg_p_perc DOUBLE PRECISION,

    -- Morfológicas - Pg
    genetica_morfologica_pg_dep DOUBLE PRECISION,
    genetica_morfologica_pg_ac_perc INTEGER,
    genetica_morfologica_pg_deca INTEGER,
    genetica_morfologica_pg_p_perc DOUBLE PRECISION,

    -- Morfológicas - Mg
    genetica_morfologica_mg_dep DOUBLE PRECISION,
    genetica_morfologica_mg_ac_perc INTEGER,
    genetica_morfologica_mg_deca INTEGER,
    genetica_morfologica_mg_p_perc DOUBLE PRECISION,

    -- Descendentes e Extras
    descendentes_filhos_quantidade INTEGER,
    descendentes_rebanhos_quantidade INTEGER,
    descendentes_netos_quantidade INTEGER,
    extra_genotipado BOOLEAN,
    extra_csg BOOLEAN,

    -- Fenótipos
    fenotipo_ipp_dias INTEGER,
    medida_aol_cm2 DOUBLE PRECISION,
    medida_acabamento_mm DOUBLE PRECISION,
    peso_p120_kg DOUBLE PRECISION,
    peso_p210_kg DOUBLE PRECISION,
    peso_p365_kg DOUBLE PRECISION,
    peso_p450_kg DOUBLE PRECISION,
    medida_pe365_cm DOUBLE PRECISION,

    -- Metadata
    fonte_origem VARCHAR(20) DEFAULT 'PMGZ',
    data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uix_farm_pmgz_rgn UNIQUE (id_farm, identificacao_animal_rgn)
);
"""

indices = """
CREATE INDEX IF NOT EXISTS idx_animais_pmgz_farm ON silver.animais_pmgz(id_farm);
CREATE INDEX IF NOT EXISTS idx_animais_pmgz_rgn ON silver.animais_pmgz(identificacao_animal_rgn);
CREATE INDEX IF NOT EXISTS idx_animais_pmgz_sexo ON silver.animais_pmgz(identificacao_animal_sexo);
CREATE INDEX IF NOT EXISTS idx_animais_pmgz_nascimento ON silver.animais_pmgz(identificacao_animal_nascimento);
CREATE INDEX IF NOT EXISTS idx_animais_pmgz_iabczg ON silver.animais_pmgz(identificacao_indice_iabczg);
"""

# FKs separadamente para não falhar tudo se uma der problema
fks = [
    ("fk_pmgz_farm", "ALTER TABLE silver.animais_pmgz ADD CONSTRAINT fk_pmgz_farm FOREIGN KEY (id_farm) REFERENCES silver.fazendas(id_farm) ON DELETE CASCADE;"),
    ("fk_pmgz_upload", "ALTER TABLE silver.animais_pmgz ADD CONSTRAINT fk_pmgz_upload FOREIGN KEY (upload_id) REFERENCES silver.uploads(upload_id) ON DELETE SET NULL;"),
    ("fk_pmgz_log", "ALTER TABLE silver.animais_pmgz ADD CONSTRAINT fk_pmgz_log FOREIGN KEY (processing_log_id) REFERENCES audit.processing_log(id) ON DELETE SET NULL;"),
]

print("=" * 60)
print("CRIANDO TABELA animais_pmgz NO BANCO DE PRODUÇÃO")
print("=" * 60)
print(f"Database: {engine.url}")
print()

try:
    with engine.begin() as conn:
        # 1. Criar tabela
        conn.execute(text(ddl_tabela))
        print("✅ Tabela criada")

        # 2. Criar índices
        conn.execute(text(indices))
        print("✅ 5 índices criados")

        # 3. Criar FKs (uma por vez, se falhar continua)
        for nome_fk, sql_fk in fks:
            try:
                conn.execute(text(sql_fk))
                print(f"✅ FK {nome_fk} criada")
            except Exception as e:
                print(f"⚠️  FK {nome_fk} ignorada (já existe ou erro): {str(e)[:50]}")

except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("Tabela silver.animais_pmgz PRONTA!")
print("=" * 60)