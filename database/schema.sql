-- Database Schema for Melhora+ Genetic Data Unifier
-- Clean Architecture: Silver Layer with Multi-Tenancy

-- Create schemas
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS audit;

-- ============================================
-- FARM TABLE (Multi-Tenancy)
-- ============================================
CREATE TABLE IF NOT EXISTS silver.fazendas (
    id_farm SERIAL PRIMARY KEY,
    nome_farm VARCHAR(255) NOT NULL,
    cnpj VARCHAR(20) UNIQUE,
    responsavel VARCHAR(255),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- MASTER TABLE: silver.animais (The Data Contract)
-- ============================================
CREATE TABLE IF NOT EXISTS silver.animais (
    id_animal SERIAL PRIMARY KEY,
    id_farm INTEGER NOT NULL REFERENCES silver.fazendas(id_farm),
    rgn_animal VARCHAR(50) NOT NULL,
    nome_animal VARCHAR(255),
    raca VARCHAR(50),
    sexo CHAR(1) CHECK (sexo IN ('M', 'F')),
    data_nascimento DATE,
    mae_rgn VARCHAR(50),
    pai_rgn VARCHAR(50),

    -- Standard Cattle Genetic Indices
    p210_peso_desmama FLOAT,
    p365_peso_ano FLOAT,
    p450_peso_sobreano FLOAT,
    pe_perimetro_escrotal FLOAT,
    a_area_olho_lombo FLOAT, -- AOL
    eg_espessura_gordura FLOAT, -- EGP
    im_idade_primeiro_parto FLOAT, -- IPP

    -- Metadata
    fonte_origem VARCHAR(50), -- ANCP, PMGZ, Geneplus
    data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraint: unique animal per farm (same RGN can exist in different farms)
    UNIQUE(id_farm, rgn_animal)
);

-- ============================================
-- DYNAMIC MAPPING TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS silver.column_mapping (
    id SERIAL PRIMARY KEY,
    source_system VARCHAR(50) NOT NULL, -- 'ANCP', 'PMGZ', 'Geneplus'
    source_column VARCHAR(100) NOT NULL, -- Name in the raw file
    target_column VARCHAR(100) NOT NULL, -- Name in silver.animais
    data_type VARCHAR(20) DEFAULT 'float', -- float, date, string
    is_required BOOLEAN DEFAULT false,
    UNIQUE(source_system, source_column)
);

-- ============================================
-- PROCESSING AUDIT LOG
-- ============================================
CREATE TABLE IF NOT EXISTS audit.processing_log (
    id SERIAL PRIMARY KEY,
    id_farm INTEGER REFERENCES silver.fazendas(id_farm),
    source_system VARCHAR(50) NOT NULL,
    filename VARCHAR(255),
    total_rows INTEGER DEFAULT 0,
    rows_inserted INTEGER DEFAULT 0,
    rows_updated INTEGER DEFAULT 0,
    rows_failed INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'processing', -- processing, completed, failed
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ============================================
-- PERFORMANCE INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_animais_farm ON silver.animais(id_farm);
CREATE INDEX IF NOT EXISTS idx_animais_rgn ON silver.animais(rgn_animal);
CREATE INDEX IF NOT EXISTS idx_animais_farm_rgn ON silver.animais(id_farm, rgn_animal);
CREATE INDEX IF NOT EXISTS idx_animais_fonte ON silver.animais(fonte_origem);
CREATE INDEX IF NOT EXISTS idx_animais_raca ON silver.animais(raca);
CREATE INDEX IF NOT EXISTS idx_processing_log_farm ON audit.processing_log(id_farm);

-- ============================================
-- RAW DATA TABLE: Stores ALL columns from original files
-- ============================================
CREATE TABLE IF NOT EXISTS silver.raw_animal_data (
    id SERIAL PRIMARY KEY,
    id_animal INTEGER REFERENCES silver.animais(id_animal) ON DELETE CASCADE,
    id_farm INTEGER NOT NULL REFERENCES silver.fazendas(id_farm),
    source_system VARCHAR(50) NOT NULL,
    processing_log_id INTEGER REFERENCES audit.processing_log(id),
    raw_data JSONB NOT NULL,  -- ALL 111 columns from the original file
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_data_animal ON silver.raw_animal_data(id_animal);
CREATE INDEX IF NOT EXISTS idx_raw_data_farm ON silver.raw_animal_data(id_farm);
CREATE INDEX IF NOT EXISTS idx_raw_data_source ON silver.raw_animal_data(source_system);

-- ============================================
-- INITIAL DATA: Default Farm (for dev)
-- ============================================
INSERT INTO silver.fazendas (nome_farm, responsavel)
VALUES ('Fazenda Desenvolvimento', 'Admin')
ON CONFLICT DO NOTHING;

-- ============================================
-- MAPPING DATA: ANCP -> silver.animais
-- ============================================
INSERT INTO silver.column_mapping (source_system, source_column, target_column, data_type, is_required) VALUES
-- ANCP
('ANCP', 'RGN', 'rgn_animal', 'string', true),
('ANCP', 'NOME', 'nome_animal', 'string', false),
('ANCP', 'SEXO', 'sexo', 'string', false),
('ANCP', 'DT_NASC', 'data_nascimento', 'date', false),
('ANCP', 'RACA', 'raca', 'string', false),
('ANCP', 'MAE_RGN', 'mae_rgn', 'string', false),
('ANCP', 'PAI_RGN', 'pai_rgn', 'string', false),
('ANCP', 'PESO_DESM', 'p210_peso_desmama', 'float', false),
('ANCP', 'PESO_SOBRE', 'p450_peso_sobreano', 'float', false),
('ANCP', 'P365', 'p365_peso_ano', 'float', false),
('ANCP', 'PE', 'pe_perimetro_escrotal', 'float', false),
('ANCP', 'AOL', 'a_area_olho_lombo', 'float', false),
('ANCP', 'EGP', 'eg_espessura_gordura', 'float', false),
('ANCP', 'IPP', 'im_idade_primeiro_parto', 'float', false),

-- PMGZ
('PMGZ', 'Registro', 'rgn_animal', 'string', true),
('PMGZ', 'Nome', 'nome_animal', 'string', false),
('PMGZ', 'Sexo', 'sexo', 'string', false),
('PMGZ', 'Data_Nasc', 'data_nascimento', 'date', false),
('PMGZ', 'Raca', 'raca', 'string', false),
('PMGZ', 'Mae_Reg', 'mae_rgn', 'string', false),
('PMGZ', 'Pai_Reg', 'pai_rgn', 'string', false),
('PMGZ', 'P210', 'p210_peso_desmama', 'float', false),
('PMGZ', 'P365', 'p365_peso_ano', 'float', false),
('PMGZ', 'P450', 'p450_peso_sobreano', 'float', false),
('PMGZ', 'PE', 'pe_perimetro_escrotal', 'float', false),
('PMGZ', 'AOL', 'a_area_olho_lombo', 'float', false),
('PMGZ', 'EGP', 'eg_espessura_gordura', 'float', false),

-- Geneplus
('Geneplus', 'PREFIXO_RGN', 'rgn_animal', 'string', true),
('Geneplus', 'NOME', 'nome_animal', 'string', false),
('Geneplus', 'SEXO', 'sexo', 'string', false),
('Geneplus', 'DT_NASC', 'data_nascimento', 'date', false),
('Geneplus', 'RACA', 'raca', 'string', false),
('Geneplus', 'MAE_RGN', 'mae_rgn', 'string', false),
('Geneplus', 'PAI_RGN', 'pai_rgn', 'string', false),
('Geneplus', 'P_DESM', 'p210_peso_desmama', 'float', false),
('Geneplus', 'P365', 'p365_peso_ano', 'float', false),
('Geneplus', 'P_SOBRE', 'p450_peso_sobreano', 'float', false),
('Geneplus', 'PE', 'pe_perimetro_escrotal', 'float', false),
('Geneplus', 'AOL', 'a_area_olho_lombo', 'float', false),
('Geneplus', 'EGP', 'eg_espessura_gordura', 'float', false),
('Geneplus', 'IPP', 'im_idade_primeiro_parto', 'float', false)
ON CONFLICT (source_system, source_column) DO NOTHING;
