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
            import traceback
            logger.error(f"Error in process_file: {str(e)}")
            logger.error(traceback.format_exc())
            self.db.rollback()

            from backend.database import SessionLocal
            fresh_db = SessionLocal()
            try:
                if self.upload_id:
                    failed_upload = fresh_db.query(Upload).filter(
                        Upload.upload_id == self.upload_id
                    ).first()
                    if failed_upload:
                        failed_upload.status = "failed"
                        failed_upload.error_message = str(e)[:1000]
                        failed_upload.completed_at = datetime.utcnow()
                        fresh_db.commit()
            except Exception as inner_e:
                logger.error(f"Error updating failed upload status: {inner_e}")
                fresh_db.rollback()
            finally:
                fresh_db.close()

            raise e

    def _process_and_persist(
        self, file_content: bytes, filename: str, source_system: str
    ) -> Tuple[pd.DataFrame, int, int, int]:
        df = self._read_file(file_content, filename, source_system)

        col_map = self.get_mappings(source_system)
        required = self.get_required_columns(source_system)
        
        # Fallback se não houver mapeamento no banco
        if not col_map:
            if source_system == "ANCP":
                col_map = {
                    "RGN": "rgn_animal",
                    "Nome": "nome_animal",
                    "Sexo": "sexo",
                    "Nasc": "data_nascimento",
                    "Raça": "raca"
                }
                required = ["RGN"]
            elif source_system == "PMGZ":
                col_map = {
                    "RGN": "rgn_animal",
                    "Nome": "nome_animal",
                    "Sexo": "sexo",
                    "Nascimento": "data_nascimento"
                }
                required = ["RGN"]

        df, rename = self._match_columns(df, col_map, required)
        df = df.rename(columns=rename)
        
        # Validação extra de segurança para evitar KeyError 'rgn_animal'
        if 'rgn_animal' not in df.columns:
            # Tenta achar alguma coluna que se pareça com RGN
            for c in df.columns:
                if str(c).upper() in ["RGN", "REGISTRO", "RGD", "CGA"]:
                    df = df.rename(columns={c: 'rgn_animal'})
                    break
            
            if 'rgn_animal' not in df.columns:
                available = list(df.columns)
                raise ValueError(f"Não foi possível encontrar a coluna de Registro (RGN) no arquivo. Colunas disponíveis: {available}")

        df = self._clean_data(df, source_system)

        # Usar o novo schema genetics
        inserted, updated, failed = self._upsert_genetics_animals(df, source_system)

        return df, inserted, updated, failed

    def _read_file(self, file_content: bytes, filename: str, source_system: str) -> pd.DataFrame:
        from backend.loaders import PMGZLoader
        import io
        
        content_io = io.BytesIO(file_content)
        
        try:
            if filename.lower().endswith((".xlsx", ".xls")):
                if source_system == "PMGZ":
                    loader = PMGZLoader(farm_id=self.farm_id)
                    df = loader.load(file_content, filename)
                    df = loader.para_colunas_banco(df)
                else:
                    try:
                        # Try as Excel first with openpyxl
                        df = pd.read_excel(content_io, engine="openpyxl")
                    except Exception:
                        content_io.seek(0)
                        try:
                            # Try as Excel old format
                            df = pd.read_excel(content_io, engine="xlrd")
                        except Exception:
                            content_io.seek(0)
                            # Fallback: maybe it's a CSV with .xls extension
                            try:
                                df = pd.read_csv(content_io, sep=";", encoding="utf-8")
                            except:
                                content_io.seek(0)
                                df = pd.read_csv(content_io, sep=",", encoding="utf-8")
            elif filename.lower().endswith(".csv"):
                try:
                    df = pd.read_csv(content_io, sep=";", encoding="utf-8")
                except:
                    content_io.seek(0)
                    df = pd.read_csv(content_io, sep=",", encoding="utf-8")
            elif filename.lower().endswith(".pag"):
                df = pd.read_csv(content_io, sep=None, engine="python")
            else:
                # Try guessing
                try:
                    df = pd.read_excel(content_io)
                except:
                    content_io.seek(0)
                    df = pd.read_csv(content_io, sep=";")
        except Exception as e:
            raise ValueError(f"Não foi possível ler o arquivo {filename}: {str(e)}")

        if df is None or df.empty:
            raise ValueError(f"O arquivo {filename} está vazio ou não pôde ser processado.")

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
        import json

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

        def safe_float(v):
            if pd.isna(v):
                return None
            try:
                return float(v)
            except:
                return None

        def safe_date(v):
            if pd.isna(v) or not v:
                return None
            try:
                if isinstance(v, datetime):
                    return v.date()
                return pd.to_datetime(v).date()
            except:
                return None

        # BATCH_SIZE maior para performance
        BATCH_SIZE = 1000
        inserted = 0
        updated = 0
        failed = 0
        total_rows = len(df)

        for batch_start in range(0, total_rows, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_rows)
            batch_df = df.iloc[batch_start:batch_end]
            
            animals_data = []
            for _, row in batch_df.iterrows():
                rgn = row.get('rgn_animal')
                if not rgn or not str(rgn).strip():
                    failed += 1
                    continue
                
                rgn_str = str(rgn).strip()
                animals_data.append({
                    'id': str(uuid.uuid4()),
                    'farm_id': str(genetics_farm_id),
                    'rgn': rgn_str,
                    'nome': safe_str(row.get('nome_animal')),
                    'serie': safe_str(row.get('serie_animal') or row.get('pmg_serie_rgd')),
                    'sexo': safe_str(row.get('sexo')),
                    'nascimento': safe_date(row.get('data_nascimento')),
                    'genotipado': safe_bool(row.get('genotipado')),
                    'csg': safe_bool(row.get('csg')),
                    'upload_id': upload_id_val,
                })

            if not animals_data:
                continue

            # Upsert Animals
            self.db.execute(
                text("""
                    INSERT INTO genetics.animals (id, farm_id, rgn, nome, serie, sexo, nascimento, genotipado, csg, upload_id)
                    VALUES (:id, :farm_id, :rgn, :nome, :serie, :sexo, :nascimento, :genotipado, :csg, :upload_id)
                    ON CONFLICT (farm_id, rgn) DO UPDATE SET
                        nome = EXCLUDED.nome,
                        serie = COALESCE(EXCLUDED.serie, genetics.animals.serie),
                        sexo = COALESCE(EXCLUDED.sexo, genetics.animals.sexo),
                        nascimento = COALESCE(EXCLUDED.nascimento, genetics.animals.nascimento),
                        genotipado = COALESCE(EXCLUDED.genotipado, genetics.animals.genotipado),
                        csg = COALESCE(EXCLUDED.csg, genetics.animals.csg),
                        upload_id = EXCLUDED.upload_id
                """),
                animals_data
            )
            inserted += len(animals_data)

            # Get IDs of animals for evaluations
            rgns_in_batch = [a['rgn'] for a in animals_data]
            animal_id_map = {r: uid for r, uid in self.db.execute(
                text("SELECT rgn, id FROM genetics.animals WHERE rgn = ANY(:rgns) AND farm_id = :fid"),
                {"rgns": rgns_in_batch, "fid": str(genetics_farm_id)}
            ).fetchall()}

            eval_to_insert = []
            for _, row in batch_df.iterrows():
                rgn = str(row.get('rgn_animal') or "").strip()
                animal_id = animal_id_map.get(rgn)
                if not animal_id: continue

                metrics_data = {}
                if source_system == "PMGZ":
                    dep_map = {
                        "PN-EDg": ("pmg_pn_dep", "pmg_pn_ac", "pmg_pn_deca", "pmg_pn_p_percent"),
                        "PD-EDg": ("pmg_pd_dep", "pmg_pd_ac", "pmg_pd_deca", "pmg_pd_p_percent"),
                        "PS-EDg": ("pmg_ps_dep", "pmg_ps_ac", "pmg_ps_deca", "pmg_ps_p_percent"),
                        "IPPg": ("pmg_ipp_dep", "pmg_ipp_ac", "pmg_ipp_deca", "pmg_ipp_p_percent"),
                        "STAYg": ("pmg_stay_dep", "pmg_stay_ac", "pmg_stay_deca", "pmg_stay_p_percent"),
                        "AOLg": ("pmg_aol_dep", "pmg_aol_ac", "pmg_aol_deca", "pmg_aol_p_percent"),
                    }
                elif source_system == "ANCP":
                    dep_map = {
                        "MGTe": ("MGTe", "ACC_MGTe", "TOP_MGTe", None),
                        "D3P": ("D3P", "ACC_D3P", "TOP_D3P", None),
                        "DIPP": ("DIPP", "ACC_DIPP", "TOP_DIPP", None),
                        "DPN": ("DPN", "ACC_DPN", "TOP_DPN", None),
                        "DSTAY": ("DSTAY", "ACC_DSTAY", "TOP_DSTAY", None),
                        "DP210": ("DP210", "ACC_DP210", "TOP_DP210", None),
                        "DP450": ("DP450", "ACC_DP450", "TOP_DP450", None),
                    }
                else:
                    dep_map = {}

                for metric_name, cols in dep_map.items():
                    dep, ac, rank, perc = cols
                    val_dep = safe_float(row.get(dep))
                    if val_dep is not None:
                        metrics_data[metric_name] = {
                            "dep": val_dep,
                            "acc": safe_float(row.get(ac)),
                            "top": safe_float(row.get(rank)),
                            "perc": safe_float(row.get(perc)) if perc else None
                        }

                indice_val = safe_float(row.get('MGTe')) if source_system == "ANCP" else safe_float(row.get('pmg_iabc'))
                rank_val = safe_float(row.get('TOP_MGTe')) if source_system == "ANCP" else safe_float(row.get('pmg_deca'))

                eval_to_insert.append({
                    'id': str(uuid.uuid4()),
                    'animal_id': str(animal_id),
                    'farm_id': str(genetics_farm_id),
                    'safra': 2026,
                    'fonte_origem': source_system,
                    'indice_principal': indice_val,
                    'rank_principal': rank_val,
                    'metrics': json.dumps(metrics_data),
                    'progeny_stats': json.dumps({}),
                    'phenotypes': json.dumps({}),
                    'upload_id': upload_id_val,
                })

            if eval_to_insert:
                self.db.execute(
                    text("""
                        INSERT INTO genetics.genetic_evaluations 
                        (id, animal_id, farm_id, safra, fonte_origem, indice_principal, rank_principal, metrics, progeny_stats, phenotypes, upload_id)
                        VALUES (:id, :animal_id, :farm_id, :safra, :fonte_origem, :indice_principal, :rank_principal, :metrics, :progeny_stats, :phenotypes, :upload_id)
                        ON CONFLICT (animal_id, safra, fonte_origem) DO UPDATE SET
                            indice_principal = EXCLUDED.indice_principal,
                            rank_principal = EXCLUDED.rank_principal,
                            metrics = EXCLUDED.metrics,
                            upload_id = EXCLUDED.upload_id
                    """),
                    eval_to_insert
                )
            
            self.db.commit()

        logger.info(f"Genetics upsert bulk: total={total_rows}, failed={failed}")
        return inserted, 0, failed

    def generate_formatted_excel(self, df: pd.DataFrame) -> bytes:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Melhora+_Clean")
        return output.getvalue()