"""
Script de Importação para Sistema de Melhoramento Genético Bovino
Projeto Melhora+ - Genética

Estratégia: Upsert hierárquico em camadas
- Camada 1: Avós (4 registros)
- Camada 2: Pais (2 registros)
- Camada 3: Animal principal (n registros)
- Camada 4: Avaliações genéticas
"""

import uuid
import json
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import UUID


@dataclass
class MetricBlock:
    dep: Optional[float] = None
    ac: Optional[float] = None
    deca: Optional[int] = None
    p_percent: Optional[float] = None

    def to_db_tuple(self):
        return f"({self._quote(self.dep)}, {self._quote(self.ac)}, {self._quote(self.deca)}, {self._quote(self.p_percent)})"

    def _quote(self, val):
        if val is None:
            return "NULL"
        return f"{val}"


@dataclass
class ProgenyInfo:
    filhos: Optional[int] = None
    rebanhos: Optional[int] = None

    def to_db_tuple(self):
        return f"({self._quote(self.filhos)}, {self._quote(self.rebanhos)})"

    def _quote(self, val):
        if val is None:
            return "NULL"
        return f"{val}"


@dataclass
class AnimalData:
    rgn: str
    nome: Optional[str] = None
    serie: Optional[str] = None
    sexo: Optional[str] = None
    nascimento: Optional[date] = None
    genotipado: Optional[str] = None
    csg: Optional[str] = None
    pai_rgn: Optional[str] = None
    mae_rgn: Optional[str] = None


@dataclass
class EvaluationData:
    animal_rgn: str
    safra: int
    fonte_origem: str

    iabczg: Optional[float] = None
    deca_index: Optional[int] = None

    pn_ed: MetricBlock = field(default_factory=MetricBlock)
    pd_ed: MetricBlock = field(default_factory=MetricBlock)
    pa_ed: MetricBlock = field(default_factory=MetricBlock)
    ps_ed: MetricBlock = field(default_factory=MetricBlock)
    pm_em: MetricBlock = field(default_factory=MetricBlock)

    ipp: MetricBlock = field(default_factory=MetricBlock)
    stay: MetricBlock = field(default_factory=MetricBlock)
    pe_365: MetricBlock = field(default_factory=MetricBlock)
    psn: MetricBlock = field(default_factory=MetricBlock)

    aol: MetricBlock = field(default_factory=MetricBlock)
    acab: MetricBlock = field(default_factory=MetricBlock)
    marmoreio: MetricBlock = field(default_factory=MetricBlock)

    eg: MetricBlock = field(default_factory=MetricBlock)
    pg: MetricBlock = field(default_factory=MetricBlock)
    mg: MetricBlock = field(default_factory=MetricBlock)

    fenotipo_aol: Optional[float] = None
    fenotipo_acab: Optional[float] = None
    fenotipo_ipp: Optional[float] = None
    fenotipo_stay: Optional[float] = None

    p120_info: ProgenyInfo = field(default_factory=ProgenyInfo)
    p210_info: ProgenyInfo = field(default_factory=ProgenyInfo)
    p365_info: ProgenyInfo = field(default_factory=ProgenyInfo)
    p450_info: ProgenyInfo = field(default_factory=ProgenyInfo)


