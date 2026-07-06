import pandas as pd
import io
import logging
from typing import Dict, List, Tuple
from datetime import datetime, timezone
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
                    upload.completed_at = datetime.now(timezone.utc)
                    upload.arquivo_nome_original = filename

            self.db.commit()

            # Recalcular cache em background
            try:
                from backend.routers.animals_v2 import refresh_dashboard_cache_background
                import threading
                if self.farm_id:
                    threading.Thread(target=refresh_dashboard_cache_background, args=(str(self.farm_id),), daemon=True).start()
                threading.Thread(target=refresh_dashboard_cache_background, args=("ALL",), daemon=True).start()
            except Exception as cache_err:
                logger.error(f"Failed to trigger cache refresh after upload: {cache_err}")

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
                        failed_upload.completed_at = datetime.now(timezone.utc)
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

        # Remove linhas totalmente vazias (evita processar "fantasmas" no Excel)
        df = df.dropna(how='all')
        if df.empty:
            raise ValueError("O arquivo parece estar vazio.")

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
                    "Raça": "raca",
                    "Série": "serie_animal",
                    "Serie": "serie_animal",
                    "Genotipado": "genotipado"
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
            elif source_system == "GENEPLUS":
                col_map = {
                    "Ident": "rgn_animal",
                    "Nome": "nome_animal",
                    "Sx": "sexo",
                    "Dtn": "data_nascimento",
                    "Cc": "raca",
                }
                required = ["Ident"]

        # Para PMGZ, o loader já faz o mapeamento completo e robusto.
        # Não precisamos do _match_columns genérico que pode falhar com as colunas já renomeadas.
        if source_system == "PMGZ":
            rename = {}
            # Garante que rgn_animal está presente (o loader já deve ter garantido)
            if 'rgn_animal' not in df.columns:
                # Fallback caso o loader não tenha mapeado por algum motivo
                df, rename = self._match_columns(df, col_map, required)
        else:
            df, rename = self._match_columns(df, col_map, required)
            
        if rename:
            df = df.rename(columns=rename)

        
        # Validação extra de segurança para evitar KeyError 'rgn_animal'
        if 'rgn_animal' not in df.columns:
            # Tenta achar alguma coluna que se pareça com RGN
            for c in df.columns:
                if str(c).upper() in ["RGN", "REGISTRO", "RGD", "CGA", "ID"]:
                    df = df.rename(columns={c: 'rgn_animal'})
                    break
            
            if 'rgn_animal' not in df.columns:
                available = list(df.columns)
                raise ValueError(f"Não foi possível encontrar a coluna de Registro (RGN) no arquivo. Colunas disponíveis: {available}")

        df = self._clean_data(df, source_system)

        # Remove duplicados de RGN + Série no próprio DataFrame para evitar CardinalityViolation no PostgreSQL
        if 'rgn_animal' in df.columns:
            # LIMPEZA CRÍTICA: rgn_animal e serie_animal devem ser limpos e padronizados antes do drop_duplicates
            df['rgn_animal'] = df['rgn_animal'].astype(str).str.strip().str.upper()
            df['rgn_animal'] = df['rgn_animal'].replace(['NAN', 'NONE', '', 'NAT'], None)
            df = df.dropna(subset=['rgn_animal'])
            
            if 'serie_animal' in df.columns:
                df['serie_animal'] = df['serie_animal'].astype(str).str.strip().str.upper()
                df['serie_animal'] = df['serie_animal'].replace(['NAN', 'NONE', '', 'NAT'], '')
            else:
                df['serie_animal'] = ''
            
            initial_count = len(df)
            df = df.drop_duplicates(subset=['rgn_animal', 'serie_animal'], keep='last')
            final_count = len(df)
            if initial_count > final_count:
                logger.info(f"Removidos {initial_count - final_count} registros duplicados de RGN+Série do arquivo.")

        # Usar o novo schema genetics
        results = self._upsert_genetics_animals(df, source_system)
        inserted, updated, failed = results if isinstance(results, tuple) else (0, 0, 0)

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
                            except Exception:
                                content_io.seek(0)
                                df = pd.read_csv(content_io, sep=",", encoding="utf-8")
            elif filename.lower().endswith(".csv"):
                try:
                    df = pd.read_csv(content_io, sep=";", encoding="utf-8")
                except Exception:
                    content_io.seek(0)
                    df = pd.read_csv(content_io, sep=",", encoding="utf-8")
            elif filename.lower().endswith(".pag"):
                df = pd.read_csv(content_io, sep=None, engine="python")
            else:
                # Try guessing
                try:
                    df = pd.read_excel(content_io)
                except Exception:
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
            df["data_nascimento"] = pd.to_datetime(df["data_nascimento"], dayfirst=True, errors="coerce").dt.date

        if "raca" in df.columns:
            df["raca"] = df["raca"].fillna("Não Informado").replace(["", "nan", "None", "-"], "Não Informado")

        if "fonte_origem" not in df.columns:
            df["fonte_origem"] = source_system

        for col in df.columns:
            if col == "data_nascimento":
                df[col] = df[col].replace([pd.NaT, None], None)
                continue
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
            "gen_pt_iqg", "gen_iqg_basico", "gen_pt_iqg_bat",
            "gen_dep_pn", "gen_acc_pn", "gen_dep_pmm", "gen_acc_pmm", "gen_dep_tmm", "gen_acc_tmm",
            "gen_dep_pd", "gen_acc_pd", "gen_dep_tmd", "gen_acc_tmd", "gen_dep_ps", "gen_acc_ps",
            "gen_dep_gpd", "gen_acc_gpd", "gen_dep_cfd", "gen_acc_cfd", "gen_dep_cfs", "gen_acc_cfs",
            "gen_dep_stay", "gen_acc_stay", "gen_dep_pes", "gen_acc_pes", "gen_dep_ipp", "gen_acc_ipp",
            "gen_dep_pp30", "gen_acc_pp30", "gen_dep_rd", "gen_acc_rd", "gen_dep_aol", "gen_acc_aol",
            "gen_dep_egs", "gen_acc_egs", "gen_dep_mar", "gen_acc_mar", "gen_dep_car", "gen_acc_car",
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
                except Exception:
                    pass

        # Enforce 3-decimal precision for deepCAR / CAR columns
        for col in df.columns:
            if "CAR" in str(col).upper():
                try:
                    df[col] = pd.to_numeric(df[col], errors="coerce").round(3)
                except Exception:
                    pass

        return df

    def _upsert_genetics_animals(self, df: pd.DataFrame, source_system: str) -> Tuple[int, int, int]:
        from sqlalchemy import text
        import uuid
        import json

        if len(df) == 0:
            return 0, 0, 0

        if self.farm_id:
            farm = self.db.query(GeneticsFarm).filter(GeneticsFarm.id == self.farm_id).first()
        else:
            farm = self.db.query(GeneticsFarm).first()

        if not farm:
            logger.error(f"No farm found in genetics.farms for ID: {self.farm_id}")
            return 0, 0, len(df)

        genetics_farm_id = farm.id
        upload_id_val = self.upload_id if self.upload_id else None

        def safe_str(val):
            if pd.isna(val) or val is None:
                return None
            s = str(val).strip()
            return s if s and s.lower() not in ['nan', 'none', ''] else None

        def safe_date(v):
            if pd.isna(v) or v is None:
                return None
            # Trata strings vazias ou placeholders
            s_val = str(v).strip().lower()
            if not s_val or s_val in ['nan', 'none', '', '-', 'nat', '—']:
                return None
            
            if isinstance(v, datetime):
                return v.date()
            if hasattr(v, 'date'):
                try: return v.date()
                except: pass
                
            try:
                # Prioridade total para formato brasileiro DD/MM/YYYY
                dt = pd.to_datetime(v, dayfirst=True, errors='coerce')
                if pd.notna(dt):
                    return dt.date()
            except Exception:
                pass
            return None

        def safe_bool(val):
            if pd.isna(val) or val is None:
                return None
            v = str(val).upper().strip()
            # ANCP usa 'G' para Genotipado
            if v in ['SIM', 'S', 'G', 'TRUE', '1']:
                return True
            elif v in ['NÃO', 'NAO', 'N', 'FALSE', '0', '']:
                return False
            return None

        def safe_float(v):
            if pd.isna(v) or v is None:
                return None
            try:
                # Limpeza robusta: remove "TOP", "%", espaços e trata vírgula como ponto
                s = str(v).upper().replace("TOP", "").replace("%", "").replace(",", ".").strip()
                if not s or s in ['-', 'NAN', 'NONE', '', 'NAT']:
                    return None
                return float(s)
            except Exception:
                return None

        # NOTE: safe_date already defined above (line ~425) — duplicate removed

        # Helper para busca robusta de colunas (case-insensitive, ignore spaces/underscores/accents)
        def get_val(r, col_name):
            import unicodedata
            if not col_name: return None
            if col_name in r: return r[col_name]
            
            def norm(text):
                if not text: return ""
                return "".join(
                    c for c in unicodedata.normalize('NFD', str(text))
                    if unicodedata.category(c) != 'Mn'
                ).lower().replace(" ", "").replace("_", "").replace("-", "")

            c_norm = norm(col_name)
            for k in r.keys():
                if norm(k) == c_norm:
                    return r[k]
            return None

        # BATCH_SIZE otimizado para reduzir round-trips e evitar timeouts
        BATCH_SIZE = 1000
        inserted = 0
        updated = 0
        failed = 0
        total_rows = len(df)

        logger.info(f"Iniciando processamento de {total_rows} registros em lotes de {BATCH_SIZE}...")

        for batch_start in range(0, total_rows, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_rows)
            batch_df = df.iloc[batch_start:batch_end]
            logger.info(f">>> Lote {batch_start} até {batch_end} de {total_rows}...")

            # 1. Pre-assign IDs for children in this batch to handle self-referencing parents
            batch_children_keys = {}
            for _, row in batch_df.iterrows():
                r_rgn = get_val(row, 'rgn_animal') or get_val(row, 'rgn') or get_val(row, 'registro')
                if r_rgn and str(r_rgn).strip().lower() not in ['nan', 'none', '', 'nat']:
                    r_rgn_str = str(r_rgn).strip().upper()
                    r_serie_str = str(get_val(row, 'serie_animal') or get_val(row, 'serie') or get_val(row, 'série') or "").strip().upper()
                    if (r_rgn_str, r_serie_str) not in batch_children_keys:
                        batch_children_keys[(r_rgn_str, r_serie_str)] = str(uuid.uuid4())

            # 2. Extract unique sires and dams from the batch
            parents_to_resolve = []
            seen_parents = set()

            for _, row in batch_df.iterrows():
                # Sire (Father)
                sire_rgn = get_val(row, 'pai_rgn')
                if sire_rgn and str(sire_rgn).strip().lower() not in ['nan', 'none', '']:
                    sire_rgn_str = str(sire_rgn).strip().upper()
                    sire_serie_str = str(get_val(row, 'pai_serie') or get_val(row, 'pai_serie_rgd') or "").strip().upper()
                    sire_nome_str = safe_str(get_val(row, 'pai_nome'))
                    key = ('sire', sire_rgn_str, sire_serie_str)
                    if key not in seen_parents:
                        seen_parents.add(key)
                        parents_to_resolve.append({
                            'type': 'sire',
                            'rgn': sire_rgn_str,
                            'serie': sire_serie_str,
                            'nome': sire_nome_str or f"PAI: {sire_rgn_str}",
                            'raca': safe_str(get_val(row, 'raca') or get_val(row, 'raça'))
                        })

                # Dam (Mother)
                dam_rgn = get_val(row, 'mae_rgn')
                if dam_rgn and str(dam_rgn).strip().lower() not in ['nan', 'none', '']:
                    dam_rgn_str = str(dam_rgn).strip().upper()
                    dam_serie_str = str(get_val(row, 'mae_serie') or get_val(row, 'mae_serie_rgd') or "").strip().upper()
                    dam_nome_str = safe_str(get_val(row, 'mae_nome'))
                    key = ('dam', dam_rgn_str, dam_serie_str)
                    if key not in seen_parents:
                        seen_parents.add(key)
                        parents_to_resolve.append({
                            'type': 'dam',
                            'rgn': dam_rgn_str,
                            'serie': dam_serie_str,
                            'nome': dam_nome_str or f"MÃE: {dam_rgn_str}",
                            'raca': safe_str(get_val(row, 'raca') or get_val(row, 'raça'))
                        })

            # 3. Query existing parents in database to map their IDs
            parent_ids_map = {}
            if parents_to_resolve:
                parent_rgns = list({p['rgn'] for p in parents_to_resolve})
                existing_parents = self.db.execute(
                    text("SELECT rgn, COALESCE(serie, ''), id FROM genetics.animals WHERE rgn = ANY(:rgns) AND farm_id = :fid"),
                    {"rgns": parent_rgns, "fid": str(genetics_farm_id)}
                ).fetchall()
                for row_rgn, row_serie, uid in existing_parents:
                    parent_ids_map[(row_rgn, row_serie)] = str(uid)

            # 4. Insert missing parents as placeholders
            parents_to_insert = []
            for p in parents_to_resolve:
                key = (p['rgn'], p['serie'])
                if key in parent_ids_map:
                    continue
                if key in batch_children_keys:
                    parent_ids_map[key] = batch_children_keys[key]
                    continue
                
                p_uuid = str(uuid.uuid4())
                parent_ids_map[key] = p_uuid
                parents_to_insert.append({
                    'id': p_uuid,
                    'farm_id': str(genetics_farm_id),
                    'rgn': p['rgn'],
                    'nome': p['nome'],
                    'serie': p['serie'],
                    'sexo': 'M' if p['type'] == 'sire' else 'F',
                    'raca': p['raca'],
                    'nascimento': None,
                    'genotipado': False,
                    'csg': False,
                    'upload_id': upload_id_val,
                })

            from psycopg2.extras import execute_values
            raw_conn = self.db.connection().connection

            if parents_to_insert:
                logger.info(f"  - [TURBO] Inserindo {len(parents_to_insert)} pais temporários...")
                with raw_conn.cursor() as cur:
                    parent_sql = """
                        INSERT INTO genetics.animals (id, farm_id, rgn, nome, serie, sexo, raca, nascimento, genotipado, csg, upload_id, sire_id, dam_id)
                        VALUES %s
                        ON CONFLICT (farm_id, rgn, serie) DO UPDATE SET
                            nome = COALESCE(genetics.animals.nome, EXCLUDED.nome),
                            sexo = COALESCE(genetics.animals.sexo, EXCLUDED.sexo),
                            raca = COALESCE(genetics.animals.raca, EXCLUDED.raca)
                    """
                    parent_tuples = []
                    for p in parents_to_insert:
                        parent_tuples.append((
                            p['id'], p['farm_id'], p['rgn'], p['nome'], p['serie'],
                            p['sexo'], p['raca'], None, 'NÃO', 'NÃO', p['upload_id'], None, None
                        ))
                    template = "(%s, %s, %s, %s, %s, %s, %s, %s, %s::genetics.boolean_status, %s::genetics.boolean_status, %s, %s, %s)"
                    execute_values(cur, parent_sql, parent_tuples, template=template)

            # 5. Build child animals with linked sire_id and dam_id
            animals_data = []
            seen_rgns_in_batch = set()

            for _, row in batch_df.iterrows():
                rgn = get_val(row, 'rgn_animal') or get_val(row, 'rgn') or get_val(row, 'registro')
                if not rgn or str(rgn).strip().lower() in ['nan', 'none', '', 'nat']:
                    failed += 1
                    continue
                
                rgn_str = str(rgn).strip().upper()
                serie_str = str(get_val(row, 'serie_animal') or get_val(row, 'serie') or get_val(row, 'série') or "").strip().upper()
                combo_key = (rgn_str, serie_str)
                if combo_key in seen_rgns_in_batch:
                    continue
                seen_rgns_in_batch.add(combo_key)
                
                # Resolve sire and dam IDs
                sire_rgn = get_val(row, 'pai_rgn')
                sire_id = None
                if sire_rgn and str(sire_rgn).strip().lower() not in ['nan', 'none', '']:
                    s_rgn_str = str(sire_rgn).strip().upper()
                    s_serie_str = str(get_val(row, 'pai_serie') or get_val(row, 'pai_serie_rgd') or "").strip().upper()
                    sire_id = parent_ids_map.get((s_rgn_str, s_serie_str))

                dam_rgn = get_val(row, 'mae_rgn')
                dam_id = None
                if dam_rgn and str(dam_rgn).strip().lower() not in ['nan', 'none', '']:
                    d_rgn_str = str(dam_rgn).strip().upper()
                    d_serie_str = str(get_val(row, 'mae_serie') or get_val(row, 'mae_serie_rgd') or "").strip().upper()
                    dam_id = parent_ids_map.get((d_rgn_str, d_serie_str))

                # Busca Nascimento
                nasc_raw = get_val(row, 'data_nascimento') or get_val(row, 'nascimento') or get_val(row, 'nasc')
                nasc_val = safe_date(nasc_raw)

                child_uuid = batch_children_keys.get(combo_key) or str(uuid.uuid4())

                animals_data.append({
                    'id': child_uuid,
                    'farm_id': str(genetics_farm_id),
                    'rgn': rgn_str,
                    'nome': safe_str(get_val(row, 'nome_animal') or get_val(row, 'nome')),
                    'serie': serie_str,
                    'sexo': safe_str(get_val(row, 'sexo')),
                    'raca': safe_str(get_val(row, 'raca') or get_val(row, 'raça')),
                    'nascimento': nasc_val,
                    'genotipado': safe_bool(get_val(row, 'genotipado') or get_val(row, 'genotipado_animal')),
                    'csg': safe_bool(get_val(row, 'csg') or get_val(row, 'csg_animal')),
                    'upload_id': upload_id_val,
                    'sire_id': sire_id,
                    'dam_id': dam_id
                })

            if animals_data:
                logger.info(f"  - [TURBO] Fazendo upsert de {len(animals_data)} animais...")
                with raw_conn.cursor() as cur:
                    # Upsert Animals including sire_id and dam_id
                    animal_sql = """
                        INSERT INTO genetics.animals (id, farm_id, rgn, nome, serie, sexo, raca, nascimento, genotipado, csg, upload_id, sire_id, dam_id)
                        VALUES %s
                        ON CONFLICT (farm_id, rgn, serie) DO UPDATE SET
                            nome = EXCLUDED.nome,
                            sexo = COALESCE(EXCLUDED.sexo, genetics.animals.sexo),
                            raca = COALESCE(EXCLUDED.raca, genetics.animals.raca),
                            nascimento = COALESCE(EXCLUDED.nascimento, genetics.animals.nascimento),
                            genotipado = EXCLUDED.genotipado,
                            csg = EXCLUDED.csg,
                            upload_id = EXCLUDED.upload_id,
                            sire_id = COALESCE(EXCLUDED.sire_id, genetics.animals.sire_id),
                            dam_id = COALESCE(EXCLUDED.dam_id, genetics.animals.dam_id)
                    """
                    animal_tuples = []
                    for a in animals_data:
                        gen_status = None
                        if a['genotipado'] is True: gen_status = 'SIM'
                        elif a['genotipado'] is False: gen_status = 'NÃO'
                        
                        csg_status = None
                        if a['csg'] is True: csg_status = 'SIM'
                        elif a['csg'] is False: csg_status = 'NÃO'

                        animal_tuples.append((
                            a['id'], a['farm_id'], a['rgn'], a['nome'], a['serie'],
                            a['sexo'], a['raca'], a['nascimento'], gen_status, csg_status, a['upload_id'],
                            a['sire_id'], a['dam_id']
                        ))
                    
                    template = "(%s, %s, %s, %s, %s, %s, %s, %s, %s::genetics.boolean_status, %s::genetics.boolean_status, %s, %s, %s)"
                    execute_values(cur, animal_sql, animal_tuples, template=template)
                inserted += len(animals_data)

            # Get IDs (ainda via SQLAlchemy para conveniência, mas com índice é rápido)
            rgns_in_batch = [a['rgn'] for a in animals_data]
            animal_id_map = {}
            db_res = self.db.execute(
                text("SELECT rgn, COALESCE(serie, ''), id FROM genetics.animals WHERE rgn = ANY(:rgns) AND farm_id = :fid"),
                {"rgns": list(set(rgns_in_batch)), "fid": str(genetics_farm_id)}
            ).fetchall()
            for row_rgn, row_serie, uid in db_res:
                animal_id_map[(row_rgn, row_serie)] = uid

            eval_to_insert = []
            for _, row in batch_df.iterrows():
                rgn = str(row.get('rgn_animal') or "").strip()
                serie = str(row.get('serie_animal') or "").strip()
                animal_id = animal_id_map.get((rgn, serie))
                if not animal_id: continue

                metrics_data = {}
                # ... (mapa de métricas simplificado para o prompt)
                # Mapeamento de busca no DataFrame (usa nomes internos ou originais)
                # Mapa de métricas conforme a fonte (Nomes originais para cada plataforma)
                if source_system == "PMGZ":
                    dep_map = {
                        "PN-EDg": ("pmg_pn_dep", "pmg_pn_ac", "pmg_pn_deca", "pmg_pn_p_percent"),
                        "PD-EDg": ("pmg_pd_dep", "pmg_pd_ac", "pmg_pd_deca", "pmg_pd_p_percent"),
                        "PS-EDg": ("pmg_ps_dep", "pmg_ps_ac", "pmg_ps_deca", "pmg_ps_p_percent"),
                        "IPPg": ("pmg_ipp_dep", "pmg_ipp_ac", "pmg_ipp_deca", "pmg_ipp_p_percent"),
                        "STAYg": ("pmg_stay_dep", "pmg_stay_ac", "pmg_stay_deca", "pmg_stay_p_percent"),
                        "AOLg": ("pmg_aol_dep", "pmg_aol_ac", "pmg_aol_deca", "pmg_aol_p_percent"),
                        "ACABg": ("pmg_acab_dep", "pmg_acab_ac", "pmg_acab_deca", "pmg_acab_p_percent"),
                        "MARg": ("pmg_mar_dep", "pmg_mar_ac", "pmg_mar_deca", "pmg_mar_p_percent"),
                    }
                elif source_system == "ANCP":
                    # Mantém nomes originais da ANCP para não confundir as plataformas
                    dep_map = {
                        "DPN": ("DPN", "ACC_DPN", "TOP_DPN", None),
                        "D3P": ("D3P", "ACC_D3P", "TOP_D3P", None),
                        "DP210": ("DP210", "ACC_DP210", "TOP_DP210", None),
                        "DP365": ("DP365", "ACC_DP365", "TOP_DP365", None),
                        "DP450": ("DP450", "ACC_DP450", "TOP_DP450", None),
                        "DIPM": ("DIPM", "ACC_DIPM", "TOP_DIPM", None),
                        "DIPP": ("DIPP", "ACC_DIPP", "TOP_DIPP", None),
                        "DSTAY": ("DSTAY", "ACC_DSTAY", "TOP_DSTAY", None),
                        "DSTAY54": ("DSTAY54", "ACC_DSTAY54", "TOP_DSTAY54", None),
                        "DPE365": ("DPE365", "ACC_DPE365", "TOP_DPE365", None),
                        "DPE450": ("DPE450", "ACC_DPE450", "TOP_DPE450", None),
                        "MP120": ("MP120", "ACC_MP120", "TOP_MP120", None),
                        "DAOL": ("DAOL", "ACC_DAOL", "TOP_DAOL", None),
                        "DACAB": ("DACAB", "ACC_DACAB", "TOP_DACAB", None),
                        "DMAR": ("DMAR", "ACC_DMAR", "TOP_DMAR", None),
                        "DES": ("DES", "ACC_DES", "TOP_DES", None),
                        "DPS": ("DPS", "ACC_DPS", "TOP_DPS", None),
                        "DMS": ("DMS", "ACC_DMS", "TOP_DMS", None),
                        "CAR": ("DCAR", "ACC_DCAR", "TOP_DCAR", None),
                        "IMS": ("IMS", "ACC_IMS", "TOP_IMS", None),
                    }
                elif source_system == "GENEPLUS":
                    # Geneplus usa DepXX / AccXX como convenção
                    # Chaves do metrics JSONB usam nomes normalizados para cross-platform comparison
                    dep_map = {
                        "PN":    ("DepPN",   "AccPN",   None, None),
                        "PMm":   ("DepPMm",  "AccPMm",  None, None),
                        "TMm":   ("DepTMm",  "AccTMm",  None, None),
                        "PD":    ("DepPD",   "AccPD",   None, None),
                        "TMD":   ("DepTMD",  "AccTMD",  None, None),
                        "PS":    ("DepPS",   "AccPS",   None, None),
                        "GPD":   ("DepGPD",  "AccGPD",  None, None),
                        "CFD":   ("DepCFD",  "AccCFD",  None, None),
                        "CFS":   ("DepCFS",  "AccCFS",  None, None),
                        "STAY":  ("DepSTAY", "AccSTAY", None, None),
                        "PES":   ("DepPES",  "AccPES",  None, None),
                        "IPP":   ("DepIPP",  "AccIPP",  None, None),
                        "PP30":  ("DepPP30", "AccPP30", None, None),
                        "RD":    ("DepRD",   "AccRD",   None, None),
                        "AOL":   ("DepAOL",  "AccAOL",  None, None),
                        "EGS":   ("DepEGS",  "AccEGS",  None, None),
                        "MAR":   ("DepMAR",  "AccMAR",  None, None),
                        "CAR":   ("DepCAR",  "AccCAR",  None, None),
                    }
                else:
                    dep_map = {}

                # (Helper get_val já definido acima no loop de animais para reaproveitamento)

                for metric_key, cols in dep_map.items():
                    dep_col, ac_col, rank_col, perc_col = cols
                    val_dep = safe_float(get_val(row, dep_col))
                    if val_dep is not None:
                        if "CAR" in str(metric_key).upper() or "CAR" in str(dep_col).upper():
                            val_dep = round(val_dep, 3)
                        metrics_data[metric_key] = {
                            "dep": val_dep,
                            "acc": safe_float(get_val(row, ac_col)),
                            "top": safe_float(get_val(row, rank_col)),
                            "perc": safe_float(get_val(row, perc_col))
                        }

                # Índices principais
                if source_system == "ANCP":
                    indice_val = safe_float(get_val(row, 'MGTe') or get_val(row, 'mgte'))
                    rank_val = safe_float(get_val(row, 'TOP_MGTe') or get_val(row, 'top_mgte') or get_val(row, 'TOP') or get_val(row, 'top'))
                elif source_system == "GENEPLUS":
                    indice_val = safe_float(get_val(row, 'IQG') or get_val(row, 'gen_iqg'))
                    rank_val = safe_float(get_val(row, 'PtIQG') or get_val(row, 'gen_pt_iqg'))
                else:  # PMGZ ou outro
                    indice_val = safe_float(get_val(row, 'pmg_iabc') or get_val(row, 'identificacao_indice_iabczg') or get_val(row, 'iabczg') or get_val(row, 'iabcz'))
                    rank_val = safe_float(get_val(row, 'pmg_deca') or get_val(row, 'identificacao_indice_deca') or get_val(row, 'deca') or get_val(row, 'deca_index'))

                rank_int = int(round(rank_val)) if rank_val is not None else None

                # Determinar a safra com base no ano da safra ou data de nascimento do animal
                safra_raw = (get_val(row, 'safra') or get_val(row, 'ano_safra') 
                             or get_val(row, 'Safra') or get_val(row, 'Ano') 
                             or get_val(row, 'ano') or get_val(row, 'ano_nascimento')
                             or get_val(row, 'AnoNasc'))
                safra_val = None
                if safra_raw is not None:
                    try:
                        safra_val = int(float(str(safra_raw).replace(",", ".").strip()))
                    except Exception:
                        pass
                
                if not safra_val:
                    nasc_raw = get_val(row, 'data_nascimento') or get_val(row, 'nascimento') or get_val(row, 'nasc')
                    nasc_val = safe_date(nasc_raw)
                    if nasc_val:
                        # Safra pecuária: nascidos de 01/07/ANO até 30/06/(ANO+1) pertencem à safra ANO.
                        # Exemplo: nascido em Maio/2026 -> Safra 2025. Nascido em Agosto/2025 -> Safra 2025.
                        if nasc_val.month < 7:
                            safra_val = nasc_val.year - 1
                        else:
                            safra_val = nasc_val.year

                if not safra_val:
                    # Fallback seguro: usa o último ano com dados de referência ANCP
                    # Evita usar datetime.now().year que pode gerar safras futuras sem referência
                    safra_val = 2024

                eval_to_insert.append((
                    str(uuid.uuid4()), str(animal_id), str(genetics_farm_id),
                    safra_val, source_system, indice_val, rank_int, rank_val, json.dumps(metrics_data),
                    json.dumps({}), json.dumps({}), upload_id_val
                ))

            if eval_to_insert:
                logger.info(f"  - [TURBO] Fazendo upsert de {len(eval_to_insert)} avaliações...")
                raw_conn = self.db.connection().connection
                with raw_conn.cursor() as cur:
                    eval_sql = """
                        INSERT INTO genetics.genetic_evaluations 
                        (id, animal_id, farm_id, safra, fonte_origem, indice_principal, rank_principal, percentil_principal, metrics, progeny_stats, phenotypes, upload_id)
                        VALUES %s
                        ON CONFLICT (animal_id, safra, fonte_origem) DO UPDATE SET
                            indice_principal = EXCLUDED.indice_principal,
                            rank_principal = EXCLUDED.rank_principal,
                            percentil_principal = EXCLUDED.percentil_principal,
                            metrics = EXCLUDED.metrics,
                            upload_id = EXCLUDED.upload_id
                    """

                    execute_values(cur, eval_sql, eval_to_insert)
            
            self.db.commit()
            logger.info(f"  - Lote finalizado.")

        logger.info(f"Genetics upsert bulk: total={total_rows}, failed={failed}")
        return inserted, 0, failed

    def generate_formatted_excel(self, df: pd.DataFrame) -> bytes:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Melhora+_Clean")
        return output.getvalue()