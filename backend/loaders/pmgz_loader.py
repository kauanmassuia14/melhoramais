import io
import re
import logging
from typing import Dict

import pandas as pd

from .base_loader import BaseLoader

logger = logging.getLogger(__name__)

DE_PARA_PMGZ_COMPLETO = {
    "_ANIMAL_NOME": "identificacao_animal_nome",
    "_ANIMAL_SERIE / RGD": "identificacao_animal_serie_rgd",
    "_ANIMAL_RGN": "identificacao_animal_rgn",
    "_ANIMAL_SEXO": "identificacao_animal_sexo",
    "_ANIMAL_NASC": "identificacao_animal_nascimento",
    "_ANIMAL_iABCZg": "identificacao_indice_iabczg",
    "_ANIMAL_DECA": "identificacao_indice_deca",
    "_ANIMAL_P %": "identificacao_indice_p_perc",
    "_ANIMAL_F %": "identificacao_indice_f_perc",
    "_PAI_NOME": "pedigree_pai_nome",
    "_PAI_SERIE / RGD": "pedigree_pai_serie_rgd",
    "_PAI_RGN": "pedigree_pai_rgn",
    "_AVÔ PATERNO_NOME": "pedigree_avo_paterno_nome",
    "_AVÔ PATERNO_SERIE / RGD": "pedigree_avo_paterno_serie_rgd",
    "_AVÔ PATERNO_RGN": "pedigree_avo_paterno_rgn",
    "_AVÓ PATERNA_NOME": "pedigree_avo_paterna_nome",
    "_AVÓ PATERNA_SERIE / RGD": "pedigree_avo_paterna_serie_rgd",
    "_AVÓ PATERNA_RGN": "pedigree_avo_paterna_rgn",
    "_MÃE_NOME": "pedigree_mae_nome",
    "_MÃE_SERIE / RGD": "pedigree_mae_serie_rgd",
    "_MÃE_RGN": "pedigree_mae_rgn",
    "_AVÔ MATERNO_NOME": "pedigree_avo_materno_nome",
    "_AVÔ MATERNO_SERIE / RGD": "pedigree_avo_materno_serie_rgd",
    "_AVÔ MATERNO_RGN": "pedigree_avo_materno_rgn",
    "_AVÓ MATERNA_NOME": "pedigree_avo_materna_nome",
    "_AVÓ MATERNA_SERIE / RGD": "pedigree_avo_materna_serie_rgd",
    "_AVÓ MATERNA_RGN": "pedigree_avo_materna_rgn",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso ao nascimento - efeito direto (PN-EDg) - kg_DEP": "genetica_crescimento_pn_edg_dep",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso ao nascimento - efeito direto (PN-EDg) - kg_AC %": "genetica_crescimento_pn_edg_ac_perc",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso ao nascimento - efeito direto (PN-EDg) - kg_DECA": "genetica_crescimento_pn_edg_deca",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso ao nascimento - efeito direto (PN-EDg) - kg_P %": "genetica_crescimento_pn_edg_p_perc",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso à desmama - efeito direto (PD-EDg) - kg_DEP": "genetica_crescimento_pd_edg_dep",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso à desmama - efeito direto (PD-EDg) - kg_AC %": "genetica_crescimento_pd_edg_ac_perc",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso à desmama - efeito direto (PD-EDg) - kg_DECA": "genetica_crescimento_pd_edg_deca",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso à desmama - efeito direto (PD-EDg) - kg_P %": "genetica_crescimento_pd_edg_p_perc",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso ao ano - efeito direto (PA-EDg)_DEP": "genetica_crescimento_pa_edg_dep",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso ao ano - efeito direto (PA-EDg)_AC %": "genetica_crescimento_pa_edg_ac_perc",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso ao ano - efeito direto (PA-EDg)_DECA": "genetica_crescimento_pa_edg_deca",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso ao ano - efeito direto (PA-EDg)_P %": "genetica_crescimento_pa_edg_p_perc",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso ao sobreano - efeito direto (PS-EDg) - kg_DEP": "genetica_crescimento_ps_edg_dep",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso ao sobreano - efeito direto (PS-EDg) - kg_AC %": "genetica_crescimento_ps_edg_ac_perc",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso ao sobreano - efeito direto (PS-EDg) - kg_DECA": "genetica_crescimento_ps_edg_deca",
    "CARACTERÍSTICAS DE CRESCIMENTO_Peso ao sobreano - efeito direto (PS-EDg) - kg_P %": "genetica_crescimento_ps_edg_p_perc",
    "CARACTERÍSTICAS MATERNAS_Peso à fase materna - efeito materno (PM-EMg) - kg_DEP": "genetica_materna_pm_emg_dep",
    "CARACTERÍSTICAS MATERNAS_Peso à fase materna - efeito materno (PM-EMg) - kg_AC %": "genetica_materna_pm_emg_ac_perc",
    "CARACTERÍSTICAS MATERNAS_Peso à fase materna - efeito materno (PM-EMg) - kg_DECA": "genetica_materna_pm_emg_deca",
    "CARACTERÍSTICAS MATERNAS_Peso à fase materna - efeito materno (PM-EMg) - kg_P %": "genetica_materna_pm_emg_p_perc",
    "CARACTERÍSTICAS REPRODUTIVAS_Idade ao primeiro parto (IPPg) - dias_DEP": "genetica_reprodutiva_ippg_dep",
    "CARACTERÍSTICAS REPRODUTIVAS_Idade ao primeiro parto (IPPg) - dias_AC %": "genetica_reprodutiva_ippg_ac_perc",
    "CARACTERÍSTICAS REPRODUTIVAS_Idade ao primeiro parto (IPPg) - dias_DECA": "genetica_reprodutiva_ippg_deca",
    "CARACTERÍSTICAS REPRODUTIVAS_Idade ao primeiro parto (IPPg) - dias_P %": "genetica_reprodutiva_ippg_p_perc",
    "CARACTERÍSTICAS REPRODUTIVAS_Stayability (STAYg) - %_DEP": "genetica_reprodutiva_stayg_dep",
    "CARACTERÍSTICAS REPRODUTIVAS_Stayability (STAYg) - %_AC %": "genetica_reprodutiva_stayg_ac_perc",
    "CARACTERÍSTICAS REPRODUTIVAS_Stayability (STAYg) - %_DECA": "genetica_reprodutiva_stayg_deca",
    "CARACTERÍSTICAS REPRODUTIVAS_Stayability (STAYg) - %_P %": "genetica_reprodutiva_stayg_p_perc",
    "CARACTERÍSTICAS REPRODUTIVAS_Perímetro escrotal aos 365 dias (PE-365g) - cm_DEP": "genetica_reprodutiva_pe365g_dep",
    "CARACTERÍSTICAS REPRODUTIVAS_Perímetro escrotal aos 365 dias (PE-365g) - cm_AC %": "genetica_reprodutiva_pe365g_ac_perc",
    "CARACTERÍSTICAS REPRODUTIVAS_Perímetro escrotal aos 365 dias (PE-365g) - cm_DECA": "genetica_reprodutiva_pe365g_deca",
    "CARACTERÍSTICAS REPRODUTIVAS_Perímetro escrotal aos 365 dias (PE-365g) - cm_P %": "genetica_reprodutiva_pe365g_p_perc",
    "CARACTERÍSTICAS REPRODUTIVAS_Precocidade Sexual Natural ( PSNg ) %_DEP": "genetica_reprodutiva_psng_dep",
    "CARACTERÍSTICAS REPRODUTIVAS_Precocidade Sexual Natural ( PSNg ) %_AC %": "genetica_reprodutiva_psng_ac_perc",
    "CARACTERÍSTICAS REPRODUTIVAS_Precocidade Sexual Natural ( PSNg ) %_DECA": "genetica_reprodutiva_psng_deca",
    "CARACTERÍSTICAS REPRODUTIVAS_Precocidade Sexual Natural ( PSNg ) %_P %": "genetica_reprodutiva_psng_p_perc",
    "CARACTERÍSTICAS DE CARCAÇA_Área de olho de lombo (AOLg) - cm²_DEP": "genetica_carcaca_aolg_dep",
    "CARACTERÍSTICAS DE CARCAÇA_Área de olho de lombo (AOLg) - cm²_AC %": "genetica_carcaca_aolg_ac_perc",
    "CARACTERÍSTICAS DE CARCAÇA_Área de olho de lombo (AOLg) - cm²_DECA": "genetica_carcaca_aolg_deca",
    "CARACTERÍSTICAS DE CARCAÇA_Área de olho de lombo (AOLg) - cm²_P %": "genetica_carcaca_aolg_p_perc",
    "CARACTERÍSTICAS DE CARCAÇA_Acabamento de carcaça (ACABg) - mm_DEP": "genetica_carcaca_acabg_dep",
    "CARACTERÍSTICAS DE CARCAÇA_Acabamento de carcaça (ACABg) - mm_AC %": "genetica_carcaca_acabg_ac_perc",
    "CARACTERÍSTICAS DE CARCAÇA_Acabamento de carcaça (ACABg) - mm_DECA": "genetica_carcaca_acabg_deca",
    "CARACTERÍSTICAS DE CARCAÇA_Acabamento de carcaça (ACABg) - mm_P %": "genetica_carcaca_acabg_p_perc",
    "CARACTERÍSTICAS DE CARCAÇA_Marmoreio (MARg) %_DEP": "genetica_carcaca_marg_dep",
    "CARACTERÍSTICAS DE CARCAÇA_Marmoreio (MARg) %_AC %": "genetica_carcaca_marg_ac_perc",
    "CARACTERÍSTICAS DE CARCAÇA_Marmoreio (MARg) %_DECA": "genetica_carcaca_marg_deca",
    "CARACTERÍSTICAS DE CARCAÇA_Marmoreio (MARg) %_P %": "genetica_carcaca_marg_p_perc",
    "CARACTERÍSTICAS MORFOLÓGICAS_Estrutura corporal (Eg)_DEP": "genetica_morfologica_eg_dep",
    "CARACTERÍSTICAS MORFOLÓGICAS_Estrutura corporal (Eg)_AC %": "genetica_morfologica_eg_ac_perc",
    "CARACTERÍSTICAS MORFOLÓGICAS_Estrutura corporal (Eg)_DECA": "genetica_morfologica_eg_deca",
    "CARACTERÍSTICAS MORFOLÓGICAS_Estrutura corporal (Eg)_P %": "genetica_morfologica_eg_p_perc",
    "CARACTERÍSTICAS MORFOLÓGICAS_Precocidade (Pg)_DEP": "genetica_morfologica_pg_dep",
    "CARACTERÍSTICAS MORFOLÓGICAS_Precocidade (Pg)_AC %": "genetica_morfologica_pg_ac_perc",
    "CARACTERÍSTICAS MORFOLÓGICAS_Precocidade (Pg)_DECA": "genetica_morfologica_pg_deca",
    "CARACTERÍSTICAS MORFOLÓGICAS_Precocidade (Pg)_P %": "genetica_morfologica_pg_p_perc",
    "CARACTERÍSTICAS MORFOLÓGICAS_Musculosidade (Mg)_DEP": "genetica_morfologica_mg_dep",
    "CARACTERÍSTICAS MORFOLÓGICAS_Musculosidade (Mg)_AC %": "genetica_morfologica_mg_ac_perc",
    "CARACTERÍSTICAS MORFOLÓGICAS_Musculosidade (Mg)_DECA": "genetica_morfologica_mg_deca",
    "CARACTERÍSTICAS MORFOLÓGICAS_Musculosidade (Mg)_P %": "genetica_morfologica_mg_p_perc",
    "INFORMAÇÕES DE DESCENDENTES_Peso aos 120 dias (P120)_FILHOS": "descendentes_p120_filhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Peso aos 120 dias (P120)_REBANHOS": "descendentes_p120_rebanhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Peso aos 210 dias (P210)_FILHOS": "descendentes_p210_filhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Peso aos 210 dias (P210)_REBANHOS": "descendentes_p210_rebanhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Peso aos 365 dias (P365)_FILHOS": "descendentes_p365_filhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Peso aos 365 dias (P365)_REBANHOS": "descendentes_p365_rebanhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Peso aos 450 dias (P450)_FILHOS": "descendentes_p450_filhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Peso aos 450 dias (P450)_REBANHOS": "descendentes_p450_rebanhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Peso aos 120 dias (P120).1_NETOS": "descendentes_p120_materno_netos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Peso aos 120 dias (P120).1_REBANHOS": "descendentes_p120_materno_rebanhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Peso aos 210 dias (P210).1_NETOS": "descendentes_p210_materno_netos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Peso aos 210 dias (P210).1_REBANHOS": "descendentes_p210_materno_rebanhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Perímetro Escrotal aos 365 dias (PE365)_FILHOS": "descendentes_pe365_filhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Perímetro Escrotal aos 365 dias (PE365)_REBANHOS": "descendentes_pe365_rebanhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Fenótipo Stayability (STAY)_FILHOS": "descendentes_stay_filhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Fenótipo Stayability (STAY)_REBANHOS": "descendentes_stay_rebanhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Fenótipo Idade ao Primeiro Parto (IPP)_FILHOS": "descendentes_ipp_filhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Fenótipo Idade ao Primeiro Parto (IPP)_REBANHOS": "descendentes_ipp_rebanhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Medida Área Olho de Lombo (AOL)_FILHOS": "descendentes_aol_filhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Medida Área Olho de Lombo (AOL)_REBANHOS": "descendentes_aol_rebanhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Medida Acabamento De Carcaça (ACAB)_FILHOS": "descendentes_acab_filhos_qtd",
    "INFORMAÇÕES DE DESCENDENTES_Medida Acabamento De Carcaça (ACAB)_REBANHOS": "descendentes_acab_rebanhos_qtd",
    "INFORMAÇÕES EXTRAS_GENOTIPADO": "extra_genotipado",
    "INFORMAÇÕES EXTRAS_GENOTIPADO_": "extra_genotipado",
    "INFORMAÇÕES EXTRAS_GENOTIPAD": "extra_genotipado",
    "INFORMAÇÕES EXTRAS_GENOTIPAD_": "extra_genotipado",
    "INFORMAÇÕES EXTRAS_CSG": "extra_csg",
    "INFORMAÇÕES EXTRAS_CSG_": "extra_csg",
}


