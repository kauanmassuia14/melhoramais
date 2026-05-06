-- DDL: Sistema de Melhoramento Genético Bovino - Projeto Melhora+
-- Versão: 1.1 - Multi-Tenant (Suporte a múltiplas fazendas)
-- Data: 2026-05-06

-- ============================================
-- SCHEMAS
-- ============================================
DROP SCHEMA IF EXISTS genetics CASCADE;
DROP SCHEMA IF EXISTS silver CASCADE;

CREATE SCHEMA IF NOT EXISTS genetics;
CREATE SCHEMA IF NOT EXISTS silver;

-- ============================================
-- 1. ENUMS
-- ============================================

CREATE TYPE genetics.animal_sex AS ENUM ('M', 'F');

CREATE TYPE genetics.boolean_status AS ENUM ('SIM', 'NÃO');

-- ============================================
-- 2. COMPOSITE TYPES
-- ============================================

CREATE TYPE genetics.metric_block AS (
    dep NUMERIC,
    ac NUMERIC,
    deca INTEGER,
    p_percent NUMERIC
);

CREATE TYPE genetics.progeny_info AS (
    filhos INTEGER,
    rebanhos INTEGER
);

-- ============================================
-- 3. TABELA: farms (Fazendas - Multi-Tenancy)
-- ============================================

CREATE TABLE genetics.farms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(255) NOT NULL,
    documento VARCHAR(20),  -- CNPJ ou CPF
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uix_farm_documento UNIQUE(documento)
);

-- Indexes para farms
CREATE INDEX idx_farms_nome ON genetics.farms(nome);
CREATE INDEX idx_farms_documento ON genetics.farms(documento);

-- ============================================
-- 4. TABELA: animals (Centralização de Indivíduos)
-- ============================================

CREATE TABLE genetics.animals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES genetics.farms(id),

    nome VARCHAR(255),
    serie VARCHAR(50),
    rgn VARCHAR(50) NOT NULL,
    sexo genetics.animal_sex,
    nascimento DATE,
    genotipado genetics.boolean_status,
    csg genetics.boolean_status,

    -- Auto-relacionamento (Genealogia)
    -- Permite referências de outras fazendas (sêmen/embrião externo)
    sire_id UUID REFERENCES genetics.animals(id),
    dam_id UUID REFERENCES genetics.animals(id),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraint: único por fazenda (RGN não é único no mundo, apenas por fazenda)
    CONSTRAINT uix_farm_rgn UNIQUE(farm_id, rgn)
);

-- Indexes para animals (incluindo farm_id para otimização)
CREATE INDEX idx_animals_farm ON genetics.animals(farm_id);
CREATE INDEX idx_animals_farm_rgn ON genetics.animals(farm_id, rgn);
CREATE INDEX idx_animals_farm_sexo ON genetics.animals(farm_id, sexo);
CREATE INDEX idx_animals_farm_nascimento ON genetics.animals(farm_id, nascimento);
CREATE INDEX idx_animals_sire ON genetics.animals(sire_id);
CREATE INDEX idx_animals_dam ON genetics.animals(dam_id);
CREATE INDEX idx_animals_farm_sire ON genetics.animals(farm_id, sire_id) WHERE sire_id IS NOT NULL;
CREATE INDEX idx_animals_farm_dam ON genetics.animals(farm_id, dam_id) WHERE dam_id IS NOT NULL;

-- ============================================
-- 5. TABELA: genetic_evaluations (1:N - Histórico por Safra)
-- ============================================

