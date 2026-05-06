import io
import re
import logging
from typing import Dict

import pandas as pd

from .base_loader import BaseLoader

logger = logging.getLogger(__name__)


MAPEAMENTO_EXCEL_PARA_SNAKE: Dict[str, str] = {
    # 1. Identificação do Animal
    'Nome': 'identificacao_animal_nome',
    'NOME': 'identificacao_animal_nome',
    'ANIMAL NOME': 'identificacao_animal_nome',
    'Série / RGD': 'identificacao_animal_serie_rgd',
    'SERIE / RGD': 'identificacao_animal_serie_rgd',
    'Serie / RGD': 'identificacao_animal_serie_rgd',
    'ANIMAL SERIE / RGD': 'identificacao_animal_serie_rgd',
    'RGN': 'identificacao_animal_rgn',
    'ANIMAL RGN': 'identificacao_animal_rgn',
    'Sexo': 'identificacao_animal_sexo',
    'SEXO': 'identificacao_animal_sexo',
    'ANIMAL SEXO': 'identificacao_animal_sexo',
    'Data Nasc': 'identificacao_animal_nascimento',
    'NASC': 'identificacao_animal_nascimento',
    'Data de Nascimento': 'identificacao_animal_nascimento',
    'ANIMAL NASC': 'identificacao_animal_nascimento',
    'iABCZg': 'identificacao_indice_iabczg',
    'iABCZ g': 'identificacao_indice_iabczg',
    'DECA': 'identificacao_indice_deca',
    'P %': 'identificacao_indice_p_perc',
    'P%': 'identificacao_indice_p_perc',
    'F %': 'identificacao_indice_f_perc',
    'F%': 'identificacao_indice_f_perc',

    # 2. Pedigree (Genealogia) - PAI
    'PAI NOME': 'pedigree_pai_nome',
    'PAI': 'pedigree_pai_nome',
    'Nome do Pai': 'pedigree_pai_nome',
    'PAI SÉRIE / RGD': 'pedigree_pai_serie_rgd',
    'PAI SERIE / RGD': 'pedigree_pai_serie_rgd',
    'PAI SERIE': 'pedigree_pai_serie_rgd',
    'PAI SÉRIE': 'pedigree_pai_serie_rgd',
    'PAI RGN': 'pedigree_pai_rgn',
    'Registro do Pai': 'pedigree_pai_rgn',

    # Pedigree - AVÔ PATERNO
    'AVÔ PATERNO NOME': 'pedigree_avo_paterno_nome',
    'AVO PATERNO NOME': 'pedigree_avo_paterno_nome',
    'AVÔ PATERNO': 'pedigree_avo_paterno_nome',
    'AVO PATERNO': 'pedigree_avo_paterno_nome',
    'Nome do Avô Paterno': 'pedigree_avo_paterno_nome',
    'AVÔ PATERNO SÉRIE / RGD': 'pedigree_avo_paterno_serie_rgd',
    'AVO PATERNO SÉRIE / RGD': 'pedigree_avo_paterno_serie_rgd',
    'AVÔ PATERNO SERIE / RGD': 'pedigree_avo_paterno_serie_rgd',
    'AVO PATERNO SERIE / RGD': 'pedigree_avo_paterno_serie_rgd',
    'AVÔ PATERNO RGN': 'pedigree_avo_paterno_rgn',
    'AVO PATERNO RGN': 'pedigree_avo_paterno_rgn',

    # Pedigree - AVÓ PATERNA
    'AVÓ PATERNA NOME': 'pedigree_avo_paterna_nome',
    'AVO PATERNA NOME': 'pedigree_avo_paterna_nome',
    'AVÓ PATERNA': 'pedigree_avo_paterna_nome',
    'AVO PATERNA': 'pedigree_avo_paterna_nome',
    'Nome da Avó Paterna': 'pedigree_avo_paterna_nome',
    'AVÓ PATERNA SÉRIE / RGD': 'pedigree_avo_paterna_serie_rgd',
    'AVO PATERNA SÉRIE / RGD': 'pedigree_avo_paterna_serie_rgd',
    'AVÓ PATERNA SERIE / RGD': 'pedigree_avo_paterna_serie_rgd',
    'AVO PATERNA SERIE / RGD': 'pedigree_avo_paterna_serie_rgd',
    'AVÓ PATERNA RGN': 'pedigree_avo_paterna_rgn',
    'AVO PATERNA RGN': 'pedigree_avo_paterna_rgn',

    # Pedigree - MÃE
    'MÃE NOME': 'pedigree_mae_nome',
    'MAE NOME': 'pedigree_mae_nome',
    'MÃE': 'pedigree_mae_nome',
    'MAE': 'pedigree_mae_nome',
    'Nome da Mãe': 'pedigree_mae_nome',
    'MÃE SÉRIE / RGD': 'pedigree_mae_serie_rgd',
    'MAE SÉRIE / RGD': 'pedigree_mae_serie_rgd',
    'MÃE SERIE / RGD': 'pedigree_mae_serie_rgd',
    'MAE SERIE / RGD': 'pedigree_mae_serie_rgd',
    'MÃE RGN': 'pedigree_mae_rgn',
    'MAE RGN': 'pedigree_mae_rgn',
    'Registro da Mãe': 'pedigree_mae_rgn',

    # Pedigree - AVÔ MATERNO
    'AVÔ MATERNO NOME': 'pedigree_avo_materno_nome',
    'AVO MATERNO NOME': 'pedigree_avo_materno_nome',
    'AVÔ MATERNO': 'pedigree_avo_materno_nome',
    'AVO MATERNO': 'pedigree_avo_materno_nome',
    'Nome do Avô Materno': 'pedigree_avo_materno_nome',
    'AVÔ MATERNO SÉRIE / RGD': 'pedigree_avo_materno_serie_rgd',
    'AVO MATERNO SÉRIE / RGD': 'pedigree_avo_materno_serie_rgd',
    'AVÔ MATERNO SERIE / RGD': 'pedigree_avo_materno_serie_rgd',
    'AVO MATERNO SERIE / RGD': 'pedigree_avo_materno_serie_rgd',
    'AVÔ MATERNO RGN': 'pedigree_avo_materno_rgn',
    'AVO MATERNO RGN': 'pedigree_avo_materno_rgn',

    # Pedigree - AVÓ MATERNA
    'AVÓ MATERNA NOME': 'pedigree_avo_materna_nome',
    'AVO MATERNA NOME': 'pedigree_avo_materna_nome',
    'AVÓ MATERNA': 'pedigree_avo_materna_nome',
    'AVO MATERNA': 'pedigree_avo_materna_nome',
    'Nome da Avó Materna': 'pedigree_avo_materna_nome',
    'AVÓ MATERNA SÉRIE / RGD': 'pedigree_avo_materna_serie_rgd',
    'AVO MATERNA SÉRIE / RGD': 'pedigree_avo_materna_serie_rgd',
    'AVÓ MATERNA SERIE / RGD': 'pedigree_avo_materna_serie_rgd',
    'AVO MATERNA SERIE / RGD': 'pedigree_avo_materna_serie_rgd',
    'AVÓ MATERNA RGN': 'pedigree_avo_materna_rgn',
    'AVO MATERNA RGN': 'pedigree_avo_materna_rgn',

    # 3. Características Genéticas: Crescimento
    # PN-EDg
    'Peso ao nascimento - efeito direto (PN-EDg) - kg': 'genetica_crescimento_pn_edg_dep',
    'Peso ao nascimento - efeito direto (PN-EDg) - kg DEP': 'genetica_crescimento_pn_edg_dep',
    'PN-EDg DEP': 'genetica_crescimento_pn_edg_dep',
    'PN-EDg': 'genetica_crescimento_pn_edg_dep',
    'Peso ao nascimento - efeito direto (PN-EDg) - kg AC%': 'genetica_crescimento_pn_edg_ac_perc',
    'PN-EDg AC%': 'genetica_crescimento_pn_edg_ac_perc',
    'Peso ao nascimento - efeito direto (PN-EDg) - kg DECA': 'genetica_crescimento_pn_edg_deca',
    'PN-EDg DECA': 'genetica_crescimento_pn_edg_deca',
    'Peso ao nascimento - efeito direto (PN-EDg) - kg P %': 'genetica_crescimento_pn_edg_p_perc',
    'PN-EDg P %': 'genetica_crescimento_pn_edg_p_perc',

    # PD-EDg
    'Peso à desmama - efeito direto (PD-EDg) - kg': 'genetica_crescimento_pd_edg_dep',
    'Peso à desmama - efeito direto (PD-EDg) - kg DEP': 'genetica_crescimento_pd_edg_dep',
    'PD-EDg DEP': 'genetica_crescimento_pd_edg_dep',
    'PD-EDg': 'genetica_crescimento_pd_edg_dep',
    'Peso à desmama - efeito direto (PD-EDg) - kg AC%': 'genetica_crescimento_pd_edg_ac_perc',
    'PD-EDg AC%': 'genetica_crescimento_pd_edg_ac_perc',
    'Peso à desmama - efeito direto (PD-EDg) - kg DECA': 'genetica_crescimento_pd_edg_deca',
    'PD-EDg DECA': 'genetica_crescimento_pd_edg_deca',
    'Peso à desmama - efeito direto (PD-EDg) - kg P %': 'genetica_crescimento_pd_edg_p_perc',
    'PD-EDg P %': 'genetica_crescimento_pd_edg_p_perc',

    # PA-EDg
    'Peso ao ano - efeito direto (PA-EDg)': 'genetica_crescimento_pa_edg_dep',
    'Peso ao ano - efeito direto (PA-EDg) - kg': 'genetica_crescimento_pa_edg_dep',
    'Peso ao ano - efeito direto (PA-EDg) - kg DEP': 'genetica_crescimento_pa_edg_dep',
    'PA-EDg DEP': 'genetica_crescimento_pa_edg_dep',
    'PA-EDg': 'genetica_crescimento_pa_edg_dep',
    'Peso ao ano - efeito direto (PA-EDg) AC%': 'genetica_crescimento_pa_edg_ac_perc',
    'PA-EDg AC%': 'genetica_crescimento_pa_edg_ac_perc',
    'Peso ao ano - efeito direto (PA-EDg) DECA': 'genetica_crescimento_pa_edg_deca',
    'PA-EDg DECA': 'genetica_crescimento_pa_edg_deca',
    'Peso ao ano - efeito direto (PA-EDg) P %': 'genetica_crescimento_pa_edg_p_perc',
    'PA-EDg P %': 'genetica_crescimento_pa_edg_p_perc',

    # PS-EDg
    'Peso ao sobreano - efeito direto (PS-EDg) - kg': 'genetica_crescimento_ps_edg_dep',
    'Peso ao sobreano - efeito direto (PS-EDg) - kg DEP': 'genetica_crescimento_ps_edg_dep',
    'PS-EDg DEP': 'genetica_crescimento_ps_edg_dep',
    'PS-EDg': 'genetica_crescimento_ps_edg_dep',
    'Peso ao sobreano - efeito direto (PS-EDg) - kg AC%': 'genetica_crescimento_ps_edg_ac_perc',
    'PS-EDg AC%': 'genetica_crescimento_ps_edg_ac_perc',
    'Peso ao sobreano - efeito direto (PS-EDg) - kg DECA': 'genetica_crescimento_ps_edg_deca',
    'PS-EDg DECA': 'genetica_crescimento_ps_edg_deca',
    'Peso ao sobreano - efeito direto (PS-EDg) - kg P %': 'genetica_crescimento_ps_edg_p_perc',
    'PS-EDg P %': 'genetica_crescimento_ps_edg_p_perc',

    # PM-EMg
    'Peso à fase materna - efeito materno (PM-EMg) - kg': 'genetica_crescimento_pm_emg_dep',
    'Peso à fase materna - efeito materno (PM-EMg) - kg DEP': 'genetica_crescimento_pm_emg_dep',
    'PM-EMg DEP': 'genetica_crescimento_pm_emg_dep',
    'PM-EMg': 'genetica_crescimento_pm_emg_dep',
    'Peso à fase materna - efeito materno (PM-EMg) - kg AC%': 'genetica_crescimento_pm_emg_ac_perc',
    'PM-EMg AC%': 'genetica_crescimento_pm_emg_ac_perc',
    'Peso à fase materna - efeito materno (PM-EMg) - kg DECA': 'genetica_crescimento_pm_emg_deca',
    'PM-EMg DECA': 'genetica_crescimento_pm_emg_deca',
    'Peso à fase materna - efeito materno (PM-EMg) - kg P %': 'genetica_crescimento_pm_emg_p_perc',
    'PM-EMg P %': 'genetica_crescimento_pm_emg_p_perc',

    # 4. Características Genéticas: Reprodutivas
    # IPPg
    'Idade ao primeiro parto (IPPg) - dias': 'genetica_reprodutiva_ippg_dep',
    'Idade ao primeiro parto (IPPg) - dias DEP': 'genetica_reprodutiva_ippg_dep',
    'IPPg DEP': 'genetica_reprodutiva_ippg_dep',
    'IPPg': 'genetica_reprodutiva_ippg_dep',
    'Idade ao primeiro parto (IPPg) - dias AC%': 'genetica_reprodutiva_ippg_ac_perc',
    'IPPg AC%': 'genetica_reprodutiva_ippg_ac_perc',
    'Idade ao primeiro parto (IPPg) - dias DECA': 'genetica_reprodutiva_ippg_deca',
    'IPPg DECA': 'genetica_reprodutiva_ippg_deca',
    'Idade ao primeiro parto (IPPg) - dias P %': 'genetica_reprodutiva_ippg_p_perc',
    'IPPg P %': 'genetica_reprodutiva_ippg_p_perc',

    # STAYg
    'Stayability (STAYg) - %': 'genetica_reprodutiva_stayg_dep',
    'Stayability (STAYg) - % DEP': 'genetica_reprodutiva_stayg_dep',
    'STAYg DEP': 'genetica_reprodutiva_stayg_dep',
    'STAYg': 'genetica_reprodutiva_stayg_dep',
    'Stayability (STAYg) - % AC%': 'genetica_reprodutiva_stayg_ac_perc',
    'STAYg AC%': 'genetica_reprodutiva_stayg_ac_perc',
    'Stayability (STAYg) - % DECA': 'genetica_reprodutiva_stayg_deca',
    'STAYg DECA': 'genetica_reprodutiva_stayg_deca',
    'Stayability (STAYg) - % P %': 'genetica_reprodutiva_stayg_p_perc',
    'STAYg P %': 'genetica_reprodutiva_stayg_p_perc',

    # PE-365g
    'Perímetro escrotal aos 365 dias (PE-365g) - cm': 'genetica_reprodutiva_pe365g_dep',
    'Perímetro escrotal aos 365 dias (PE-365g) - cm DEP': 'genetica_reprodutiva_pe365g_dep',
    'PE-365g DEP': 'genetica_reprodutiva_pe365g_dep',
    'PE-365g': 'genetica_reprodutiva_pe365g_dep',
    'Perímetro escrotal aos 365 dias (PE-365g) - cm AC%': 'genetica_reprodutiva_pe365g_ac_perc',
    'PE-365g AC%': 'genetica_reprodutiva_pe365g_ac_perc',
    'Perímetro escrotal aos 365 dias (PE-365g) - cm DECA': 'genetica_reprodutiva_pe365g_deca',
    'PE-365g DECA': 'genetica_reprodutiva_pe365g_deca',
    'Perímetro escrotal aos 365 dias (PE-365g) - cm P %': 'genetica_reprodutiva_pe365g_p_perc',
    'PE-365g P %': 'genetica_reprodutiva_pe365g_p_perc',

    # PE-450g
    'Perímetro escrotal aos 450 dias (PE-450g) - cm': 'genetica_reprodutiva_pe450g_dep',
    'Perímetro escrotal aos 450 dias (PE-450g) - cm DEP': 'genetica_reprodutiva_pe450g_dep',
    'PE-450g DEP': 'genetica_reprodutiva_pe450g_dep',
    'PE-450g': 'genetica_reprodutiva_pe450g_dep',
    'Perímetro escrotal aos 450 dias (PE-450g) - cm AC%': 'genetica_reprodutiva_pe450g_ac_perc',
    'PE-450g AC%': 'genetica_reprodutiva_pe450g_ac_perc',
    'Perímetro escrotal aos 450 dias (PE-450g) - cm DECA': 'genetica_reprodutiva_pe450g_deca',
    'PE-450g DECA': 'genetica_reprodutiva_pe450g_deca',
    'Perímetro escrotal aos 450 dias (PE-450g) - cm P %': 'genetica_reprodutiva_pe450g_p_perc',
    'PE-450g P %': 'genetica_reprodutiva_pe450g_p_perc',

    # 5. Características Genéticas: Carcaça
    # AOLg
    'Área de olho de lombo (AOLg) - cm²': 'genetica_carcaca_aolg_dep',
    'Área de olho de lombo (AOLg) - cm2': 'genetica_carcaca_aolg_dep',
    'Área de olho de lombo (AOLg) - cm² DEP': 'genetica_carcaca_aolg_dep',
    'AOLg DEP': 'genetica_carcaca_aolg_dep',
    'AOLg': 'genetica_carcaca_aolg_dep',
    'Área de olho de lombo (AOLg) - cm² AC%': 'genetica_carcaca_aolg_ac_perc',
    'AOLg AC%': 'genetica_carcaca_aolg_ac_perc',
    'Área de olho de lombo (AOLg) - cm² DECA': 'genetica_carcaca_aolg_deca',
    'AOLg DECA': 'genetica_carcaca_aolg_deca',
    'Área de olho de lombo (AOLg) - cm² P %': 'genetica_carcaca_aolg_p_perc',
    'AOLg P %': 'genetica_carcaca_aolg_p_perc',

    # ACABg
    'Acabamento de carcaça (ACABg) - mm': 'genetica_carcaca_acabg_dep',
    'Acabamento de carcaça (ACABg) - mm DEP': 'genetica_carcaca_acabg_dep',
    'ACABg DEP': 'genetica_carcaca_acabg_dep',
    'ACABg': 'genetica_carcaca_acabg_dep',
    'Acabamento de carcaça (ACABg) - mm AC%': 'genetica_carcaca_acabg_ac_perc',
    'ACABg AC%': 'genetica_carcaca_acabg_ac_perc',
    'Acabamento de carcaça (ACABg) - mm DECA': 'genetica_carcaca_acabg_deca',
    'ACABg DECA': 'genetica_carcaca_acabg_deca',
    'Acabamento de carcaça (ACABg) - mm P %': 'genetica_carcaca_acabg_p_perc',
    'ACABg P %': 'genetica_carcaca_acabg_p_perc',

    # MARg
    'Marmoreio (MARg) %': 'genetica_carcaca_marg_dep',
    'Marmoreio (MARg) % DEP': 'genetica_carcaca_marg_dep',
    'MARg DEP': 'genetica_carcaca_marg_dep',
    'MARg': 'genetica_carcaca_marg_dep',
    'Marmoreio (MARg) % AC%': 'genetica_carcaca_marg_ac_perc',
    'MARg AC%': 'genetica_carcaca_marg_ac_perc',
    'Marmoreio (MARg) % DECA': 'genetica_carcaca_marg_deca',
    'MARg DECA': 'genetica_carcaca_marg_deca',
    'Marmoreio (MARg) % P %': 'genetica_carcaca_marg_p_perc',
    'MARg P %': 'genetica_carcaca_marg_p_perc',

    # 6. Características Morfológicas
    # Eg (Estrutura)
    'Estrutura corporal (Eg)': 'genetica_morfologica_eg_dep',
    'Estrutura corporal (Eg) DEP': 'genetica_morfologica_eg_dep',
    'Eg DEP': 'genetica_morfologica_eg_dep',
    'Eg': 'genetica_morfologica_eg_dep',
    'Estrutura corporal (Eg) AC%': 'genetica_morfologica_eg_ac_perc',
    'Eg AC%': 'genetica_morfologica_eg_ac_perc',
    'Estrutura corporal (Eg) DECA': 'genetica_morfologica_eg_deca',
    'Eg DECA': 'genetica_morfologica_eg_deca',
    'Estrutura corporal (Eg) P %': 'genetica_morfologica_eg_p_perc',
    'Eg P %': 'genetica_morfologica_eg_p_perc',

    # Pg (Precocidade)
    'Precocidade (Pg)': 'genetica_morfologica_pg_dep',
    'Precocidade (Pg) DEP': 'genetica_morfologica_pg_dep',
    'Pg DEP': 'genetica_morfologica_pg_dep',
    'Pg': 'genetica_morfologica_pg_dep',
    'Precocidade (Pg) AC%': 'genetica_morfologica_pg_ac_perc',
    'Pg AC%': 'genetica_morfologica_pg_ac_perc',
    'Precocidade (Pg) DECA': 'genetica_morfologica_pg_deca',
    'Pg DECA': 'genetica_morfologica_pg_deca',
    'Precocidade (Pg) P %': 'genetica_morfologica_pg_p_perc',
    'Pg P %': 'genetica_morfologica_pg_p_perc',

    # Mg (Musculosidade)
    'Musculosidade (Mg)': 'genetica_morfologica_mg_dep',
    'Musculosidade (Mg) DEP': 'genetica_morfologica_mg_dep',
    'Mg DEP': 'genetica_morfologica_mg_dep',
    'Mg': 'genetica_morfologica_mg_dep',
    'Musculosidade (Mg) AC%': 'genetica_morfologica_mg_ac_perc',
    'Mg AC%': 'genetica_morfologica_mg_ac_perc',
    'Musculosidade (Mg) DECA': 'genetica_morfologica_mg_deca',
    'Mg DECA': 'genetica_morfologica_mg_deca',
    'Musculosidade (Mg) P %': 'genetica_morfologica_mg_p_perc',
    'Mg P %': 'genetica_morfologica_mg_p_perc',

    # 6. Informações de Descendentes e Extras
    'FILHOS': 'descendentes_filhos_quantidade',
    'Filhos': 'descendentes_filhos_quantidade',
    'REBANHOS': 'descendentes_rebanhos_quantidade',
    'Rebanhos': 'descendentes_rebanhos_quantidade',
    'NETOS': 'descendentes_netos_quantidade',
    'Netos': 'descendentes_netos_quantidade',
    'GENOTIPADO': 'extra_genotipado',
    'Genotipado': 'extra_genotipado',
    'CSG': 'extra_csg',

    # 7. Fenótipos e Medidas Reais
    'IPP': 'fenotipo_ipp_dias',
    'IPP (dias)': 'fenotipo_ipp_dias',
    'AOL': 'medida_aol_cm2',
    'AOL (cm2)': 'medida_aol_cm2',
    'Área de Olho de Lombo': 'medida_aol_cm2',
    'ACAB': 'medida_acabamento_mm',
    'Acabamento': 'medida_acabamento_mm',
    'Espessura de Gordura': 'medida_acabamento_mm',
    'P120': 'peso_p120_kg',
    'Peso aos 120 dias': 'peso_p120_kg',
    'P210': 'peso_p210_kg',
    'Peso aos 210 dias': 'peso_p210_kg',
    'P365': 'peso_p365_kg',
    'Peso aos 365 dias': 'peso_p365_kg',
    'P450': 'peso_p450_kg',
    'Peso aos 450 dias': 'peso_p450_kg',
    'PE365': 'medida_pe365_cm',
    'Perímetro Escrotal 365': 'medida_pe365_cm',
}