COLUNAS_FLOAT = [
    'identificacao_indice_iabczg', 'identificacao_indice_p_perc', 'identificacao_indice_f_perc',
    'genetica_crescimento_pn_edg_dep', 'genetica_crescimento_pn_edg_ac_perc', 'genetica_crescimento_pn_edg_p_perc',
    'genetica_crescimento_pd_edg_dep', 'genetica_crescimento_pd_edg_ac_perc', 'genetica_crescimento_pd_edg_p_perc',
    'genetica_crescimento_pa_edg_dep', 'genetica_crescimento_pa_edg_ac_perc', 'genetica_crescimento_pa_edg_p_perc',
    'genetica_crescimento_ps_edg_dep', 'genetica_crescimento_ps_edg_ac_perc', 'genetica_crescimento_ps_edg_p_perc',
    'genetica_materna_pm_emg_dep', 'genetica_materna_pm_emg_ac_perc', 'genetica_materna_pm_emg_p_perc',
    'genetica_reprodutiva_ippg_dep', 'genetica_reprodutiva_ippg_ac_perc', 'genetica_reprodutiva_ippg_p_perc',
    'genetica_reprodutiva_stayg_dep', 'genetica_reprodutiva_stayg_ac_perc', 'genetica_reprodutiva_stayg_p_perc',
    'genetica_reprodutiva_pe365g_dep', 'genetica_reprodutiva_pe365g_ac_perc', 'genetica_reprodutiva_pe365g_p_perc',
    'genetica_reprodutiva_psng_dep', 'genetica_reprodutiva_psng_ac_perc', 'genetica_reprodutiva_psng_p_perc',
    'genetica_carcaca_aolg_dep', 'genetica_carcaca_aolg_ac_perc', 'genetica_carcaca_aolg_p_perc',
    'genetica_carcaca_acabg_dep', 'genetica_carcaca_acabg_ac_perc', 'genetica_carcaca_acabg_p_perc',
    'genetica_carcaca_marg_dep', 'genetica_carcaca_marg_ac_perc', 'genetica_carcaca_marg_p_perc',
    'genetica_morfologica_eg_dep', 'genetica_morfologica_eg_ac_perc', 'genetica_morfologica_eg_p_perc',
    'genetica_morfologica_pg_dep', 'genetica_morfologica_pg_ac_perc', 'genetica_morfologica_pg_p_perc',
    'genetica_morfologica_mg_dep', 'genetica_morfologica_mg_ac_perc', 'genetica_morfologica_mg_p_perc',
    'medida_aol_cm2', 'medida_acabamento_mm',
    'peso_p120_kg', 'peso_p210_kg', 'peso_p365_kg', 'peso_p450_kg', 'medida_pe365_cm',
    'descendentes_p120_filhos_qtd', 'descendentes_p120_rebanhos_qtd',
    'descendentes_p210_filhos_qtd', 'descendentes_p210_rebanhos_qtd',
    'descendentes_p365_filhos_qtd', 'descendentes_p365_rebanhos_qtd',
    'descendentes_p450_filhos_qtd', 'descendentes_p450_rebanhos_qtd',
]