CREATE TABLE genetics.genetic_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    animal_id UUID NOT NULL REFERENCES genetics.animals(id),
    farm_id UUID NOT NULL REFERENCES genetics.farms(id),

    -- Identificação da avaliação
    safra INTEGER NOT NULL,
    fonte_origem VARCHAR(20) CHECK (fonte_origem IN ('PMGZ', 'ANCP', 'GENEPLUS')),

    -- Campos globais de avaliação
    iabczg NUMERIC,
    deca_index INTEGER,

    -- ============================================
    -- CRESCIMENTO (metric_block)
    -- ============================================
    pn_ed genetics.metric_block,  -- Peso Nascimento
    pd_ed genetics.metric_block,   -- Peso Desmama
    pa_ed genetics.metric_block,   -- Peso Ano
    ps_ed genetics.metric_block,   -- Peso Sobreano
    pm_em genetics.metric_block,   -- Peso Materno (Maternal)

    -- ============================================
    -- REPRODUTIVAS/MATERNAS (metric_block)
    -- ============================================
    ipp genetics.metric_block,          -- Idade Primeiro Parto
    stay genetics.metric_block,         -- Stayability (LONGEVIDADE)
    pe_365 genetics.metric_block,       -- Perímetro Escrotal 365 dias
    psn genetics.metric_block,         -- Precocidade Sexual

    -- ============================================
    -- CARCAÇA (metric_block)
    -- ============================================
    aol genetics.metric_block,      -- Área Olho de Lobo
    acab genetics.metric_block,     -- Acabamento
    marmoreio genetics.metric_block, -- Marmoreio (Maciez)

    -- ============================================
    -- MORFOLÓGICAS (metric_block)
    -- ============================================
    eg genetics.metric_block,       -- Estrutura
    pg genetics.metric_block,       -- Precocidade
    mg genetics.metric_block,       -- Musculosidade

    -- ============================================
    -- MEDIDAS FENOTÍPICAS (NUMERIC simples)
    -- ============================================
    fenotipo_aol NUMERIC,   -- AOL medida real (cm²)
    fenotipo_acab NUMERIC,  -- Acabamento real (mm)
    fenotipo_ipp NUMERIC,   -- IPP real (dias)
    fenotipo_stay NUMERIC,  -- Stay real (dias/%)

    -- ============================================
    -- INFORMAÇÕES DE DESCENDENTES (progeny_info)
    -- ============================================
    p120_info genetics.progeny_info,
    p210_info genetics.progeny_info,
    p365_info genetics.progeny_info,
    p450_info genetics.progeny_info,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT uix_farm_animal_safra UNIQUE(farm_id, animal_id, safra)
);

-- Indexes para genetic_evaluations (incluindo farm_id para otimização de dashboards)
CREATE INDEX idx_ge_farm ON genetics.genetic_evaluations(farm_id);
CREATE INDEX idx_ge_farm_safra ON genetics.genetic_evaluations(farm_id, safra);
CREATE INDEX idx_ge_animal ON genetics.genetic_evaluations(animal_id);
CREATE INDEX idx_ge_farm_iabczg ON genetics.genetic_evaluations(farm_id, iabczg) WHERE iabczg IS NOT NULL;
CREATE INDEX idx_ge_fonte ON genetics.genetic_evaluations(fonte_origem);
CREATE INDEX idx_ge_safra ON genetics.genetic_evaluations(safra);

-- ============================================
-- 6. TABELA: evaluation_progeny_history (Histórico de Descendentes Detalhado)
-- ============================================

CREATE TABLE genetics.evaluation_progeny_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID NOT NULL REFERENCES genetics.genetic_evaluations(id) ON DELETE CASCADE,

    periodo VARCHAR(10) NOT NULL,  -- 'P120', 'P210', 'P365', 'P450'
    filhos INTEGER,
    rebanhos INTEGER,
    netos INTEGER,
    neto_rebanhos INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uix_eval_periodo UNIQUE(evaluation_id, periodo)
);

CREATE INDEX idx_eph_evaluation ON genetics.evaluation_progeny_history(evaluation_id);

-- ============================================
-- 7. VIEWS
-- ============================================

-- View completa de animais com fazenda
CREATE OR REPLACE VIEW genetics.v_animals_full AS
SELECT
    a.id,
    a.farm_id,
    f.nome AS farm_nome,
    a.nome AS animal_nome,
    a.serie,
    a.rgn,
    a.sexo,
    a.nascimento,
    a.genotipado,
    a.csg,
    a.sire_id,
    a.dam_id,
    s.farm_id AS sire_farm_id,
    s.rgn AS sire_rgn,
    s.nome AS sire_nome,
    d.farm_id AS dam_farm_id,
    d.rgn AS dam_rgn,
    d.nome AS dam_nome,
    COUNT(ge.id) AS total_evaluations,
    MAX(ge.safra) AS ultima_safra,
    MAX(ge.iabczg) AS ultimo_iabczg,
    a.created_at,
    a.updated_at