COLUNAS_FLOAT = [
    'identificacao_indice_iabczg', 'identificacao_indice_p_perc', 'identificacao_indice_f_perc',
    'genetica_crescimento_pn_edg_dep', 'genetica_crescimento_pn_edg_ac_perc', 'genetica_crescimento_pn_edg_p_perc',
    'genetica_crescimento_pd_edg_dep', 'genetica_crescimento_pd_edg_ac_perc', 'genetica_crescimento_pd_edg_p_perc',
    'genetica_crescimento_pa_edg_dep', 'genetica_crescimento_pa_edg_ac_perc', 'genetica_crescimento_pa_edg_p_perc',
    'genetica_crescimento_ps_edg_dep', 'genetica_crescimento_ps_edg_ac_perc', 'genetica_crescimento_ps_edg_p_perc',
    'genetica_crescimento_pm_emg_dep', 'genetica_crescimento_pm_emg_ac_perc', 'genetica_crescimento_pm_emg_p_perc',
    'genetica_reprodutiva_ippg_dep', 'genetica_reprodutiva_ippg_ac_perc', 'genetica_reprodutiva_ippg_p_perc',
    'genetica_reprodutiva_stayg_dep', 'genetica_reprodutiva_stayg_ac_perc', 'genetica_reprodutiva_stayg_p_perc',
    'genetica_reprodutiva_pe365g_dep', 'genetica_reprodutiva_pe365g_ac_perc', 'genetica_reprodutiva_pe365g_p_perc',
    'genetica_reprodutiva_pe450g_dep', 'genetica_reprodutiva_pe450g_ac_perc', 'genetica_reprodutiva_pe450g_p_perc',
    'genetica_carcaca_aolg_dep', 'genetica_carcaca_aolg_ac_perc', 'genetica_carcaca_aolg_p_perc',
    'genetica_carcaca_acabg_dep', 'genetica_carcaca_acabg_ac_perc', 'genetica_carcaca_acabg_p_perc',
    'genetica_carcaca_marg_dep', 'genetica_carcaca_marg_ac_perc', 'genetica_carcaca_marg_p_perc',
    'genetica_morfologica_eg_dep', 'genetica_morfologica_eg_ac_perc', 'genetica_morfologica_eg_p_perc',
    'genetica_morfologica_pg_dep', 'genetica_morfologica_pg_ac_perc', 'genetica_morfologica_pg_p_perc',
    'genetica_morfologica_mg_dep', 'genetica_morfologica_mg_ac_perc', 'genetica_morfologica_mg_p_perc',
    'medida_aol_cm2', 'medida_acabamento_mm',
    'peso_p120_kg', 'peso_p210_kg', 'peso_p365_kg', 'peso_p450_kg', 'medida_pe365_cm',
]

