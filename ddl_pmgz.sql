-- DDL para PostgreSQL - Tabela animais_pmgz
-- Sistema: Melhora+ - Dados Genéticos PMGZ
-- Executar após criação do schema silver

CREATE TABLE IF NOT EXISTS silver.animais_pmgz (
    -- PK e FK
    id SERIAL PRIMARY KEY,
    id_farm INTEGER NOT NULL REFERENCES silver.fazendas(id_farm),
    upload_id UUID REFERENCES silver.uploads(upload_id),
    processing_log_id INTEGER REFERENCES audit.processing_log(id),

    -- 1. Identificação do Animal
    identificacao_animal_nome VARCHAR(255),
    identificacao_animal_serie_rgd VARCHAR(50),
    identificacao_animal_rgn VARCHAR(50) NOT NULL,
    identificacao_animal_sexo CHAR(1),
    identificacao_animal_nascimento DATE,
    identificacao_indice_iabczg DOUBLE PRECISION,
    identificacao_indice_deca INTEGER,
    identificacao_indice_p_perc DOUBLE PRECISION,
    identificacao_indice_f_perc DOUBLE PRECISION,

    -- 2. Pedigree (Genealogia) - Pai
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

    -- 3. Características Genéticas: Crescimento
    -- PN-EDg
    genetica_crescimento_pn_edg_dep DOUBLE PRECISION,
    genetica_crescimento_pn_edg_ac_perc INTEGER,
    genetica_crescimento_pn_edg_deca INTEGER,
    genetica_crescimento_pn_edg_p_perc DOUBLE PRECISION,

    -- PD-EDg
    genetica_crescimento_pd_edg_dep DOUBLE PRECISION,
    genetica_crescimento_pd_edg_ac_perc INTEGER,
    genetica_crescimento_pd_edg_deca INTEGER,
    genetica_crescimento_pd_edg_p_perc DOUBLE PRECISION,

    -- PA-EDg
    genetica_crescimento_pa_edg_dep DOUBLE PRECISION,
    genetica_crescimento_pa_edg_ac_perc INTEGER,
    genetica_crescimento_pa_edg_deca INTEGER,
    genetica_crescimento_pa_edg_p_perc DOUBLE PRECISION,

    -- PS-EDg
    genetica_crescimento_ps_edg_dep DOUBLE PRECISION,
    genetica_crescimento_ps_edg_ac_perc INTEGER,
    genetica_crescimento_ps_edg_deca INTEGER,
    genetica_crescimento_ps_edg_p_perc DOUBLE PRECISION,

    -- PM-EMg
    genetica_crescimento_pm_emg_dep DOUBLE PRECISION,
    genetica_crescimento_pm_emg_ac_perc INTEGER,
    genetica_crescimento_pm_emg_deca INTEGER,
    genetica_crescimento_pm_emg_p_perc DOUBLE PRECISION,

    -- 4. Características Genéticas: Reprodutivas
    -- IPPg
    genetica_reprodutiva_ippg_dep DOUBLE PRECISION,
    genetica_reprodutiva_ippg_ac_perc INTEGER,
    genetica_reprodutiva_ippg_deca INTEGER,
    genetica_reprodutiva_ippg_p_perc DOUBLE PRECISION,

    -- STAYg
    genetica_reprodutiva_stayg_dep DOUBLE PRECISION,
    genetica_reprodutiva_stayg_ac_perc INTEGER,
    genetica_reprodutiva_stayg_deca INTEGER,
    genetica_reprodutiva_stayg_p_perc DOUBLE PRECISION,

    -- PE-365g
    genetica_reprodutiva_pe365g_dep DOUBLE PRECISION,
    genetica_reprodutiva_pe365g_ac_perc INTEGER,
    genetica_reprodutiva_pe365g_deca INTEGER,
    genetica_reprodutiva_pe365g_p_perc DOUBLE PRECISION,

    -- PE-450g
    genetica_reprodutiva_pe450g_dep DOUBLE PRECISION,
    genetica_reprodutiva_pe450g_ac_perc INTEGER,
    genetica_reprodutiva_pe450g_deca INTEGER,
    genetica_reprodutiva_pe450g_p_perc DOUBLE PRECISION,

    -- 5. Características Genéticas: Carcaça
    -- AOLg
    genetica_carcaca_aolg_dep DOUBLE PRECISION,
    genetica_carcaca_aolg_ac_perc INTEGER,
    genetica_carcaca_aolg_deca INTEGER,
    genetica_carcaca_aolg_p_perc DOUBLE PRECISION,

    -- ACABg
    genetica_carcaca_acabg_dep DOUBLE PRECISION,
    genetica_carcaca_acabg_ac_perc INTEGER,
    genetica_carcaca_acabg_deca INTEGER,
    genetica_carcaca_acabg_p_perc DOUBLE PRECISION,

    -- MARg
    genetica_carcaca_marg_dep DOUBLE PRECISION,
    genetica_carcaca_marg_ac_perc INTEGER,
    genetica_carcaca_marg_deca INTEGER,
    genetica_carcaca_marg_p_perc DOUBLE PRECISION,

    -- Características Morfológicas
    -- Eg
    genetica_morfologica_eg_dep DOUBLE PRECISION,
    genetica_morfologica_eg_ac_perc INTEGER,
    genetica_morfologica_eg_deca INTEGER,
    genetica_morfologica_eg_p_perc DOUBLE PRECISION,

    -- Pg
    genetica_morfologica_pg_dep DOUBLE PRECISION,
    genetica_morfologica_pg_ac_perc INTEGER,
    genetica_morfologica_pg_deca INTEGER,
    genetica_morfologica_pg_p_perc DOUBLE PRECISION,

    -- Mg
    genetica_morfologica_mg_dep DOUBLE PRECISION,
    genetica_morfologica_mg_ac_perc INTEGER,
    genetica_morfologica_mg_deca INTEGER,
    genetica_morfologica_mg_p_perc DOUBLE PRECISION,

    -- 6. Informações de Descendentes e Extras
    descendentes_filhos_quantidade INTEGER,
    descendentes_rebanhos_quantidade INTEGER,
    descendentes_netos_quantidade INTEGER,
    extra_genotipado BOOLEAN,
    extra_csg BOOLEAN,

    -- 7. Fenótipos e Medidas Reais
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

    -- Constraints
    CONSTRAINT uix_farm_pmgz_rgn UNIQUE (id_farm, identificacao_animal_rgn)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_animais_pmgz_farm ON silver.animais_pmgz(id_farm);
CREATE INDEX IF NOT EXISTS idx_animais_pmgz_rgn ON silver.animais_pmgz(identificacao_animal_rgn);
CREATE INDEX IF NOT EXISTS idx_animais_pmgz_sexo ON silver.animais_pmgz(identificacao_animal_sexo);
CREATE INDEX IF NOT EXISTS idx_animais_pmgz_nascimento ON silver.animais_pmgz(identificacao_animal_nascimento);
CREATE INDEX IF NOT EXISTS idx_animais_pmgz_iabczg ON silver.animais_pmgz(identificacao_indice_iabczg);

COMMENT ON TABLE silver.animais_pmgz IS 'Tabela específica para dados PMGZ - Programa de Melhoramento Genético de Zebuínos';