FROM genetics.animals a
JOIN genetics.farms f ON a.farm_id = f.id
LEFT JOIN genetics.animals s ON a.sire_id = s.id
LEFT JOIN genetics.animals d ON a.dam_id = d.id
LEFT JOIN genetics.genetic_evaluations ge ON a.id = ge.animal_id
GROUP BY a.id, a.farm_id, f.nome, a.nome, a.serie, a.rgn, a.sexo, a.nascimento,
         a.genotipado, a.csg, a.sire_id, a.dam_id,
         s.farm_id, s.rgn, s.nome, d.farm_id, d.rgn, d.nome,
         a.created_at, a.updated_at;

-- View para dashboard de fazenda (filtro rápido por fazenda)
CREATE OR REPLACE VIEW genetics.v_dashboard_farm AS
SELECT
    f.id AS farm_id,
    f.nome AS farm_nome,
    COUNT(DISTINCT a.id) AS total_animais,
    COUNT(DISTINCT a.id) FILTER (WHERE a.sexo = 'M') AS total_machos,
    COUNT(DISTINCT a.id) FILTER (WHERE a.sexo = 'F') AS total_fêmeas,
    COUNT(DISTINCT ge.id) AS total_avaliacoes,
    MAX(ge.safra) AS ultima_safra,
    COUNT(DISTINCT a.id) FILTER (WHERE a.genotipado = 'SIM') AS total_genotipados,
    ROUND(AVG(ge.iabczg), 2) AS media_iabczg
FROM genetics.farms f
LEFT JOIN genetics.animals a ON f.id = a.farm_id
LEFT JOIN genetics.genetic_evaluations ge ON a.id = ge.animal_id AND f.id = ge.farm_id
GROUP BY f.id, f.nome;

-- View para ranking de animais por fazenda
CREATE OR REPLACE VIEW genetics.v_animal_ranking AS
SELECT
    a.farm_id,
    f.nome AS farm_nome,
    a.id AS animal_id,
    a.rgn,
    a.nome AS animal_nome,
    a.sexo,
    ge.safra,
    ge.iabczg,
    ge.deca_index,
    ROW_NUMBER() OVER (PARTITION BY a.farm_id, ge.safra ORDER BY ge.iabczg DESC) AS ranking
FROM genetics.animals a
JOIN genetics.farms f ON a.farm_id = f.id
JOIN genetics.genetic_evaluations ge ON a.id = ge.animal_id AND f.id = ge.farm_id
WHERE ge.iabczg IS NOT NULL;

-- ============================================
-- 8. FUNÇÕES AUXILIARES
-- ============================================

-- Função para atualizar timestamp automático
CREATE OR REPLACE FUNCTION genetics.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para updated_at em farms
CREATE TRIGGER trigger_farms_updated_at
    BEFORE UPDATE ON genetics.farms
    FOR EACH ROW
    EXECUTE FUNCTION genetics.update_updated_at();

-- Trigger para updated_at em animals
CREATE TRIGGER trigger_animals_updated_at
    BEFORE UPDATE ON genetics.animals
    FOR EACH ROW
    EXECUTE FUNCTION genetics.update_updated_at();

-- Trigger para updated_at em genetic_evaluations
CREATE TRIGGER trigger_genetic_evaluations_updated_at
    BEFORE UPDATE ON genetics.genetic_evaluations
    FOR EACH ROW
    EXECUTE FUNCTION genetics.update_updated_at();