class GeneticsImporter:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.rgn_to_id: dict[str, uuid.UUID] = {}

    def import_from_dataframe(self, df: pd.DataFrame, fonte_origem: str = 'PMGZ', safra: int = 2024):
        """
        Importa dados de um DataFrame pandas
        """
        print(f"Iniciando importação de {len(df)} registros...")

        # Extrair todos os RGNs únicos
        all_rgns = self._collect_all_rgns(df)

        # Criar/upsertar animais em camadas
        self._process_animals_cascade(df, all_rgns)

        # Criar avaliações genéticas
        self._process_evaluations(df, fonte_origem, safra)

        print(f"Importação concluída! {len(self.rgn_to_id)} animais processados.")

    def _collect_all_rgns(self, df: pd.DataFrame) -> dict[str, list[dict]]:
        """
        Coleta todos os RGNs únicos do DataFrame organizando por profundidade genealógica
        """
        rgns = {
            'avos_paternos': set(),
            'avos_maternos': set(),
            'pais': set(),
            'principais': set()
        }

        for _, row in df.iterrows():
            # Animal principal
            if pd.notna(row.get('rgn')):
                rgns['principais'].add(str(row['rgn']))

            # Pais
            if pd.notna(row.get('pai_rgn')):
                rgns['pais'].add(str(row['pai_rgn']))
            if pd.notna(row.get('mae_rgn')):
                rgns['pais'].add(str(row['mae_rgn']))

            # Avós paternos
            if pd.notna(row.get('avo_paterno_rgn')):
                rgns['avos_paternos'].add(str(row['avo_paterno_rgn']))
            if pd.notna(row.get('avo_paterno_mae_rgn')):
                rgns['avos_paternos'].add(str(row['avo_paterno_mae_rgn']))

            # Avós maternos
            if pd.notna(row.get('avo_materno_rgn')):
                rgns['avos_maternos'].add(str(row['avo_materno_rgn']))
            if pd.notna(row.get('avo_materno_mae_rgn')):
                rgns['avos_maternos'].add(str(row['avo_materno_mae_rgn']))

        # Converter para OrderedDict por profundidade (avós primeiro)
        return {
            'avos_paternos': list(rgns['avos_paternos']),
            'avos_maternos': list(rgns['avos_maternos']),
            'pais': list(rgns['pais']),
            'principais': list(rgns['principais'])
        }

    def _process_animals_cascade(self, df: pd.DataFrame, all_rgns: dict[str, list]):
        """
        Processa animais em camadas para garantir que pais existam antes dos filhos
        """
        # Camada 1: Avós paternos
        print("  Processando avós paternos...")
        self._upsert_animals_from_rgn_list(all_rgns['avos_paternos'], df)

        # Camada 2: Avós maternos
        print("  Processando avós maternos...")
        self._upsert_animals_from_rgn_list(all_rgns['avos_maternos'], df)

        # Camada 3: Pais
        print("  Processando pais...")
        self._upsert_animals_from_rgn_list(all_rgns['pais'], df)

        # Camada 4: Animais principais
        print("  Processando animais principais...")
        self._upsert_animals_from_rgn_list(all_rgns['principais'], df)

    def _upsert_animals_from_rgn_list(self, rgn_list: list, df: pd.DataFrame):
        """
        Cria/atualiza animais a partir de uma lista de RGNs
        """
        if not rgn_list:
            return

        # Criar lookup por RGN
        df_by_rgn = df.set_index('rgn') if 'rgn' in df.columns else pd.DataFrame()

        for rgn in rgn_list:
            # Buscar dados do animal no DataFrame
            row = df_by_rgn.get(rgn)

            if row is not None and not isinstance(row, pd.DataFrame):
                animal_data = self._extract_animal_data(row)
            else:
                # Animal não tem dados completos, criar registro básico
                animal_data = AnimalData(rgn=rgn)

            self._upsert_animal(animal_data)

    def _extract_animal_data(self, row: pd.Series) -> AnimalData:
        """Extrai dados do animal de uma linha do DataFrame"""
        return AnimalData(
            rgn=str(row.get('rgn', '')),
            nome=row.get('nome'),
            serie=row.get('serie'),
            sexo=row.get('sexo'),
            nascimento=pd.to_datetime(row.get('nascimento')) if pd.notna(row.get('nascimento')) else None,
            genotipado=row.get('genotipado'),
            csg=row.get('csg'),
            pai_rgn=row.get('pai_rgn'),
            mae_rgn=row.get('mae_rgn')
        )

    def _upsert_animal(self, data: AnimalData):
        """
        Upsert de animal (INSERT ou UPDATE)
        """
        # Verificar se já existe
        existing_id = self.rgn_to_id.get(data.rgn)

        if existing_id:
            # UPDATE
            self._update_animal(existing_id, data)
        else:
            # INSERT
            new_id = self._insert_animal(data)
            if new_id:
                self.rgn_to_id[data.rgn] = new_id

    def _insert_animal(self, data: AnimalData) -> Optional[uuid.UUID]:
        """Insere novo animal"""
        # Converter sexo para enum
        sexo_val = f"'{data.sexo}'" if data.sexo in ['M', 'F'] else 'NULL'
        genotipado_val = f"'{data.genotipado}'" if data.genotipado in ['SIM', 'NÃO'] else 'NULL'
        csg_val = f"'{data.csg}'" if data.csg in ['SIM', 'NÃO'] else 'NULL'

        # Converter data
        nasc_val = f"'{data.nascimento}'" if data.nascimento else 'NULL'

        # Buscar IDs dos pais
        sire_id_val = f"'{self.rgn_to_id.get(data.pai_rgn)}'" if data.pai_rgn and self.rgn_to_id.get(data.pai_rgn) else 'NULL'
        dam_id_val = f"'{self.rgn_to_id.get(data.mae_rgn)}'" if data.mae_rgn and self.rgn_to_id.get(data.mae_rgn) else 'NULL'

        # Criar UUID
        new_id = uuid.uuid4()

        sql = f"""
        INSERT INTO genetics.animals (
            id, nome, serie, rgn, sexo, nascimento,
            genotipado, csg, sire_id, dam_id
        ) VALUES (
            '{new_id}',
            {self._quote(data.nome)},
            {self._quote(data.serie)},
            {self._quote(data.rgn)},
            {sexo_val},
            {nasc_val},
            {genotipado_val},
            {csg_val},
            {sire_id_val},
            {dam_id_val}
        )
        ON CONFLICT (rgn) DO NOTHING
        RETURNING id;
        """

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                row = result.fetchone()
                if row:
                    return row[0]
                # Se não retornou, pode já existir
                # Buscar ID existente
                return self._get_animal_id_by_rgn(data.rgn)
        except Exception as e:
            print(f"Erro ao inserir animal {data.rgn}: {e}")
            return None

    def _update_animal(self, animal_id: uuid.UUID, data: AnimalData):
        """Atualiza animal existente"""
        # Buscar IDs dos pais (pode ter mudado)
        sire_id_val = f"'{self.rgn_to_id.get(data.pai_rgn)}'" if data.pai_rgn and self.rgn_to_id.get(data.pai_rgn) else 'NULL'
        dam_id_val = f"'{self.rgn_to_id.get(data.mae_rgn)}'" if data.mae_rgn and self.rgn_to_id.get(data.mae_rgn) else 'NULL'

        nasc_val = f"'{data.nascimento}'" if data.nascimento else 'NULL'
        sexo_val = f"'{data.sexo}'" if data.sexo in ['M', 'F'] else 'NULL'

        sql = f"""
        UPDATE genetics.animals SET
            nome = COALESCE({self._quote(data.nome)}, nome),
            serie = COALESCE({self._quote(data.serie)}, serie),
            sexo = COALESCE({sexo_val}, sexo),
            nascimento = COALESCE({nasc_val}, nascimento),
            sire_id = COALESCE({sire_id_val}, sire_id),
            dam_id = COALESCE({dam_id_val}, dam_id),
            genotipado = COALESCE({self._quote(data.genotipado)}, genotipado),
            csg = COALESCE({self._quote(data.csg)}, csg)
        WHERE id = '{animal_id}';
        """

        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
        except Exception as e:
            print(f"Erro ao atualizar animal {data.rgn}: {e}")

    def _get_animal_id_by_rgn(self, rgn: str) -> Optional[uuid.UUID]:
        """Busca ID do animal pelo RGN"""
        sql = f"SELECT id FROM genetics.animals WHERE rgn = {self._quote(rgn)} LIMIT 1;"
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                row = result.fetchone()
                if row:
                    return row[0]
        except Exception as e:
            print(f"Erro ao buscar ID do animal {rgn}: {e}")
        return None

    def _process_evaluations(self, df: pd.DataFrame, fonte_origem: str, safra: int):
        """Processa avaliações genéticas"""
        print(f"  Processando avaliações genéticas (safra {safra})...")

        for _, row in df.iterrows():
            rgn = row.get('rgn')
            if not rgn or pd.isna(rgn):
                continue

            animal_id = self.rgn_to_id.get(str(rgn))
            if not animal_id:
                print(f"  AVISO: Animal {rgn} não encontrado, pulando avaliação")
                continue

            eval_data = self._extract_evaluation_data(row, animal_id, fonte_origem, safra)
            self._insert_evaluation(eval_data)

    def _extract_evaluation_data(self, row: pd.Series, animal_id: uuid.UUID, fonte: str, safra: int) -> EvaluationData:
        """Extrai dados de avaliação de uma linha do DataFrame"""

        def parse_metric(dep_col, ac_col, deca_col, p_percent_col) -> MetricBlock:
            return MetricBlock(
                dep=row.get(dep_col),
                ac=row.get(ac_col),
                deca=int(row[deca_col]) if pd.notna(row.get(deca_col)) else None,
                p_percent=row.get(p_percent_col)
            )

        return EvaluationData(
            animal_id=str(animal_id),
            fonte_origem=fonte,
            safra=safra,
            iabczg=row.get('iabczg'),
            deca_index=int(row['deca_index']) if pd.notna(row.get('deca_index')) else None,
            pn_ed=parse_metric('pn_ed_dep', 'pn_ed_ac', 'pn_ed_deca', 'pn_ed_p_percent'),
            pd_ed=parse_metric('pd_ed_dep', 'pd_ed_ac', 'pd_ed_deca', 'pd_ed_p_percent'),
            pa_ed=parse_metric('pa_ed_dep', 'pa_ed_ac', 'pa_ed_deca', 'pa_ed_p_percent'),
            ps_ed=parse_metric('ps_ed_dep', 'ps_ed_ac', 'ps_ed_deca', 'ps_ed_p_percent'),
            pm_em=parse_metric('pm_em_dep', 'pm_em_ac', 'pm_em_deca', 'pm_em_p_percent'),
            ipp=parse_metric('ipp_dep', 'ipp_ac', 'ipp_deca', 'ipp_p_percent'),
            stay=parse_metric('stay_dep', 'stay_ac', 'stay_deca', 'stay_p_percent'),
            pe_365=parse_metric('pe_365_dep', 'pe_365_ac', 'pe_365_deca', 'pe_365_p_percent'),
            psn=parse_metric('psn_dep', 'psn_ac', 'psn_deca', 'psn_p_percent'),
            aol=parse_metric('aol_dep', 'aol_ac', 'aol_deca', 'aol_p_percent'),
            acab=parse_metric('acab_dep', 'acab_ac', 'acab_deca', 'acab_p_percent'),
            marmoreio=parse_metric('marmoreio_dep', 'marmoreio_ac', 'marmoreio_deca', 'marmoreio_p_percent'),
            eg=parse_metric('eg_dep', 'eg_ac', 'eg_deca', 'eg_p_percent'),
            pg=parse_metric('pg_dep', 'pg_ac', 'pg_deca', 'pg_p_percent'),
            mg=parse_metric('mg_dep', 'mg_ac', 'mg_deca', 'mg_p_percent'),
            fenotipo_aol=row.get('fenotipo_aol'),
            fenotipo_acab=row.get('fenotipo_acab'),
            fenotipo_ipp=row.get('fenotipo_ipp'),
            fenotipo_stay=row.get('fenotipo_stay'),
            p120_info=ProgenyInfo(
                filhos=int(row['desc_p120_filhos']) if pd.notna(row.get('desc_p120_filhos')) else None,
                rebanhos=int(row['desc_p120_rebanhos']) if pd.notna(row.get('desc_p120_rebanhos')) else None
            ),
            p210_info=ProgenyInfo(
                filhos=int(row['desc_p210_filhos']) if pd.notna(row.get('desc_p210_filhos')) else None,
                rebanhos=int(row['desc_p210_rebanhos']) if pd.notna(row.get('desc_p210_rebanhos')) else None
            ),
            p365_info=ProgenyInfo(
                filhos=int(row['desc_p365_filhos']) if pd.notna(row.get('desc_p365_filhos')) else None,
                rebanhos=int(row['desc_p365_rebanhos']) if pd.notna(row.get('desc_p365_rebanhos')) else None
            ),
            p450_info=ProgenyInfo(
                filhos=int(row['desc_p450_filhos']) if pd.notna(row.get('desc_p450_filhos')) else None,
                rebanhos=int(row['desc_p450_rebanhos']) if pd.notna(row.get('desc_p450_rebanhos')) else None
            )
        )

    def _insert_evaluation(self, data: EvaluationData):
        """Insere avaliação genética"""
        new_id = uuid.uuid4()

        sql = f"""
        INSERT INTO genetics.genetic_evaluations (
            id, animal_id, safra, fonte_origem,
            iabczg, deca_index,
            pn_ed, pd_ed, pa_ed, ps_ed, pm_em,
            ipp, stay, pe_365, psn,
            aol, acab, marmoreio,
            eg, pg, mg,
            fenotipo_aol, fenotipo_acab, fenotipo_ipp, fenotipo_stay,
            p120_info, p210_info, p365_info, p450_info
        ) VALUES (
            '{new_id}',
            '{data.animal_id}',
            {data.safra},
            '{data.fonte_origem}',
            {self._quote(data.iabczg)},
            {self._quote(data.deca_index)},
            {data.pn_ed.to_db_tuple()},
            {data.pd_ed.to_db_tuple()},
            {data.pa_ed.to_db_tuple()},
            {data.ps_ed.to_db_tuple()},
            {data.pm_em.to_db_tuple()},
            {data.ipp.to_db_tuple()},
            {data.stay.to_db_tuple()},
            {data.pe_365.to_db_tuple()},
            {data.psn.to_db_tuple()},
            {data.aol.to_db_tuple()},
            {data.acab.to_db_tuple()},
            {data.marmoreio.to_db_tuple()},
            {data.eg.to_db_tuple()},
            {data.pg.to_db_tuple()},
            {data.mg.to_db_tuple()},
            {self._quote(data.fenotipo_aol)},
            {self._quote(data.fenotipo_acab)},
            {self._quote(data.fenotipo_ipp)},
            {self._quote(data.fenotipo_stay)},
            {data.p120_info.to_db_tuple()},
            {data.p210_info.to_db_tuple()},
            {data.p365_info.to_db_tuple()},
            {data.p450_info.to_db_tuple()}
        )
        ON CONFLICT (animal_id, safra) DO UPDATE SET
            iabczg = EXCLUDED.iabczg,
            deca_index = EXCLUDED.deca_index;
        """

        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
        except Exception as e:
            print(f"Erro ao inserir avaliação para {data.animal_id}: {e}")

    def _quote(self, val):
        """Formata valor para SQL"""
        if val is None:
            return "NULL"
        if isinstance(val, str):
            return f"'{val.replace("'", "''")}"
        return str(val)


# ============================================
# EXEMPLO DE USO
# ============================================

if __name__ == "__main__":
    import os

    DB_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/melhoramais")

    # Ler arquivo XLS
    df = pd.read_excel("dados_pmgz.xlsx")

    # Renomear colunas conforme mapeamento
    column_mapping = {
        'Registro': 'rgn',
        'Nome': 'nome',
        'Serie': 'serie',
        'Sexo': 'sexo',
        'Data_Nasc': 'nascimento',
        'Pai_Reg': 'pai_rgn',
        'Mae_Reg': 'mae_rgn',
        # ... outras colunas
    }
    df = df.rename(columns=column_mapping)

    # Importar
    importer = GeneticsImporter(DB_URL)
    importer.import_from_dataframe(df, fonte_origem='PMGZ', safra=2024)