COLUNAS_INTEGER = [
    'identificacao_indice_deca',
    'genetica_crescimento_pn_edg_deca', 'genetica_crescimento_pd_edg_deca',
    'genetica_crescimento_pa_edg_deca', 'genetica_crescimento_ps_edg_deca', 'genetica_crescimento_pm_emg_deca',
    'genetica_reprodutiva_ippg_deca', 'genetica_reprodutiva_stayg_deca',
    'genetica_reprodutiva_pe365g_deca', 'genetica_reprodutiva_pe450g_deca',
    'genetica_carcaca_aolg_deca', 'genetica_carcaca_acabg_deca', 'genetica_carcaca_marg_deca',
    'genetica_morfologica_eg_deca', 'genetica_morfologica_pg_deca', 'genetica_morfologica_mg_deca',
    'descendentes_filhos_quantidade', 'descendentes_rebanhos_quantidade', 'descendentes_netos_quantidade',
    'fenotipo_ipp_dias',
]

COLUNAS_BOOLEAN = ['extra_genotipado', 'extra_csg']


class PMGZLoader(BaseLoader):
    """Loader para dados PMGZ com mapeamento de colunas Excel -> snake_case."""

    def __init__(self, farm_id: int = 1):
        super().__init__(farm_id)

    def load(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Executa o pipeline completo de carregamento PMGZ."""
        df = self._ler_arquivo(file_content, filename)
        df = self._normalizar_cabecalhos(df)
        df = self._renomear_colunas(df)
        df = self._tratar_dados(df)
        df['id_farm'] = self.farm_id
        df['fonte_origem'] = 'PMGZ'
        return df

    def _ler_arquivo(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Lê o arquivo Excel ou CSV detectando o formato."""
        if filename.endswith(('.xlsx', '.xls')):
            return self._ler_excel_com_headers(file_content)
        elif filename.endswith('.csv'):
            return self._ler_csv(file_content)
        else:
            raise ValueError(f'Formato não suportado: {filename}')

    def _ler_excel_com_headers(self, file_content: bytes) -> pd.DataFrame:
        """Lê Excel com headers multi-linha (células mescladas)."""
        raw = pd.read_excel(io.BytesIO(file_content), header=None, nrows=20)

        keywords = {
            'RGN', 'NOME', 'SEXO', 'NASC', 'SERIE', 'DECA', 'iABCZg', 'DEP',
            'ANIMAL', 'PAI', 'MÃE', 'MAE', 'PESO', 'IPP', 'STAY', 'PE-365', 'AOL', 'ACAB', 'MAR',
            'Estrutura', 'Precocidade', 'Musculosidade', 'GENOTIPADO', 'CSG', 'FILHOS', 'NETOS'
        }

        best_row, best_score = 0, 0
        for i, row in raw.iterrows():
            score = sum(1 for val in row.values if str(val).strip().upper() in keywords)
            if score > best_score:
                best_score, best_row = score, i

        if best_score < 2:
            raise ValueError(f'Não foi possível localizar header no arquivo PMGZ. Score: {best_score}')

        group_row = best_row - 1
        subcol_row = best_row

        group_names_raw = raw.loc[group_row].values
        subcol_names_raw = raw.loc[subcol_row].values

        group_names_filled = pd.Series(group_names_raw).ffill().values
        subcol_names = [str(s).strip() if pd.notna(s) else 'Unknown' for s in subcol_names_raw]

        composite_names = []
        for g, s in zip(group_names_filled, subcol_names):
            g_str = str(g).strip() if pd.notna(g) else ''
            if g_str and g_str != 'nan':
                composite_names.append(f'{g_str} {s}')
            else:
                composite_names.append(s)

        df = pd.read_excel(io.BytesIO(file_content), header=None, skiprows=best_row + 1)
        df.columns = composite_names

        logger.info(f'Excel PMGZ lido: {len(df)} linhas, {len(df.columns)} colunas')
        return df

    def _ler_csv(self, file_content: bytes) -> pd.DataFrame:
        """Lê arquivo CSV detectando separador."""
        sep = self._detectar_separador(file_content)
        df = pd.read_csv(io.BytesIO(file_content), sep=sep, encoding='utf-8-sig')
        df.columns = [str(c).strip() for c in df.columns]
        logger.info(f'CSV PMGZ lido: {len(df)} linhas, {len(df.columns)} colunas')
        return df

    def _normalizar_cabecalhos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza nomes de colunas: strip, title case."""
        df.columns = [str(c).strip() for c in df.columns]
        return df

    def _renomear_colunas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica mapeamento Excel -> snake_case."""
        rename_map = {}
        for col in df.columns:
            col_normalizado = str(col).strip()
            if col_normalizado in MAPEAMENTO_EXCEL_PARA_SNAKE:
                rename_map[col] = MAPEAMENTO_EXCEL_PARA_SNAKE[col_normalizado]
            else:
                for excel_col, snake_col in MAPEAMENTO_EXCEL_PARA_SNAKE.items():
                    if excel_col.lower() in col_normalizado.lower() or col_normalizado.lower() in excel_col.lower():
                        if col not in rename_map:
                            rename_map[col] = snake_col
                        break

        df = df.rename(columns=rename_map)
        df = df.dropna(how='all')
        logger.info(f'Colunas renomeadas: {len(rename_map)} mapeamentos')
        return df

    def _tratar_dados(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converte tipos, trata vírgulas, booleanos e limpa dados."""
        seen = set()
        unique_cols = []
        for col in df.columns:
            if col not in seen:
                seen.add(col)
                unique_cols.append(col)
        df = df[unique_cols]

        for col in df.columns:
            try:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].str.replace(',', '.', regex=False)
                df[col] = df[col].replace(['-', '', 'nan', 'None', 'NaN', 'nat'], None)
            except Exception as e:
                logger.warning(f"Erro ao tratar coluna {col}: {e}")
                continue

        df = self._aplicar_tipos_numericos(df, COLUNAS_FLOAT)
        df = self._aplicar_tipos_inteiros(df, COLUNAS_INTEGER)
        df = self._converter_booleanos(df, COLUNAS_BOOLEAN)

        if 'identificacao_animal_nascimento' in df.columns:
            df['identificacao_animal_nascimento'] = df['identificacao_animal_nascimento'].apply(self._converter_data)

        if 'identificacao_animal_sexo' in df.columns:
            df['identificacao_animal_sexo'] = df['identificacao_animal_sexo'].apply(
                lambda x: 'M' if str(x).upper().strip() in ['MACHO', 'M', '1']
                else ('F' if str(x).upper().strip() in ['FEMEA', 'FÊMEA', 'F', '2']
                else None)
            )

        return df

    def para_colunas_banco(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converte colunas do formato novo para colunas existentes na tabela animais."""
        mapa = {
            # Identificação
            'identificacao_animal_nome': 'nome_animal',
            'identificacao_animal_rgn': 'rgn_animal',
            'identificacao_animal_serie_rgd': 'pmg_serie_rgd',
            'identificacao_animal_sexo': 'sexo',
            'identificacao_animal_nascimento': 'data_nascimento',
            'identificacao_indice_iabczg': 'pmg_iabc',
            'identificacao_indice_deca': 'pmg_deca',
            'identificacao_indice_p_perc': 'pmg_p_percent',
            'identificacao_indice_f_perc': 'pmg_f_percent',
            # Genealogia
            'pedigree_pai_nome': 'pai_nome',
            'pedigree_pai_serie_rgd': 'pai_serie_rgd',
            'pedigree_pai_rgn': 'pai_rgn',
            'pedigree_mae_nome': 'mae_nome',
            'pedigree_mae_serie_rgd': 'mae_serie_rgd',
            'pedigree_mae_rgn': 'mae_rgn',
            # Crescimento
            'genetica_crescimento_pn_edg_dep': 'pmg_pn_dep',
            'genetica_crescimento_pn_edg_ac_perc': 'pmg_pn_ac',
            'genetica_crescimento_pn_edg_deca': 'pmg_pn_deca',
            'genetica_crescimento_pn_edg_p_perc': 'pmg_pn_p_percent',
            'genetica_crescimento_pd_edg_dep': 'pmg_pd_dep',
            'genetica_crescimento_pd_edg_ac_perc': 'pmg_pd_ac',
            'genetica_crescimento_pd_edg_deca': 'pmg_pd_deca',
            'genetica_crescimento_pd_edg_p_perc': 'pmg_pd_p_percent',
            'genetica_crescimento_pa_edg_dep': 'pmg_pa_dep',
            'genetica_crescimento_pa_edg_ac_perc': 'pmg_pa_ac',
            'genetica_crescimento_pa_edg_deca': 'pmg_pa_deca',
            'genetica_crescimento_pa_edg_p_perc': 'pmg_pa_p_percent',
            'genetica_crescimento_ps_edg_dep': 'pmg_ps_dep',
            'genetica_crescimento_ps_edg_ac_perc': 'pmg_ps_ac',
            'genetica_crescimento_ps_edg_deca': 'pmg_ps_deca',
            'genetica_crescimento_ps_edg_p_perc': 'pmg_ps_p_percent',
            'genetica_crescimento_pm_emg_dep': 'pmg_pm_dep',
            'genetica_crescimento_pm_emg_ac_perc': 'pmg_pm_ac',
            'genetica_crescimento_pm_emg_deca': 'pmg_pm_deca',
            'genetica_crescimento_pm_emg_p_perc': 'pmg_pm_p_percent',
            # Reprodutivas
            'genetica_reprodutiva_ippg_dep': 'pmg_ipp_dep',
            'genetica_reprodutiva_ippg_ac_perc': 'pmg_ipp_ac',
            'genetica_reprodutiva_ippg_deca': 'pmg_ipp_deca',
            'genetica_reprodutiva_ippg_p_perc': 'pmg_ipp_p_percent',
            'genetica_reprodutiva_stayg_dep': 'pmg_stay_dep',
            'genetica_reprodutiva_stayg_ac_perc': 'pmg_stay_ac',
            'genetica_reprodutiva_stayg_deca': 'pmg_stay_deca',
            'genetica_reprodutiva_stayg_p_perc': 'pmg_stay_p_percent',
            'genetica_reprodutiva_pe365g_dep': 'pmg_pe365_dep',
            'genetica_reprodutiva_pe365g_ac_perc': 'pmg_pe365_ac',
            'genetica_reprodutiva_pe365g_deca': 'pmg_pe365_deca',
            'genetica_reprodutiva_pe365g_p_perc': 'pmg_pe365_p_percent',
            # Carcaça
            'genetica_carcaca_aolg_dep': 'pmg_aol_dep',
            'genetica_carcaca_aolg_ac_perc': 'pmg_aol_ac',
            'genetica_carcaca_aolg_deca': 'pmg_aol_deca',
            'genetica_carcaca_aolg_p_perc': 'pmg_aol_p_percent',
            'genetica_carcaca_acabg_dep': 'pmg_acab_dep',
            'genetica_carcaca_acabg_ac_perc': 'pmg_acab_ac',
            'genetica_carcaca_acabg_deca': 'pmg_acab_deca',
            'genetica_carcaca_acabg_p_perc': 'pmg_acab_p_percent',
            'genetica_carcaca_marg_dep': 'pmg_mar_dep',
            'genetica_carcaca_marg_ac_perc': 'pmg_mar_ac',
            'genetica_carcaca_marg_deca': 'pmg_mar_deca',
            'genetica_carcaca_marg_p_perc': 'pmg_mar_p_percent',
            # Morfológicas
            'genetica_morfologica_eg_dep': 'pmg_eg_dep',
            'genetica_morfologica_eg_ac_perc': 'pmg_eg_ac',
            'genetica_morfologica_eg_deca': 'pmg_eg_deca',
            'genetica_morfologica_eg_p_perc': 'pmg_eg_p_percent',
            'genetica_morfologica_pg_dep': 'pmg_p_dep',
            'genetica_morfologica_pg_ac_perc': 'pmg_p_ac',
            'genetica_morfologica_pg_deca': 'pmg_p_deca',
            'genetica_morfologica_pg_p_perc': 'pmg_p_p_percent',
            'genetica_morfologica_mg_dep': 'pmg_m_dep',
            'genetica_morfologica_mg_ac_perc': 'pmg_m_ac',
            'genetica_morfologica_mg_deca': 'pmg_m_deca',
            'genetica_morfologica_mg_p_perc': 'pmg_m_p_percent',
            # Extras
            'extra_genotipado': 'genotipado',
            'extra_csg': 'csg',
            # Fenótipos
            'medida_aol_cm2': 'a_area_olho_lombo',
            'medida_acabamento_mm': 'eg_espessura_gordura',
            'peso_p210_kg': 'p210_peso_desmama',
            'peso_p365_kg': 'p365_peso_ano',
            'peso_p450_kg': 'p450_peso_sobreano',
            'medida_pe365_cm': 'pe_perimetro_escrotal',
            'fenotipo_ipp_dias': 'im_idade_primeiro_parto',
        }

        rename = {col: novo for col, novo in mapa.items() if col in df.columns}
        df = df.rename(columns=rename)
        return df