-- Função para obter árvore genealógica completa (até 4 gerações)
CREATE OR REPLACE FUNCTION genetics.get_pedigree(p_animal_id UUID)
RETURNS TABLE (
    geracao INTEGER,
    animal_id UUID,
    rgn VARCHAR,
    nome VARCHAR,
    sexo genetics.animal_sex
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE pedigree AS (
        -- Geração 0: Animal atual
        SELECT 0 AS geracao, id, rgn, nome, sexo FROM genetics.animals WHERE id = p_animal_id
        UNION ALL
        -- Geração N+1: Pais
        SELECT
            p.geracao + 1,
            a.id,
            a.rgn,
            a.nome,
            a.sexo
        FROM pedigree p
        JOIN genetics.animals a ON a.id = p.animal_id
        WHERE p.geracao < 4  -- Limite de 4 gerações
    )
    SELECT * FROM pedigree;
END;
$$ LANGUAGE plpgsql;

-- Função para validar que sire/dam são da mesma fazenda (opcional)
CREATE OR REPLACE FUNCTION genetics.validate_same_farm(p_animal_id UUID, p_sire_id UUID, p_dam_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_farm_id UUID;
    v_sire_farm UUID;
    v_dam_farm UUID;
BEGIN
    SELECT farm_id INTO v_farm_id FROM genetics.animals WHERE id = p_animal_id;

    IF p_sire_id IS NOT NULL THEN
        SELECT farm_id INTO v_sire_farm FROM genetics.animals WHERE id = p_sire_id;
    END IF;

    IF p_dam_id IS NOT NULL THEN
        SELECT farm_id INTO v_dam_farm FROM genetics.animals WHERE id = p_dam_id;
    END IF;

    -- Retorna TRUE se todos forem da mesma fazenda ou se pais forem NULL
    RETURN (v_sire_farm IS NULL OR v_sire_farm = v_farm_id)
       AND (v_dam_farm IS NULL OR v_dam_farm = v_farm_id);
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 9. SEED DATA (Dados de exemplo)
-- ============================================

-- Inserir fazendas de exemplo
INSERT INTO genetics.farms (id, nome, documento) VALUES
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Fazenda Boa Vista', '12.345.678/0001-90'),
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'Fazenda Santa Luz', '23.456.789/0001-01'),
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'Fazenda Recanto Verde', '34.567.890/0001-12')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- COMENTÁRIOS (DOCUMENTAÇÃO)
-- ============================================

COMMENT ON TYPE genetics.animal_sex IS 'Sexo do animal: M=Macho, F=Fêmea';
COMMENT ON TYPE genetics.boolean_status IS 'Status booleano: SIM ou NÃO';
COMMENT ON TYPE genetics.metric_block IS 'Bloco de métricas genéticas: DEP, AC%, DECA, P%';
COMMENT ON TYPE genetics.progeny_info IS 'Informações de descendentes: filhos e rebanhos';

COMMENT ON TABLE genetics.farms IS 'Tabela de fazendas - Multi-Tenancy';
COMMENT ON TABLE genetics.animals IS 'Tabela central de indivíduos bovinos (animal do registro, pais e avós) - Multi-Tenant';
COMMENT ON TABLE genetics.genetic_evaluations IS 'Avaliações genéticas por animal, fazenda e safra';

COMMENT ON COLUMN genetics.farms.documento IS 'CNPJ ou CPF da fazenda';
COMMENT ON COLUMN genetics.animals.farm_id IS 'Fazenda proprietária do animal';
COMMENT ON COLUMN genetics.animals.sire_id IS 'ID do pai (sire) - pode ser de outra fazenda (sêmen externo)';
COMMENT ON COLUMN genetics.animals.dam_id IS 'ID da mãe (dam) - pode ser de outra fazenda (embrião externo)';
COMMENT ON COLUMN genetics.genetic_evaluations.farm_id IS 'Fazenda para filtro direto sem JOIN';

COMMENT ON CONSTRAINT genetics.uix_farm_rgn ON genetics.animals IS 'RGN único por fazenda, não no mundo';
COMMENT ON CONSTRAINT genetics.uix_farm_animal_safra ON genetics.genetic_evaluations IS 'Avaliação única por fazenda/animal/safra';