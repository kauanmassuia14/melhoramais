import pandas as pd
import io
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models import ColumnMapping, ProcessingLog, Upload, IS_SQLITE, GeneticsAnimal, GeneticsFarm

logger = logging.getLogger(__name__)


class GeneticDataProcessor:
    def __init__(self, db: Session, farm_id: str = None, upload_id: str = None):
        self.db = db
        self.farm_id = farm_id
        self.upload_id = upload_id
        self.upload_log_id = None

    def get_mappings(self, source_system: str) -> Dict[str, str]:
        mappings = self.db.query(ColumnMapping).filter(
            ColumnMapping.source_system == source_system
        ).all()
        return {m.source_column: m.target_column for m in mappings}

    def get_required_columns(self, source_system: str) -> List[str]:
        mappings = self.db.query(ColumnMapping).filter(
            ColumnMapping.source_system == source_system,
            ColumnMapping.is_required == True,
        ).all()
        return [m.source_column for m in mappings]

    def _match_columns(
        self, df: pd.DataFrame, col_map: Dict[str, str], required: List[str]
    ) -> Tuple[pd.DataFrame, Dict[str, str]]:
        import re
        file_lookup: Dict[str, str] = {}

        for col in df.columns:
            col_str = str(col)
            norm = col_str.strip().lower().replace(" ", "_")
            file_lookup[norm] = col_str

            parenthetical = re.search(r'\(([^)]+)\)', col_str)
            if parenthetical:
                file_lookup[parenthetical.group(1).lower().strip()] = col_str

            col_lower = col_str.lower()
            dep_suffixes = [" dep", " ac %", " deca", " p %"]
            for suffix in dep_suffixes:
                if col_lower.endswith(suffix):
                    base = col_lower[:-len(suffix)].strip()
                    base_underscored = base.replace(" ", "_")
                    if base not in file_lookup:
                        file_lookup[base] = col_str
                    if base_underscored not in file_lookup:
                        file_lookup[base_underscored] = col_str

        rename: Dict[str, str] = {}
        missing: List[str] = []

        for source_col, target_col in col_map.items():
            norm_source = source_col.strip().lower().replace(" ", "_")
            explicit_suffix = None
            for suff in ["_dep", "_ac%", "_deca", "_p_%"]:
                if norm_source.endswith(suff):
                    explicit_suffix = suff
                    break

            actual = None

            if explicit_suffix:
                actual = file_lookup.get(norm_source)
                if not actual:
                    alt = norm_source.replace("_ac%", "_ac_%").replace("_p%", "_p_%").replace("_deca", "_deca")
                    actual = file_lookup.get(alt)
            else:
                actual = file_lookup.get(norm_source)
                if not actual:
                    alt = norm_source.replace("_", "-")
                    actual = file_lookup.get(alt)

            if actual is not None:
                rename[actual] = target_col
            elif source_col in required:
                missing.append(source_col)

        if missing:
            available = list(df.columns)
            raise ValueError(f"Required columns missing: {missing}")

        return df, rename

    def process_file(
        self, file_content: bytes, filename: str, source_system: str
    ) -> Tuple[pd.DataFrame, ProcessingLog, Upload]:
        from sqlalchemy.exc import SQLAlchemyError
        from backend.database import SessionLocal

        log = None
        upload = None

        try:
            df, inserted, updated, failed = self._process_and_persist(
                file_content, filename, source_system
            )

            if self.upload_id:
                upload = self.db.query(Upload).filter(
                    Upload.upload_id == self.upload_id
                ).first()
                if upload:
                    upload.total_registros = len(df)
                    upload.rows_inserted = inserted
                    upload.rows_updated = updated
                    upload.status = "completed"
                    upload.completed_at = datetime.utcnow()
                    upload.arquivo_nome_original = filename

            self.db.commit()
            return df, None, upload

        except Exception as e:
            self.db.rollback()

            fresh_db = SessionLocal()
            try:
                failed_log = fresh_db.query(ProcessingLog).filter(
                    ProcessingLog.id == log_id
                ).first()
                if failed_log:
                    failed_log.status = "failed"
                    failed_log.error_message = str(e)[:1000]
                    failed_log.completed_at = datetime.utcnow()
                    fresh_db.commit()

                if self.upload_id:
                    failed_upload = fresh_db.query(Upload).filter(
                        Upload.upload_id == self.upload_id
                    ).first()
                    if failed_upload:
                        failed_upload.status = "failed"
                        failed_upload.error_message = str(e)[:1000]
                        failed_upload.completed_at = datetime.utcnow()
                        fresh_db.commit()
            except Exception:
                fresh_db.rollback()
                raise
            finally:
                fresh_db.close()

            raise

    def _process_and_persist(
        self, file_content: bytes, filename: str, source_system: str
    ) -> Tuple[pd.DataFrame, int, int, int]:
        df = self._read_file(file_content, filename, source_system)

        if source_system == "PMGZ":
            col_map = {}
            required = []
        else:
            col_map = self.get_mappings(source_system)
            required = self.get_required_columns(source_system)

        df, rename = self._match_columns(df, col_map, required)
        df = df.rename(columns=rename)
        df = self._clean_data(df, source_system)

        df["id_farm"] = self.farm_id
        if self.upload_id:
            df["upload_id"] = self.upload_id

        inserted, updated, failed = self._upsert_genetics_animals(df, source_system)

        return df, inserted, updated, failed

    def _read_file(self, file_content: bytes, filename: str, source_system: str) -> pd.DataFrame:
        from backend.loaders import PMGZLoader
        
        if filename.endswith((".xlsx", ".xls")):
            if source_system == "PMGZ":
                loader = PMGZLoader(farm_id=self.farm_id)
                df = loader.load(file_content, filename)
                df = loader.para_colunas_banco(df)
            else:
                df = pd.read_excel(io.BytesIO(file_content))
        elif filename.endswith(".csv"):
            if source_system == "PMGZ":
                df = pd.read_csv(io.BytesIO(file_content), sep="\t")
                if len(df.columns) == 1:
                    df = pd.read_csv(io.BytesIO(file_content), sep=";")
                if len(df.columns) == 1:
                    df = pd.read_csv(io.BytesIO(file_content))
            else:
                df = pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith(".PAG"):
            df = pd.read_csv(io.BytesIO(file_content), sep=None, engine="python")
        else:
            raise ValueError(f"Unsupported file format: {filename}")

        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all")

        return df

    def _clean_data(self, df: pd.DataFrame, source_system: str) -> pd.DataFrame:
        if "sexo" in df.columns:
            df["sexo"] = df["sexo"].astype(str).str.upper().str.strip()
            sex_map = {"MACHO": "M", "FEMEA": "F", "FÊMEA": "F", "1": "M", "2": "F"}
            df["sexo"] = df["sexo"].replace(sex_map)
            df["sexo"] = df["sexo"].apply(
                lambda x: x[0] if isinstance(x, str) and len(x) > 0 and x[0] in ["M", "F"] else None
            )

        if "data_nascimento" in df.columns:
            df["data_nascimento"] = pd.to_datetime(df["data_nascimento"], errors="coerce").dt.date

        if "raca" in df.columns:
            df["raca"] = df["raca"].fillna("Nelore").replace(["", "nan", "None", "-"], "Nelore")

        if "fonte_origem" not in df.columns:
            df["fonte_origem"] = source_system

        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].str.replace(",", ".", regex=False)
            df[col] = df[col].replace(["-", "", "nan", "None", "NaN", "nat"], None)

        float_columns = {
            "p210_peso_desmama", "p365_peso_ano", "p450_peso_sobreano", "peso_nascimento", "peso_final",
            "pe_perimetro_escrotal", "a_area_olho_lombo", "eg_espessura_gordura", "altura", "circumference",
            "im_idade_primeiro_parto", "intervalo_partos", "dias_gestacao",
            "anc_mg", "anc_te", "anc_m", "anc_p", "anc_dp", "anc_sp", "anc_e", "anc_sao", "anc_leg", "anc_sh", "anc_pp30",
            "anc_dipp", "anc_d3p", "anc_dstay", "anc_dpn", "anc_dp12", "anc_dpe", "anc_daol", "anc_dacab",
            "anc_ac_mg", "anc_ac_te", "anc_ac_m", "anc_ac_p",
            "gen_iqg", "gen_pmm", "gen_p", "gen_dp", "gen_sp", "gen_e", "gen_sao", "gen_leg", "gen_sh", "gen_pp30",
            "gen_pn", "gen_p120", "gen_tmd", "gen_pd", "gen_tm120", "gen_ps", "gen_gpd", "gen_cfd", "gen_cfs",
            "gen_hp_stay", "gen_rd", "gen_egs", "gen_acab", "gen_mar",
            "gen_ac_iqg", "gen_ac_pmm", "gen_ac_p",
            "pmg_iabc", "pmg_zpmm", "pmg_p", "pmg_dp", "pmg_sp", "pmg_e", "pmg_sao", "pmg_leg", "pmg_sh",
            "pmg_pp30", "pmg_pn", "pmg_pa", "pmg_ps", "pmg_pm", "pmg_ipp", "pmg_stay", "pmg_pe", "pmg_aol",
            "pmg_acab", "pmg_mar", "pmg_deca", "pmg_deca_pn", "pmg_deca_p12", "pmg_deca_ps", "pmg_deca_stay",
            "pmg_deca_pe", "pmg_deca_aol", "pmg_meta_p", "pmg_meta_m", "pmg_meta_t",
            "pmg_ac_iabc", "pmg_ac_p", "pmg_ac_m",
            "pmg_p_percent", "pmg_f_percent",
            "pmg_pn_dep", "pmg_pn_ac", "pmg_pn_deca", "pmg_pn_p_percent",
            "pmg_pd_dep", "pmg_pd_ac", "pmg_pd_deca", "pmg_pd_p_percent",
            "pmg_pa_dep", "pmg_pa_ac", "pmg_pa_deca", "pmg_pa_p_percent",
            "pmg_ps_dep", "pmg_ps_ac", "pmg_ps_deca", "pmg_ps_p_percent",
            "pmg_pm_dep", "pmg_pm_ac", "pmg_pm_deca", "pmg_pm_p_percent",
            "pmg_ipp_dep", "pmg_ipp_ac", "pmg_ipp_deca", "pmg_ipp_p_percent",
            "pmg_stay_dep", "pmg_stay_ac", "pmg_stay_deca", "pmg_stay_p_percent",
            "pmg_pe365_dep", "pmg_pe365_ac", "pmg_pe365_deca", "pmg_pe365_p_percent",
            "pmg_psn_dep", "pmg_psn_ac", "pmg_psn_deca", "pmg_psn_p_percent",
            "pmg_aol_dep", "pmg_aol_ac", "pmg_aol_deca", "pmg_aol_p_percent",
            "pmg_acab_dep", "pmg_acab_ac", "pmg_acab_deca", "pmg_acab_p_percent",
            "pmg_mar_dep", "pmg_mar_ac", "pmg_mar_deca", "pmg_mar_p_percent",
            "pmg_eg_dep", "pmg_eg_ac", "pmg_eg_deca", "pmg_eg_p_percent",
            "pmg_p_dep", "pmg_p_ac", "pmg_p_deca", "pmg_p_p_percent",
            "pmg_m_dep", "pmg_m_ac", "pmg_m_deca", "pmg_m_p_percent",
            "p120_peso_120"
        }

        for col in df.columns:
            if col in float_columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                except:
                    pass

        return df

    def _upsert_genetics_animals(self, df: pd.DataFrame, source_system: str) -> Tuple[int, int, int]:
        from sqlalchemy import text
        import uuid

        if len(df) == 0:
            return 0, 0, 0

        farm = self.db.query(GeneticsFarm).first()
        if not farm:
            logger.error("No farm found in genetics.farms")
            return 0, 0, len(df)

        genetics_farm_id = farm.id
        upload_id_val = self.upload_id if self.upload_id else None

        def safe_str(val):
            if pd.isna(val):
                return None
            s = str(val).strip()
            return s if s and s.lower() not in ['nan', 'none', ''] else None

        def safe_bool(val):
            if pd.isna(val):
                return None
            v = str(val).upper().strip()
            if v == 'SIM':
                return True
            elif v in ['NÃO', 'NAO', 'N', '']:
                return False
            return None

        def to_tuple(dep_val, ac_val, deca_val, p_val):
            def clean_val(v):
                if pd.isna(v):
                    return None
                try:
                    return float(v)
                except:
                    return None
            return (
                clean_val(dep_val),
                clean_val(ac_val),
                clean_val(deca_val) if deca_val and not pd.isna(deca_val) else None,
                clean_val(p_val)
            )

        BATCH_SIZE = 2000
        inserted = 0
        updated = 0
        failed = 0
        total_rows = len(df)

        for batch_start in range(0, total_rows, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_rows)
            batch_df = df.iloc[batch_start:batch_end]

            batch_rgns = batch_df['rgn_animal'].dropna().astype(str).str.strip().tolist()
            batch_rgns = [r for r in batch_rgns if r]

            existing_map = {}
            if batch_rgns:
                existing = self.db.execute(
                    text("SELECT rgn, id FROM genetics.animals WHERE rgn = ANY(:rgds) AND farm_id = :fid"),
                    {"rgds": batch_rgns, "fid": str(genetics_farm_id)}
                ).fetchall()
                existing_map = {r: uid for r, uid in existing}

            animal_ids_map = {}
            animals_to_insert = []
            animals_to_update_ids = []

            for _, row in batch_df.iterrows():
                rgn = row.get('rgn_animal')
                if not rgn or not str(rgn).strip():
                    failed += 1
                    continue

                rgn_str = str(rgn).strip()

                if rgn_str in existing_map:
                    animal_id = existing_map[rgn_str]
                    animal_ids_map[rgn_str] = animal_id
                    animals_to_update_ids.append(animal_id)
                else:
                    animal_id = uuid.uuid4()
                    animal_ids_map[rgn_str] = animal_id
                    animals_to_insert.append({
                        'id': str(animal_id),
                        'farm_id': str(genetics_farm_id),
                        'rgn': rgn_str,
                        'nome': safe_str(row.get('nome_animal')),
                        'serie': safe_str(row.get('pmg_serie_rgd')),
                        'sexo': safe_str(row.get('sexo')),
                        'nascimento': safe_str(row.get('data_nascimento')),
                        'genotipado': safe_bool(row.get('genotipado')),
                        'csg': safe_bool(row.get('csg')),
                        'upload_id': upload_id_val,
                    })

            if animals_to_insert:
                self.db.execute(
                    text("""
                        INSERT INTO genetics.animals (id, farm_id, rgn, nome, serie, sexo, nascimento, genotipado, csg, upload_id)
                        VALUES (:id, :farm_id, :rgn, :nome, :serie, :sexo, :nascimento, :genotipado, :csg, :upload_id)
                    """),
                    animals_to_insert
                )
                inserted += len(animals_to_insert)

            if animals_to_update_ids:
                self.db.execute(
                    text("""
                        UPDATE genetics.animals SET
                            nome = CASE WHEN :nome IS NOT NULL THEN :nome ELSE nome END,
                            serie = CASE WHEN :serie IS NOT NULL THEN :serie ELSE serie END,
                            sexo = CASE WHEN :sexo IS NOT NULL THEN :sexo ELSE sexo END,
                            nascimento = CASE WHEN :nascimento IS NOT NULL THEN :nascimento ELSE nascimento END,
                            genotipado = CASE WHEN :genotipado IS NOT NULL THEN :genotipado ELSE genotipado END,
                            csg = CASE WHEN :csg IS NOT NULL THEN :csg ELSE csg END,
                            upload_id = COALESCE(:upload_id, upload_id)
                        WHERE id = ANY(:ids)
                    """),
                    {
                        'ids': animals_to_update_ids,
                        'nome': safe_str(batch_df.iloc[0].get('nome_animal')),
                        'serie': safe_str(batch_df.iloc[0].get('pmg_serie_rgd')),
                        'sexo': safe_str(batch_df.iloc[0].get('sexo')),
                        'nascimento': safe_str(batch_df.iloc[0].get('data_nascimento')),
                        'genotipado': safe_bool(batch_df.iloc[0].get('genotipado')),
                        'csg': safe_bool(batch_df.iloc[0].get('csg')),
                        'upload_id': upload_id_val,
                    }
                )
                updated += len(animals_to_update_ids)

            eval_to_insert = []
            for _, row in batch_df.iterrows():
                rgn = row.get('rgn_animal')
                if not rgn or not str(rgn).strip():
                    continue

                rgn_str = str(rgn).strip()
                animal_id = animal_ids_map.get(rgn_str)

                if not animal_id:
                    continue

                eval_to_insert.append({
                    'id': str(uuid.uuid4()),
                    'animal_id': str(animal_id),
                    'farm_id': str(genetics_farm_id),
                    'safra': 2026,
                    'fonte_origem': source_system,
                    'iabczg': float(row.get('pmg_iabc')) if row.get('pmg_iabc') and not pd.isna(row.get('pmg_iabc')) else None,
                    'pn_ed': to_tuple(row.get('pmg_pn_dep'), row.get('pmg_pn_ac'), row.get('pmg_pn_deca'), row.get('pmg_pn_p_percent')),
                    'pd_ed': to_tuple(row.get('pmg_pd_dep'), row.get('pmg_pd_ac'), row.get('pmg_pd_deca'), row.get('pmg_pd_p_percent')),
                    'ps_ed': to_tuple(row.get('pmg_ps_dep'), row.get('pmg_ps_ac'), row.get('pmg_ps_deca'), row.get('pmg_ps_p_percent')),
                    'pm_em': to_tuple(row.get('pmg_pm_dep'), row.get('pmg_pm_ac'), row.get('pmg_pm_deca'), row.get('pmg_pm_p_percent')),
                    'ipp': to_tuple(row.get('pmg_ipp_dep'), row.get('pmg_ipp_ac'), row.get('pmg_ipp_deca'), row.get('pmg_ipp_p_percent')),
                    'stay': to_tuple(row.get('pmg_stay_dep'), row.get('pmg_stay_ac'), row.get('pmg_stay_deca'), row.get('pmg_stay_p_percent')),
                    'pe_365': to_tuple(row.get('pmg_pe365_dep'), row.get('pmg_pe365_ac'), row.get('pmg_pe365_deca'), row.get('pmg_pe365_p_percent')),
                    'psn': to_tuple(row.get('pmg_psn_dep'), row.get('pmg_psn_ac'), row.get('pmg_psn_deca'), row.get('pmg_psn_p_percent')),
                    'aol': to_tuple(row.get('pmg_aol_dep'), row.get('pmg_aol_ac'), row.get('pmg_aol_deca'), row.get('pmg_aol_p_percent')),
                    'acab': to_tuple(row.get('pmg_acab_dep'), row.get('pmg_acab_ac'), row.get('pmg_acab_deca'), row.get('pmg_acab_p_percent')),
                    'marmoreio': to_tuple(row.get('pmg_mar_dep'), row.get('pmg_mar_ac'), row.get('pmg_mar_deca'), row.get('pmg_mar_p_percent')),
                    'eg': to_tuple(row.get('pmg_eg_dep'), row.get('pmg_eg_ac'), row.get('pmg_eg_deca'), row.get('pmg_eg_p_percent')),
                    'pg': to_tuple(row.get('pmg_p_dep'), row.get('pmg_p_ac'), row.get('pmg_p_deca'), row.get('pmg_p_p_percent')),
                    'mg': to_tuple(row.get('pmg_m_dep'), row.get('pmg_m_ac'), row.get('pmg_m_deca'), row.get('pmg_m_p_percent')),
                })

            if eval_to_insert:
                self.db.execute(
                    text("""
                        INSERT INTO genetics.genetic_evaluations 
                        (id, animal_id, farm_id, safra, fonte_origem, iabczg, pn_ed, pd_ed, ps_ed, pm_em, ipp, stay, pe_365, psn, aol, acab, marmoreio, eg, pg, mg)
                        VALUES (:id, :animal_id, :farm_id, :safra, :fonte_origem, :iabczg, :pn_ed, :pd_ed, :ps_ed, :pm_em, :ipp, :stay, :pe_365, :psn, :aol, :acab, :marmoreio, :eg, :pg, :mg)
                    """),
                    eval_to_insert
                )

            self.db.commit()

        logger.info(f"Genetics upsert: inserted={inserted}, updated={updated}, failed={failed}")
        return inserted, updated, failed

    def generate_formatted_excel(self, df: pd.DataFrame) -> bytes:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Melhora+_Clean")
        return output.getvalue()