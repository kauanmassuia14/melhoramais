-- Database Schema for Melhora+ Genetic Data Unifier

-- Create schema silver if not exists
CREATE SCHEMA IF NOT EXISTS silver;

-- Master Table: silver.animais (The Data Contract)
CREATE TABLE IF NOT EXISTS silver.animais (
    id_animal SERIAL PRIMARY KEY,
    rgn_animal VARCHAR(50) UNIQUE NOT NULL, -- Registro Geral Nacional (MANDATORY)
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
    im_idade_primeiro_parto FLOAT, -- IPP (Genetic index equivalent)
    
    -- Metadata
    fonte_origem VARCHAR(50), -- ANCP, PMGZ, Geneplus
    data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dynamic Mapping Table: silver.column_mapping
CREATE TABLE IF NOT EXISTS silver.column_mapping (
    id SERIAL PRIMARY KEY,
    source_system VARCHAR(50) NOT NULL, -- 'ANCP', 'PMGZ', 'Geneplus'
    source_column VARCHAR(100) NOT NULL, -- Name in the raw file
    target_column VARCHAR(100) NOT NULL, -- Name in silver.animais
    data_type VARCHAR(20) DEFAULT 'float', -- float, date, string
    UNIQUE(source_system, source_column)
);

-- Initial Mapping Data
INSERT INTO silver.column_mapping (source_system, source_column, target_column, data_type) VALUES
-- ANCP Mappings
('ANCP', 'RGN', 'rgn_animal', 'string'),
('ANCP', 'NOME', 'nome_animal', 'string'),
('ANCP', 'SEXO', 'sexo', 'string'),
('ANCP', 'DT_NASC', 'data_nascimento', 'date'),
('ANCP', 'PESO_DESM', 'p210_peso_desmama', 'float'),
('ANCP', 'PESO_SOBRE', 'p450_peso_sobreano', 'float'),

-- PMGZ Mappings
('PMGZ', 'Registro', 'rgn_animal', 'string'),
('PMGZ', 'Nome', 'nome_animal', 'string'),
('PMGZ', 'P210', 'p210_peso_desmama', 'float'),
('PMGZ', 'P365', 'p365_peso_ano', 'float'),
('PMGZ', 'P450', 'p450_peso_sobreano', 'float'),

-- Geneplus Mappings
('Geneplus', 'PREFIXO_RGN', 'rgn_animal', 'string'),
('Geneplus', 'P_DESM', 'p210_peso_desmama', 'float'),
('Geneplus', 'P_SOBRE', 'p450_peso_sobreano', 'float');
