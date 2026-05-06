# Mapeamento de Colunas para Importação - Genética

Este documento define o mapeamento das colunas do arquivo fonte para as novas tabelas `genetics.animals` e `genetics.genetic_evaluations`.

## Animais (Tabela: genetics.animals)

| Coluna Origem | Coluna Destino | Tipo | Obrigatório |
|---------------|----------------|------|-------------|
| Registro | rgn | VARCHAR(50) | SIM |
| Nome | nome | VARCHAR(255) | NÃO |
| Serie | serie | VARCHAR(50) | NÃO |
| Sexo | sexo | animal_sex ('M', 'F') | NÃO |
| Data_Nasc | nascimento | DATE | NÃO |
| Genotipado | genotipado | boolean_status ('SIM', 'NÃO') | NÃO |
| CSG | csg | boolean_status ('SIM', 'NÃO') | NÃO |
| Pai_Reg | sire_id (lookup por RGN) | UUID | NÃO |
| Mae_Reg | dam_id (lookup por RGN) | UUID | NÃO |

## Avaliações Genéticas (Tabela: genetics.genetic_evaluations)

### Campos Gerais

| Coluna Origem | Coluna Destino | Tipo |
|---------------|----------------|------|
| IABCZg | iabczg | NUMERIC |
| DECA | deca_index | INTEGER |

### Crescimento (metric_block)

| Coluna Origem (DEP) | Coluna Origem (AC%) | Coluna Origem (DECA) | Coluna Origem (P%) | Campo Destino |
|---------------------|---------------------|----------------------|--------------------|----------------|
| PN-EDg_DEP | PN-EDg_AC% | PN-EDg_DECA | PN-EDg_P% | pn_ed |
| PD-EDg_DEP | PD-EDg_AC% | PD-EDg_DECA | PD-EDg_P% | pd_ed |
| PA-EDg_DEP | PA-EDg_AC% | PA-EDg_DECA | PA-EDg_P% | pa_ed |
| PS-EDg_DEP | PS-EDg_AC% | PS-EDg_DECA | PS-EDg_P% | ps_ed |
| PM-EMg_DEP | PM-EMg_AC% | PM-EMg_DECA | PM-EMg_P% | pm_em |

### Reprodutivas/Maternas (metric_block)

| Coluna Origem (DEP) | Coluna Origem (AC%) | Coluna Origem (DECA) | Coluna Origem (P%) | Campo Destino |
|---------------------|---------------------|----------------------|--------------------|----------------|
| IPPg_DEP | IPPg_AC% | IPPg_DECA | IPPg_P% | ipp |
| STAYg_DEP | STAYg_AC% | STAYg_DECA | STAYg_P% | stay |
| PE-365g_DEP | PE-365g_AC% | PE-365g_DECA | PE-365g_P% | pe_365 |
| PSNg_DEP | PSNg_AC% | PSNg_DECA | PSNg_P% | psn |
| PM-EMg_DEP | PM-EMg_AC% | PM-EMg_DECA | PM-EMg_P% | pm_em |

### Carcaça (metric_block)

| Coluna Origem (DEP) | Coluna Origem (AC%) | Coluna Origem (DECA) | Coluna Origem (P%) | Campo Destino |
|---------------------|---------------------|----------------------|--------------------|----------------|
| AOLg_DEP | AOLg_AC% | AOLg_DECA | AOLg_P% | aol |
| ACABg_DEP | ACABg_AC% | ACABg_DECA | ACABg_P% | acab |
| MARg_DEP | MARg_AC% | MARg_DECA | MARg_P% | marmoreio |

### Morfológicas (metric_block)

| Coluna Origem (DEP) | Coluna Origem (AC%) | Coluna Origem (DECA) | Coluna Origem (P%) | Campo Destino |
|---------------------|---------------------|----------------------|--------------------|----------------|
| Eg_DEP | Eg_AC% | Eg_DECA | Eg_P% | eg |
| Pg_DEP | Pg_AC% | Pg_DECA | Pg_P% | pg |
| Mg_DEP | Mg_AC% | Mg_DECA | Mg_P% | mg |

### Medidas Fenotípicas (NUMERIC simples)

| Coluna Origem | Campo Destino |
|---------------|---------------|
| AOL_Medida | fenotipo_aol |
| ACAB_Medida | fenotipo_acab |
| IPP_Fenotipico | fenotipo_ipp |
| STAY_Fenotipico | fenotipo_stay |

### Informações de Descendentes (progeny_info)

| Coluna Filhos | Coluna Rebanhos | Campo Destino |
|---------------|-----------------|----------------|
| P120_Filhos | P120_Rebanhos | p120_info |
| P210_Filhos | P210_Rebanhos | p210_info |
| P365_Filhos | P365_Rebanhos | p365_info |
| P450_Filhos | P450_Rebanhos | p450_info |

## Exemplo de Conversão de DataFrame

```python
import pandas as pd

# Mapeamento de colunas
COLUMN_MAPPING = {
    # Animal
    'Registro': 'rgn',
    'Nome': 'nome',
    'Serie': 'serie',
    'Sexo': 'sexo',
    'Data_Nasc': 'nascimento',
    'Genotipado': 'genotipado',
    'CSG': 'csg',
    'Pai_Reg': 'pai_rgn',
    'Mae_Reg': 'mae_rgn',

    # Geral avaliação
    'IABCZg': 'iabczg',
    'DECA': 'deca_index',

    # Crescimento
    'PN-EDg_DEP': 'pn_ed_dep',
    'PN-EDg_AC%': 'pn_ed_ac',
    'PN-EDg_DECA': 'pn_ed_deca',
    'PN-EDg_P%': 'pn_ed_p_percent',

    # ... continuar para todos os campos
}

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara o DataFrame para importação"""
    # Renomear colunas
    df = df.rename(columns=COLUMN_MAPPING)

    # Converter datas
    df['nascimento'] = pd.to_datetime(df['nascimento'], errors='coerce')

    # Converter sexo para enum
    df['sexo'] = df['sexo'].map({'M': 'M', 'F': 'F', 'Macho': 'M', 'Fêmea': 'F'})

    # Converter boolean_status
    for col in ['genotipado', 'csg']:
        df[col] = df[col].map({
            'Sim': 'SIM',
            'sim': 'SIM',
            'Sim': 'NÃO',
            'Não': 'NÃO',
            'nao': 'NÃO'
        })

    return df
```

## Ordems de Processamento

Para evitar erros de chave estrangeira, seguir esta ordem:

1. **Avós Paternos** - RGNs únicos de `avo_paterno_rgn`, `avo_paterno_mae_rgn`
2. **Avós Maternos** - RGNs únicos de `avo_materno_rgn`, `avo_materno_mae_rgn`
3. **Pais** - RGNs únicos de `pai_rgn`, `mae_rgn`
4. **Animal Principal** - RGNs de `rgn`
5. **Avaliações** - Para cada animal processado