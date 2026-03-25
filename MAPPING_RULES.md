# MAPPING_RULES.md - Melhora+ Genetic Data Platform

## Overview

This document defines the universal column mapping between three genetic data platforms (ANCP, PMGZ, Geneplus) and the unified `silver.animais` master table.

The mapping is **NOT hardcoded** — it is stored in `silver.column_mapping` and loaded dynamically at runtime.

## Unified Target Schema (silver.animais)

| Column | Type | Description |
|--------|------|-------------|
| `id_animal` | SERIAL PK | Auto-increment |
| `id_farm` | INT FK | Multi-tenant: references `silver.fazendas` |
| `rgn_animal` | VARCHAR(50) | Registro Geral Nacional (UNIQUE per farm) |
| `nome_animal` | VARCHAR(255) | Animal name |
| `raca` | VARCHAR(50) | Breed |
| `sexo` | CHAR(1) | M or F |
| `data_nascimento` | DATE | Birth date |
| `mae_rgn` | VARCHAR(50) | Mother's RGN |
| `pai_rgn` | VARCHAR(50) | Father's RGN |
| `p210_peso_desmama` | FLOAT | Weaning weight index |
| `p365_peso_ano` | FLOAT | Year weight index |
| `p450_peso_sobreano` | FLOAT | Over-year weight index |
| `pe_perimetro_escrotal` | FLOAT | Scrotal circumference |
| `a_area_olho_lombo` | FLOAT | Eye of loin area |
| `eg_espessura_gordura` | FLOAT | Fat thickness |
| `im_idade_primeiro_parto` | FLOAT | Age at first calving |
| `fonte_origem` | VARCHAR(50) | Source system |
| `data_processamento` | TIMESTAMP | Processing timestamp |

## Mapping Tables

### ANCP → silver.animais

| ANCP Column | Target Column | Type | Required |
|-------------|---------------|------|----------|
| RGN | rgn_animal | string | YES |
| NOME | nome_animal | string | no |
| SEXO | sexo | string | no |
| DT_NASC | data_nascimento | date | no |
| RACA | raca | string | no |
| MAE_RGN | mae_rgn | string | no |
| PAI_RGN | pai_rgn | string | no |
| PESO_DESM | p210_peso_desmama | float | no |
| PESO_SOBRE | p450_peso_sobreano | float | no |
| P365 | p365_peso_ano | float | no |
| PE | pe_perimetro_escrotal | float | no |
| AOL | a_area_olho_lombo | float | no |
| EGP | eg_espessura_gordura | float | no |
| IPP | im_idade_primeiro_parto | float | no |

### PMGZ → silver.animais

| PMGZ Column | Target Column | Type | Required |
|-------------|---------------|------|----------|
| Registro | rgn_animal | string | YES |
| Nome | nome_animal | string | no |
| Sexo | sexo | string | no |
| Data_Nasc | data_nascimento | date | no |
| Raca | raca | string | no |
| Mae_Reg | mae_rgn | string | no |
| Pai_Reg | pai_rgn | string | no |
| P210 | p210_peso_desmama | float | no |
| P365 | p365_peso_ano | float | no |
| P450 | p450_peso_sobreano | float | no |
| PE | pe_perimetro_escrotal | float | no |
| AOL | a_area_olho_lombo | float | no |
| EGP | eg_espessura_gordura | float | no |

### Geneplus → silver.animais

| Geneplus Column | Target Column | Type | Required |
|-----------------|---------------|------|----------|
| PREFIXO_RGN | rgn_animal | string | YES |
| NOME | nome_animal | string | no |
| SEXO | sexo | string | no |
| DT_NASC | data_nascimento | date | no |
| RACA | raca | string | no |
| MAE_RGN | mae_rgn | string | no |
| PAI_RGN | pai_rgn | string | no |
| P_DESM | p210_peso_desmama | float | no |
| P365 | p365_peso_ano | float | no |
| P_SOBRE | p450_peso_sobreano | float | no |
| PE | pe_perimetro_escrotal | float | no |
| AOL | a_area_olho_lombo | float | no |
| EGP | eg_espessura_gordura | float | no |
| IPP | im_idade_primeiro_parto | float | no |

## Cross-Platform Translation Matrix

| Unified Concept | ANCP | PMGZ | Geneplus |
|-----------------|------|------|----------|
| Animal ID | RGN | Registro | PREFIXO_RGN |
| Name | NOME | Nome | NOME |
| Sex | SEXO | Sexo | SEXO |
| Birth Date | DT_NASC | Data_Nasc | DT_NASC |
| Weaning Weight | PESO_DESM | P210 | P_DESM |
| Year Weight | P365 | P365 | P365 |
| Over-Year Weight | PESO_SOBRE | P450 | P_SOBRE |
| Scrotal Circum. | PE | PE | PE |
| Eye of Loin | AOL | AOL | AOL |
| Fat Thickness | EGP | EGP | EGP |
| Age First Calving | IPP | - | IPP |

## Sex Normalization

| Source Value | Normalized |
|-------------|------------|
| MACHO | M |
| FEMEA / FÊMEA | F |
| 1 | M |
| 2 | F |
| M / F | M / F |

## Deduplication Strategy

When the same RGN appears from multiple sources for the same farm:
- **Strategy**: UPSERT on `(id_farm, rgn_animal)`
- **Last write wins** by `data_processamento`
- `fonte_origem` is updated to the latest source

## How to Add a New Source System

1. Insert new rows into `silver.column_mapping` with the new `source_system` value
2. Mark the RGN-equivalent column as `is_required = true`
3. The processor will automatically pick up the new mappings at runtime
4. No code changes needed in `processor.py`
