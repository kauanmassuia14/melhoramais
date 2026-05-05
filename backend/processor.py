import pandas as pd
import io
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models import ColumnMapping, Animal, ProcessingLog, Upload, IS_SQLITE, RawAnimalData

logger = logging.getLogger(__name__)


class GeneticDataProcessor:
    def __init__(self, db: Session, farm_id: int = 1, upload_id: str = None):
        self.db = db
        self.farm_id = farm_id
        self.upload_id = upload_id
        self.upload_log_id = None  # Will be set during processing

    def get_mappings(self, source_system: str) -> Dict[str, str]:
        """Fetch column mappings from DB for a source system."""
        mappings = self.db.query(ColumnMapping).filter(
            ColumnMapping.source_system == source_system
        ).all()
        return {m.source_column: m.target_column for m in mappings}

    def get_required_columns(self, source_system: str) -> List[str]:
        """Get required column names in source format for validation."""
        mappings = self.db.query(ColumnMapping).filter(
            ColumnMapping.source_system == source_system,
            ColumnMapping.is_required == True,
        ).all()
        return [m.source_column for m in mappings]

    def _match_columns(
        self, df: pd.DataFrame, col_map: Dict[str, str], required: List[str]
    ) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """
        Match file columns to mapping, handling:
        - Case differences: 'Registro' vs 'REGISTRO'
        - Whitespace: ' Registro ' vs 'Registro'
        - Pandas duplicate suffixes: RGN.1, NOME.2, etc.
        - Underscore/space: 'SERIE / RGD' vs 'serie__rgd'
        - Parenthesis: 'Peso ao nascimento - efeito direto (PN-EDg) - kg' 
        - Partial match: match part of name inside parenthesis
        - PMGZ composite: 'kg DEP' can match 'kg' (DEP is implicit in seed.py)
        """
        import re
        file_lookup: Dict[str, str] = {}
        
        for col in df.columns:
            norm = str(col).strip().lower().replace(" ", "_")
            file_lookup[norm] = col
            
            parenthetical = re.search(r'\(([^)]+)\)', str(col))
            if parenthetical:
                file_lookup[parenthetical.group(1).lower().strip()] = col
                short_code = parenthetical.group(1).lower().strip().replace("-", "")
                if short_code not in file_lookup:
                    file_lookup[short_code] = col
            file_lookup[norm] = col
            
            col_lower = str(col).lower()
            dep_suffixes = [" dep", " ac %", " deca", " p %"]
            for suffix in dep_suffixes:
                if col_lower.endswith(suffix):
                    base = col_lower[:-len(suffix)].strip()
                    base_underscored = base.replace(" ", "_")
                    if base not in file_lookup:
                        file_lookup[base] = col
                    if base_underscored not in file_lookup:
                        file_lookup[base_underscored] = col
                    # Also add version with underscore before suffix (e.g., "kg_ac_%")
                    base_with_underscore = base.replace(" ", "_")
                    if base_with_underscore not in file_lookup:
                        file_lookup[base_with_underscore] = col

        rename: Dict[str, str] = {}
        missing: List[str] = []

        for source_col, target_col in col_map.items():
            norm_source = source_col.strip().lower().replace(" ", "_")
            
            # Check if source has explicit suffix
            explicit_suffix = None
            for suff in ["_dep", "_ac%", "_deca", "_p_%"]:
                if norm_source.endswith(suff):
                    explicit_suffix = suff
                    break
            
            actual = None
            
            if explicit_suffix:
                # Source has explicit suffix - look up exact match or with underscore variant
                actual = file_lookup.get(norm_source)
                if not actual:
                    # Try: _ac% -> _ac_% (underscore before suffix)
                    alt = norm_source.replace("_ac%", "_ac_%").replace("_p%", "_p_%").replace("_deca", "_deca")
                    actual = file_lookup.get(alt)
            else:
                # Source has NO suffix (implicit DEP) - use base lookup
                actual = file_lookup.get(norm_source)
                if not actual:
                    # Try lowercase with spaces
                    alt = norm_source.replace("_", "-")
                    actual = file_lookup.get(alt)
            
            if actual is not None:
                rename[actual] = target_col
            else:
                # Try PREFIX match: "RGN" should match "ANIMAL RGN"
                source_lower = source_col.lower()
                for file_col in df.columns:
                    if file_col.lower().endswith(source_lower):
                        actual = file_col
                        logger.info(f"Prefix match: '{source_col}' -> '{file_col}'")
                        break
            
            if actual is not None:
                rename[actual] = target_col
            elif source_col in required:
                missing.append(source_col)

        if missing:
            available = list(df.columns)
            raise ValueError(
                f"Required columns missing for mapping: {missing}\n"
                f"Columns found in file ({len(available)} total):\n"
                f"{available[:50]}...\n"  # Show first 50
                f"Tip: check the column names in your Excel file match the mapping."
            )

        return df, rename

    def process_file(
        self, file_content: bytes, filename: str, source_system: str
    ) -> Tuple[pd.DataFrame, ProcessingLog, Upload]:
        """Full pipeline: read → map → clean → persist.
        
        Uses two separate transactions:
        1. First creates the ProcessingLog entry (committed immediately)
        2. Then processes and upserts animals (committed separately)
        3. Updates Upload record with results
        
        This prevents the 'current transaction is aborted' error where
        a failed animal upsert would leave the log insertion uncommitable.
        """
        from sqlalchemy.exc import SQLAlchemyError
        from backend.database import SessionLocal
        
        # Transaction 1: Create log entry and commit immediately
        log = ProcessingLog(
            id_farm=self.farm_id,
            source_system=source_system,
            filename=filename,
            status="processing",
            started_at=datetime.utcnow(),
        )
        self.db.add(log)
        self.db.commit()  # Commit immediately to persist log_id
        
        log_id = log.id
        
        # Set the log_id for use in processing
        self.upload_log_id = log_id
        
        upload = None

        try:
            # Transaction 2: Process animals (may fail without affecting log)
            df, inserted, updated, failed = self._process_and_persist(
                file_content, filename, source_system
            )

            # Save ALL raw data to raw_animal_data table
            from datetime import date as date_type
            raw_batch = []
            for _, row in df.iterrows():
                raw_values = row.to_dict()
                raw_values = {k: (None if pd.isna(v) else v) for k, v in raw_values.items()}
                # Convert dates to ISO strings for JSON serialization
                for k, v in raw_values.items():
                    if isinstance(v, date_type):
                        raw_values[k] = v.isoformat()
                raw_batch.append({
                    "id_animal": None,
                    "id_farm": self.farm_id,
                    "source_system": source_system,
                    "processing_log_id": self.upload_log_id,
                    "raw_data": raw_values,
                })
            
            if raw_batch:
                self.db.bulk_insert_mappings(RawAnimalData, raw_batch)
            self.db.commit()

            log.total_rows = len(df)
            log.rows_inserted = inserted
            log.rows_updated = updated
            log.rows_failed = failed
            log.status = "completed"
            log.completed_at = datetime.utcnow()
            
            # Update upload record if provided
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
            return df, log, upload

        except Exception as e:
            # Rollback failed animal transaction
            self.db.rollback()
            
            # Transaction 3: Update log and upload status in a FRESH session
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
                
                # Update upload status to failed
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
        """Process file and persist animals. Called within a separate transaction."""
        logger.info(f"=== START _process_and_persist ===")
        logger.info(f"file_content size: {len(file_content)} bytes")
        logger.info(f"filename: {filename}, source_system: {source_system}")
        
        # Read file
        logger.info(f"Calling _read_file...")
        df = self._read_file(file_content, filename, source_system)
        logger.info(f"After _read_file: {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"df columns: {list(df.columns)[:20]}")
        
        # Get mappings
        col_map = self.get_mappings(source_system)
        required = self.get_required_columns(source_system)
        
        # DEBUG: Log all file columns to understand the structure
        logger.info(f"File columns BEFORE mapping ({len(df.columns)}): {list(df.columns)[:30]}")
        logger.info(f"Mapping for source_system={source_system}: {col_map}")
        
        df, rename = self._match_columns(df, col_map, required)
        df = df.rename(columns=rename)
        
        logger.info(f"File columns AFTER mapping ({len(df.columns)}): {list(df.columns)[:30]}")
        logger.info(f"Rename dict applied: {rename}")
        
        valid_targets = set(Animal.__table__.columns.keys())
        logger.info(f"Valid DB columns: {len(valid_targets)}")
        
        keep = [c for c in df.columns if c in valid_targets]
        missing_from_db = [c for c in df.columns if c not in valid_targets]
        logger.info(f"Columns matched to DB: {len(keep)}")
        logger.info(f"Columns NOT matched (missing in DB): {missing_from_db[:20]}")
        valid_targets = set(Animal.__table__.columns.keys())
        keep = [c for c in df.columns if c in valid_targets]
        df = df[keep]
        df = self._clean_data(df, source_system)
        df["id_farm"] = self.farm_id
        # Add upload_id if provided
        if self.upload_id:
            df["upload_id"] = self.upload_id
        logger.info(f"Calling _upsert_animals with {len(df)} records...")
        inserted, updated, failed = self._upsert_animals(df)
        logger.info(f"_upsert_animals result: inserted={inserted}, updated={updated}, failed={failed}")
        return df, inserted, updated, failed

    def _read_file(
        self, file_content: bytes, filename: str, source_system: str
    ) -> pd.DataFrame:
        """Read file into DataFrame. Handles multi-row headers for PMGZ."""
        if filename.endswith((".xlsx", ".xls")):
            if source_system == "PMGZ":
                df = self._read_pmgz_excel(file_content)
            else:
                df = pd.read_excel(io.BytesIO(file_content))
        elif filename.endswith(".csv"):
            if source_system == "PMGZ":
                # For PMGZ CSV files - the header is in the first row
                df = pd.read_csv(io.BytesIO(file_content), sep="\t")
                # Handle potential semicolon separator
                if len(df.columns) == 1:
                    df = pd.read_csv(io.BytesIO(file_content), sep=";")
                # Handle comma separator
                if len(df.columns) == 1:
                    df = pd.read_csv(io.BytesIO(file_content))
            else:
                df = pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith(".PAG"):
            df = pd.read_csv(
                io.BytesIO(file_content), sep=None, engine="python"
            )
        else:
            raise ValueError(f"Unsupported file format: {filename}")

        # Strip whitespace from column names
        df.columns = [str(c).strip() for c in df.columns]

        # Map PMGZ columns to database fields
        if source_system == "PMGZ":
            df = self._map_pmgz_columns(df)
        
        # Drop fully empty rows
        df = df.dropna(how="all")

        return df

    def _read_pmgz_excel(self, file_content: bytes) -> pd.DataFrame:
        """
        PMGZ Excel files have MULTI-ROW headers due to merged cells.
        
        Line 5: Group names like "Peso ao nascimento - efeito direto (PN-EDg) - kg"
        Line 6: Sub-columns like "DEP", "AC%", "DECA", "P%"
        
        We use ffill() to propagate group names, then combine with sub-columns.
        """
        raw = pd.read_excel(
            io.BytesIO(file_content), header=None, nrows=20
        )
        
        logger.info(f"_read_pmgz_excel: scanned {len(raw)} rows to find header")
        
        best_row = None
        best_score = 0
        header_keywords = {
            "RGN", "NOME", "SEXO", "NASC", "SERIE", "DECA", "iABCZg", "DEP", "FILHOS",
            "ANIMAL", "PAI", "MÃE", "PESO", "IPP", "STAY", "PE-365", "AOL", "ACAB", "MAR",
            "Estrutura", "Precocidade", "Musculosidade", "GENOTIPADO", "CSG"
        }

        for i, row in raw.iterrows():
            score = 0
            for val in row.values:
                val_str = str(val).strip().upper()
                if val_str in header_keywords:
                    score += 1
            if score > best_score:
                best_score = score
                best_row = i
        
        logger.info(f"_read_pmgz_excel: best_row={best_row}, best_score={best_score}")

        if best_row is None or best_score < 2:
            rows_info = []
            for i, row in raw.iterrows():
                row_str = ", ".join([str(v)[:20] for v in row.values if pd.notna(v)])
                rows_info.append(f"Row {i}: {row_str[:100]}")
            
            raise ValueError(
                f"Could not find header row in PMGZ file. "
                f"Scanned {len(raw)} rows, best score was {best_score}. "
                f"First few rows:\n" + "\n".join(rows_info[:5])
            )

        group_row = best_row - 1
        subcol_row = best_row

        group_names_raw = raw.loc[group_row].values
        subcol_names_raw = raw.loc[subcol_row].values

        group_names_filled = pd.Series(group_names_raw).ffill().values
        subcol_names = [str(s).strip() if pd.notna(s) else "Unknown" for s in subcol_names_raw]

        composite_names = []
        for g, s in zip(group_names_filled, subcol_names):
            g_str = str(g).strip() if pd.notna(g) else ""
            if g_str and g_str != "nan":
                composite_names.append(f"{g_str} {s}")
            else:
                composite_names.append(s)

        seen = {}
        unique_names = []
        for name in composite_names:
            if name in seen:
                seen[name] += 1
                unique_names.append(f"{name}.{seen[name] - 1}")
            else:
                seen[name] = 0
                unique_names.append(name)

        df = pd.read_excel(
            io.BytesIO(file_content),
            header=None,
            skiprows=best_row + 1,
        )
        df.columns = unique_names
        
        # Rename PMGZ columns to database field names
        df = self._map_pmgz_columns(df)
        
        logger.info(f"_read_pmgz_excel: Final columns created: {len(df.columns)}, first 15: {unique_names[:15]}")

        return df

    def _map_pmgz_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map PMGZ column names to database field names."""
        rename_map = {
            "RGN": "rgn_animal",
            "NOME": "nome_animal",
            "Sexo": "sexo",
            "NASC": "data_nascimento",
            "SERIE / RGD": "pmg_serie_rgd",
            "iABCZg": "pmg_iabc",
            "DECA": "pmg_deca",
            "P %": "pmg_p_percent",
            "F %": "pmg_f_percent",
            "FILHOS": "pmg_filhos",
            "REBANHOS": "pmg_rebanhos",
            "NETOS": "pmg_netos",
            "GENOTIPADO": "genotipado",
            "CSG": "csg",
            # Peso Nascimento
            "Peso ao nascimento DEP": "pmg_pn_dep",
            "Peso ao nascimento AC %": "pmg_pn_ac",
            "Peso ao nascimento DECA": "pmg_pn_deca",
            "Peso ao nascimento P %": "pmg_pn_p_percent",
            # Peso Desmama (P210)
            "P210 DEP": "pmg_pd_dep",
            "P210 AC %": "pmg_pd_ac",
            "P210 DECA": "pmg_pd_deca",
            "P210 P %": "pmg_pd_p_percent",
            # Peso Ano (P365)
            "Peso ao ano DEP": "pmg_pa_dep",
            "Peso ao ano AC %": "pmg_pa_ac",
            "Peso ao ano DECA": "pmg_pa_deca",
            "Peso ao ano P %": "pmg_pa_p_percent",
            # Peso Sobreano (P450)
            "Peso ao sobreano DEP": "pmg_ps_dep",
            "Peso ao sobreano AC %": "pmg_ps_ac",
            "Peso ao sobreano DECA": "pmg_ps_deca",
            "Peso ao sobreano P %": "pmg_ps_p_percent",
            # Peso Materno
            "Peso maternal DEP": "pmg_pm_dep",
            "Peso maternal AC %": "pmg_pm_ac",
            "Peso maternal DECA": "pmg_pm_deca",
            "Peso maternal P %": "pmg_pm_p_percent",
            # IPP
            "Idade ao primeiro parto DEP": "pmg_ipp_dep",
            "Idade ao primeiro parto AC %": "pmg_ipp_ac",
            "Idade ao primeiro parto DECA": "pmg_ipp_deca",
            "Idade ao primeiro parto P %": "pmg_ipp_p_percent",
            # Stayability
            "Stayability DEP": "pmg_stay_dep",
            "Stayability AC %": "pmg_stay_ac",
            "Stayability DECA": "pmg_stay_deca",
            "Stayability P %": "pmg_stay_p_percent",
            # PE-365
            "PE-365 DEP": "pmg_pe365_dep",
            "PE-365 AC %": "pmg_pe365_ac",
            "PE-365 DECA": "pmg_pe365_deca",
            "PE-365 P %": "pmg_pe365_p_percent",
            # AOL
            "AOL DEP": "pmg_aol_dep",
            "AOL AC %": "pmg_aol_ac",
            "AOL DECA": "pmg_aol_deca",
            "AOL P %": "pmg_aol_p_percent",
            # Acabamento
            "Acabamento DEP": "pmg_acab_dep",
            "Acabamento AC %": "pmg_acab_ac",
            "Acabamento DECA": "pmg_acab_deca",
            "Acabamento P %": "pmg_acab_p_percent",
            # Marmoreio
            "Marmoreio DEP": "pmg_mar_dep",
            "Marmoreio AC %": "pmg_mar_ac",
            "Marmoreio DECA": "pmg_mar_deca",
            "Marmoreio P %": "pmg_mar_p_percent",
            # Estrutura
            "Estrutura DEP": "pmg_eg_dep",
            "Estrutura AC %": "pmg_eg_ac",
            "Estrutura DECA": "pmg_eg_deca",
            "Estrutura P %": "pmg_eg_p_percent",
            # Precocidade
            "Precocidade DEP": "pmg_p_dep",
            "Precocidade AC %": "pmg_p_ac",
            "Precocidade DECA": "pmg_p_deca",
            "Precocidade P %": "pmg_p_p_percent",
            # Musculosidade
            "Musculosidade DEP": "pmg_m_dep",
            "Musculosidade AC %": "pmg_m_ac",
            "Musculosidade DECA": "pmg_m_deca",
            "Musculosidade P %": "pmg_m_p_percent",
            # Precocidade Sexual
            "Precocidade sexual DEP": "pmg_psn_dep",
            "Precocidade sexual AC %": "pmg_psn_ac",
            "Precocidade sexual DECA": "pmg_psn_deca",
            "Precocidade sexual P %": "pmg_psn_p_percent",
            # Mãe
            "MÃE": "mae_rgn",
            "PAI": "pai_rgn",
            # Additional aliases
            "NOME SERIE / RGD": "nome_serie_rgd",
            "DEP AC %": "pmg_dep_ac",
            "DEP P %": "pmg_dep_pct",
        }
        
        # For CSV files with simple headers (one row), use direct mapping
        # Based on your CSV: NOME, SERIE / RGD, RGN, SEXO, NASC, iABCZg, DECA, P %, F %, etc.
        simple_rename = {
            "NOME": "nome_animal",
            "SERIE / RGD": "pmg_serie_rgd",
            "RGN": "rgn_animal",
            "SEXO": "sexo",
            "NASC": "data_nascimento",
            "iABCZg": "pmg_iabc",
            "DECA": "pmg_deca",
            "P %": "pmg_p_percent",
            "F %": "pmg_f_percent",
            "GENOTIPADO": "genotipado",
            "CSG": "csg",
            "FILHOS": "pmg_filhos",
            "REBANHOS": "pmg_rebanhos",
            "NETOS": "pmg_netos",
            # Additional PMGZ columns (simple format)
            "0,87": "pmg_pn_dep",
            "36": "pmg_pn_ac",
            "10": "pmg_pn_deca",
            "15,42": "pmg_pa_dep",
            "28,64": "pmg_pa_dep",
            "34,80": "pmg_ps_dep",
        }
        
        # Try multiple rename strategies
        new_cols = {}
        for col in df.columns:
            col_str = str(col).strip()
            if col_str in rename_map:
                new_cols[col] = rename_map[col_str]
            elif col_str in simple_rename:
                new_cols[col] = simple_rename[col_str]
            else:
                # Try partial match
                for key, value in rename_map.items():
                    if key.lower() in col_str.lower():
                        new_cols[col] = value
                        break
        
        # Direct column mappings (these should always work)
        direct_mappings = {
            "RGN": "rgn_animal",
            "NOME": "nome_animal",
            "SEXO": "sexo",
            "NASC": "data_nascimento",
            "iABCZg": "pmg_iabc",
            "DECA": "pmg_deca",
            "GENOTIPADO": "genotipado",
            "CSG": "csg",
        }
        
        for old_name, new_name in direct_mappings.items():
            if old_name in df.columns and new_name not in df.columns:
                new_cols[old_name] = new_name
        
        df = df.rename(columns=new_cols)
        
        # Ensure required fields exist
        if "rgn_animal" not in df.columns and "RGN" in df.columns:
            df["rgn_animal"] = df["RGN"]
            
        logger.info(f"_map_pmgz_columns: Mapped columns, final: {list(df.columns)[:30]}")
        
        return df

    def _clean_data(self, df: pd.DataFrame, source_system: str) -> pd.DataFrame:
        """Standardize and clean data fields."""
        if "sexo" in df.columns:
            df["sexo"] = df["sexo"].astype(str).str.upper().str.strip()
            sex_map = {
                "MACHO": "M",
                "FEMEA": "F",
                "FÊMEA": "F",
                "1": "M",
                "2": "F",
                "M": "M",
                "F": "F",
            }
            df["sexo"] = df["sexo"].replace(sex_map)
            df["sexo"] = df["sexo"].apply(
                lambda x: x[0]
                if isinstance(x, str) and len(x) > 0 and x[0] in ["M", "F"]
                else None
            )

        if "data_nascimento" in df.columns:
            df["data_nascimento"] = pd.to_datetime(
                df["data_nascimento"], errors="coerce"
            ).dt.date
        
        # Default race to Nelore if empty
        if "raca" in df.columns:
            df["raca"] = df["raca"].fillna("Nelore")
            df["raca"] = df["raca"].replace(["", "nan", "None", "-"], "Nelore")
        
        if "fonte_origem" not in df.columns:
            df["fonte_origem"] = source_system
        
        logger.info(f"_clean_data: Columns before cleaning: {list(df.columns)}")
        
        # DEBUG: Sample of raw values before conversion
        for col in df.columns:
            sample_vals = df[col].head(2).tolist()
            logger.info(f"_clean_data: {col} sample BEFORE: {sample_vals} (type: {df[col].dtype})")
        
        # First: convert ALL columns to string to handle Brazilian number format (comma decimal)
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].str.replace(",", ".", regex=False)
            df[col] = df[col].replace(["-", "", "nan", "None", "NaN", "nat"], None)

        # Now try to convert each column to appropriate type
        # Only convert columns that should be numeric (weights, DEP scores, etc.)
        float_columns = {"p210_peso_desmama", "p365_peso_ano", "p450_peso_sobreano", "peso_nascimento", "peso_final",
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
                      "pmg_serie_rgd", "pmg_p_percent", "pmg_f_percent",
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
                      "p120_peso_120"}
        
        for col in df.columns:
            if col in float_columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                except:
                    pass
        
        # DEBUG: Sample after conversion
        for col in df.columns:
            sample_vals = df[col].head(2).tolist()
            logger.info(f"_clean_data: {col} sample AFTER: {sample_vals} (type: {df[col].dtype})")
        
        return df

    def _upsert_animals(
        self, df: pd.DataFrame
    ) -> Tuple[int, int, int]:
        """UPSERT animals using BULK operations for performance."""
        inserted = 0
        updated = 0
        failed = 0
        
        logger.info(f"Processing {len(df)} animals with BULK method...")
        logger.info(f"Columns in df: {list(df.columns)[:20]}")
        
        # DEBUG: Show first record
        first_record = df.iloc[0].to_dict()
        logger.info(f"First record sample: rgn={first_record.get('rgn_animal')}, pmg_iabc={first_record.get('pmg_iabc')}, pmg_stay_dep={first_record.get('pmg_stay_dep')}")
        logger.info(f"First record keys: {list(first_record.keys())[:30]}")
        
        # Step 1: Query ALL existing animals at once (1 query, not N)
        existing_animals = self.db.query(Animal).filter(
            Animal.id_farm == self.farm_id
        ).all()
        
        # Create lookup dict: rgn_animal -> Animal object
        existing_map = {a.rgn_animal: a for a in existing_animals}
        logger.info(f"Found {len(existing_map)} existing animals in DB")
        
        # Step 2: Convert dataframe to list of dicts
        records = df.to_dict('records')
        
        # Fix boolean columns: 'SIM'/'NÃO' -> True/False
        for values in records:
            if 'genotipado' in values:
                val = str(values.get('genotipado', '')).upper().strip()
                values['genotipado'] = True if val == 'SIM' else False if val in ['NÃO', 'N', 'NAO', ''] else None
            if 'csg' in values:
                val = str(values.get('csg', '')).upper().strip()
                values['csg'] = True if val == 'SIM' else False if val in ['NÃO', 'N', 'NAO', ''] else None
        
        # Step 3: Process each record
        animals_to_insert = []
        animals_to_update = []
        
        logger.info(f"_upsert_animals: first record keys: {list(records[0].keys())[:20]}")
        
        for values in records:
            # Clean NaN values
            values = {k: (None if pd.isna(v) else v) for k, v in values.items()}
            values["processing_log_id"] = self.upload_log_id
            values["id_farm"] = self.farm_id
            
            # DEBUG: Log the values for first record only
            if updated + inserted == 0:
                logger.info(f"_upsert_animals: sample values: rgn={values.get('rgn_animal')}, pmg_iabc={values.get('pmg_iabc')}, pmg_stay_dep={values.get('pmg_stay_dep')}")
            
            rgn = values.get("rgn_animal")
            if not rgn:
                logger.warning(f"Skipping row - no rgn_animal: {values}")
                failed += 1
                continue
            
            if rgn in existing_map:
                # Update existing
                existing = existing_map[rgn]
                for k, v in values.items():
                    if k not in ("id_animal", "id_farm", "rgn_animal"):
                        setattr(existing, k, v)
                existing.processing_log_id = self.upload_log_id
                updated += 1
            else:
                # Insert new
                animals_to_insert.append(values)
                inserted += 1
        
        # Step 4: Bulk insert new animals
        if animals_to_insert:
            logger.info(f"Bulk inserting {len(animals_to_insert)} new animals...")
            for values in animals_to_insert:
                animal = Animal(**values)
                self.db.add(animal)
        
        # Step 5: Single commit for everything
        try:
            self.db.commit()
            logger.info(f"COMMIT successful - inserted={inserted}, updated={updated}, failed={failed}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"COMMIT failed: {e}")
            failed = inserted + updated
            inserted = 0
            updated = 0
        
        logger.info(f"Done: inserted={inserted}, updated={updated}, failed={failed}")
        return inserted, updated, failed

    def generate_formatted_excel(self, df: pd.DataFrame) -> bytes:
        """Export cleaned DataFrame to formatted Excel."""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Melhora+_Clean")
        return output.getvalue()