COLUNAS_INTEGER = [
    'identificacao_indice_deca',
    'genetica_crescimento_pn_edg_deca', 'genetica_crescimento_pd_edg_deca',
    'genetica_crescimento_pa_edg_deca', 'genetica_crescimento_ps_edg_deca', 'genetica_materna_pm_emg_deca',
    'genetica_reprodutiva_ippg_deca', 'genetica_reprodutiva_stayg_deca',
    'genetica_reprodutiva_pe365g_deca', 'genetica_reprodutiva_psng_deca',
    'genetica_carcaca_aolg_deca', 'genetica_carcaca_acabg_deca', 'genetica_carcaca_marg_deca',
    'genetica_morfologica_eg_deca', 'genetica_morfologica_pg_deca', 'genetica_morfologica_mg_deca',
    'fenotipo_ipp_dias',
]

COLUNAS_BOOLEAN = ['extra_genotipado', 'extra_csg']


class PMGZLoader(BaseLoader):
    """Loader para dados PMGZ com mapeamento de colunas Excel -> snake_case."""

    def __init__(self, farm_id: int = 1):
        super().__init__(farm_id)

    def load(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Executa o pipeline completo de carregamento PMGZ com flattening de 3 níveis."""
        df = self._ler_arquivo(file_content, filename)
        df = self._flatten_columns(df)
        df = self._normalizar_cabecalhos(df)
        df = self._renomear_colunas_completo(df)
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
        """Lê Excel com header na linha 5 (index 4)."""
        try:
            df = pd.read_excel(io.BytesIO(file_content), header=[4, 5, 6])
            logger.info(f"Excel multi-header lido: {len(df)} linhas, colunas nível 0: {df.columns.nlevels}")
            return df
        except Exception as e:
            logger.warning(f"Falha no multi-header line 5, tentando método Legacy: {e}")
            return self._ler_excel_com_headers_legacy(file_content)

    def _ler_excel_com_headers_legacy(self, file_content: bytes) -> pd.DataFrame:
        """Lê Excel com headers multi-linha (células mescladas) - método fallback."""
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

        logger.info(f'Excel PMGZ lido (legacy): {len(df)} linhas, {len(df.columns)} colunas')
        return df

    def _flatten_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Achatamento de MultiIndex (3 níveis) -> strings únicas."""
        import traceback
        logger.info(f"_flatten_columns: nlevels={df.columns.nlevels}, cols={len(df.columns)}")
        
        new_columns = []
        for i, col in enumerate(df.columns):
            try:
                col_tuple = tuple(col) if hasattr(col, '__iter__') and not isinstance(col, str) else (col,)
                if len(col_tuple) > 1:
                    filtered = []
                    for nivel in col_tuple:
                        nivel_str = str(nivel).strip()
                        if nivel_str and nivel_str != 'nan' and 'Unnamed' not in nivel_str:
                            filtered.append(nivel_str)
                    if filtered:
                        new_col = '_'.join(filtered)
                    else:
                        new_col = str(col_tuple[-1]) if len(col_tuple) > 0 else 'unknown'
                else:
                    new_col = str(col).strip()
                new_columns.append(new_col)
            except Exception as e:
                logger.error(f"Erro na coluna {i}: {col} - {e}\n{traceback.format_exc()}")
                new_columns.append(f"col_{i}")
        
        df.columns = new_columns
        logger.info(f"Flattening: {len(df.columns)} colunas, sample: {df.columns[:5]}")
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

    def _renomear_colunas_completo(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica dicionário DE_PARA_PMGZ_COMPLETO para mapeamento exato."""
        logger.info(f"Colunas antes rename: {list(df.columns)[:10]}")
        
        rename_map = {}
        for col in df.columns:
            col_str = str(col)
            if col_str in DE_PARA_PMGZ_COMPLETO:
                rename_map[col_str] = DE_PARA_PMGZ_COMPLETO[col_str]
            elif col in DE_PARA_PMGZ_COMPLETO:
                rename_map[col] = DE_PARA_PMGZ_COMPLETO[col]
        
        df = df.rename(columns=rename_map)
        logger.info(f'Colunas renomeadas via DE_PARA_PMGZ_COMPLETO: {len(rename_map)} mapeamentos')
        
        colunas_sem_mapeamento = [c for c in df.columns if c not in rename_map.values]
        if colunas_sem_mapeamento:
            logger.warning(f'Colunas não mapeadas: {colunas_sem_mapeamento[:10]}')
        
        return df

    def _renomear_colunas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica mapeamento Excel -> snake_case."""
        rename_map = {}
        prefixos = {
            'ANIMAL': 'animal',
            'PAI': 'pai',
            'MÃE': 'mae',
            'MAE': 'mae',
            'AVÔ PATERNO': 'avo_paterno',
            'AVO PATERNO': 'avo_paterno',
            'AVÓ PATERNA': 'avo_paterna',
            'AVO PATERNA': 'avo_paterna',
            'AVÔ MATERNO': 'avo_materno',
            'AVO MATERNO': 'avo_materno',
            'AVÓ MATERNA': 'avo_materna',
            'AVO MATERNA': 'avo_materna',
        }

        for col in df.columns:
            col_normalizado = str(col).strip()
            
            if col_normalizado in MAPEAMENTO_EXCEL_PARA_SNAKE:
                rename_map[col] = MAPEAMENTO_EXCEL_PARA_SNAKE[col_normalizado]
                continue

            prefixo_encontrado = None
            for prefixo, key_prefix in prefixos.items():
                if col_normalizado.startswith(prefixo + ' ') or col_normalizado.startswith(prefixo.upper() + ' '):
                    prefixo_encontrado = key_prefix
                    break
            
            if prefixo_encontrado:
                subcol = col_normalizado
                for p, k in prefixos.items():
                    if col_normalizado.startswith(p + ' '):
                        subcol = col_normalizado[len(p):].strip()
                        break
                    elif col_normalizado.startswith(p.upper() + ' '):
                        subcol = col_normalizado[len(p.upper()):].strip()
                        break

                if 'NOME' in subcol.upper():
                    rename_map[col] = f'pedigree_{prefixo_encontrado}_nome'
                elif 'SERIE' in subcol.upper() or 'RGD' in subcol.upper():
                    rename_map[col] = f'pedigree_{prefixo_encontrado}_serie_rgd'
                elif 'RGN' in subcol.upper():
                    rename_map[col] = f'pedigree_{prefixo_encontrado}_rgn'
            elif col_normalizado.startswith('ANIMAL '):
                subcol = col_normalizado[7:].strip()
                if 'iABCZ' in subcol.upper():
                    rename_map[col] = 'identificacao_indice_iabczg'
                elif 'DECA' in subcol.upper():
                    rename_map[col] = 'identificacao_indice_deca'
                elif 'P %' in subcol or 'P%' in subcol:
                    rename_map[col] = 'identificacao_indice_p_perc'
                elif 'F %' in subcol or 'F%' in subcol:
                    rename_map[col] = 'identificacao_indice_f_perc'
            else:
                for excel_col, snake_col in MAPEAMENTO_EXCEL_PARA_SNAKE.items():
                    if excel_col.lower() in col_normalizado.lower() or col_normalizado.lower() in excel_col.lower():
                        if str(col) not in rename_map:
                            rename_map[str(col)] = snake_col
                        break

        df = df.rename(columns=rename_map)
        df = df.dropna(how='all')
        logger.info(f'Colunas renomeadas: {len(rename_map)} mapeamentos')
        logger.info(f'Sample colunas após rename: {list(df.columns)[:15]}')
        return df

    def _tratar_dados(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converte tipos, trata vírgulas, booleanos e limpa dados."""
        new_columns = []
        for i, col in enumerate(df.columns):
            series = df.iloc[:, i]
            if hasattr(series, 'str'):
                try:
                    series = series.astype(str).str.strip()
                    series = series.str.replace(',', '.', regex=False)
                    series = series.replace(['-', '', 'nan', 'None', 'NaN', 'nat'], None)
                except:
                    pass
            new_columns.append(series)
        df = pd.concat(new_columns, axis=1)
        df.columns = df.columns.astype(str)
        
        seen = set()
        unique_cols = []
        for col in df.columns:
            col_str = str(col)
            if col_str not in seen:
                seen.add(col_str)
                unique_cols.append(col_str)
        df = df[unique_cols]

        for col in df.columns:
            if col in COLUNAS_FLOAT:
                df[col] = df[col].apply(self._converter_numero_brasileiro)
            elif col in COLUNAS_INTEGER:
                df[col] = df[col].apply(self._converter_numero_brasileiro)
                df[col] = df[col].astype('Int64')
            elif col in COLUNAS_BOOLEAN:
                df[col] = df[col].apply(
                    lambda x: True if str(x).upper().strip() == 'SIM'
                    else (False if str(x).upper().strip() in ['NÃO', 'NAO', 'N']
                    else None)
                )

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
            'genetica_reprodutiva_psng_dep': 'pmg_psn_dep',
            'genetica_reprodutiva_psng_ac_perc': 'pmg_psn_ac',
            'genetica_reprodutiva_psng_deca': 'pmg_psn_deca',
            'genetica_reprodutiva_psng_p_perc': 'pmg_psn_p_percent',
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