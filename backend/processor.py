import pandas as pd
import io
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models import ColumnMapping, ProcessingLog, Upload, IS_SQLITE, GeneticsAnimal, GeneticsFarm
from backend.loaders import PMGZLoader

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
            col_str = str(col)
            norm = col_str.strip().lower().replace(" ", "_")
            file_lookup[norm] = col_str
            
            parenthetical = re.search(r'\(([^)]+)\)', col_str)
            if parenthetical:
                file_lookup[parenthetical.group(1).lower().strip()] = col_str
                short_code = parenthetical.group(1).lower().strip().replace("-", "")
                if isinstance(file_lookup, dict) and short_code not in file_lookup:
                    file_lookup[short_code] = col_str
            file_lookup[norm] = col_str
            
            col_lower = col_str.lower()
            dep_suffixes = [" dep", " ac %", " deca", " p %"]
            for suffix in dep_suffixes:
                if col_lower.endswith(suffix):
                    base = col_lower[:-len(suffix)].strip()
                    base_underscored = base.replace(" ", "_")
                    if isinstance(file_lookup, dict) and base not in file_lookup:
                        file_lookup[base] = col_str
                    if isinstance(file_lookup, dict) and base_underscored not in file_lookup:
                        file_lookup[base_underscored] = col_str
                    base_with_underscore = base.replace(" ", "_")
                    if isinstance(file_lookup, dict) and base_with_underscore not in file_lookup:
                        file_lookup[base_with_underscore] = col_str

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
        """Process file and persist to genetics schema."""
        logger.info(f"=== START _process_and_persist ===")
        logger.info(f"file_content size: {len(file_content)} bytes")
        logger.info(f"filename: {filename}, source_system: {source_system}")
        
        # Read file
        logger.info(f"Calling _read_file...")
        df = self._read_file(file_content, filename, source_system)
        logger.info(f"After _read_file: {len(df)} rows, {len(df.columns)} columns")
        
        # For PMGZ, use pre-mapped columns
        if source_system == "PMGZ":
            col_map = {}
            required = []
        else:
            col_map = self.get_mappings(source_system)
            required = self.get_required_columns(source_system)
        
        df, rename = self._match_columns(df, col_map, required)
        df = df.rename(columns=rename)
        
        # Clean data
        df = self._clean_data(df, source_system)
        
        # Add id_farm
        df["id_farm"] = self.farm_id
        if self.upload_id:
            df["upload_id"] = self.upload_id
        
        # Save to genetics schema
        logger.info(f"Calling _upsert_genetics_animals with {len(df)} records...")
        inserted, updated, failed = self._upsert_genetics_animals(df, source_system)
        logger.info(f"_upsert_genetics_animals result: inserted={inserted}, updated={updated}, failed={failed}")
        
        return df, inserted, updated, failed

    def _read_file(
        self, file_content: bytes, filename: str, source_system: str
    ) -> pd.DataFrame:
        """Read file into DataFrame. Handles multi-row headers for PMGZ."""
        if filename.endswith((".xlsx", ".xls")):
            if source_system == "PMGZ":
                loader = PMGZLoader(farm_id=self.farm_id)
                df = loader.load(file_content, filename)
                df = loader.para_colunas_banco(df)
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

        df = pd.read_excel(
            io.BytesIO(file_content),
            header=None,
            skiprows=best_row + 1,
        )
        df.columns = composite_names
        
        # Rename PMGZ columns to database field names
        df = self._map_pmgz_columns(df)
        
        logger.info(f"_read_pmgz_excel: Final columns created: {len(df.columns)}, first 15: {composite_names[:15]}")

        return df

    def _map_pmgz_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map PMGZ column names to database field names.
        
        PMGZ Excel has sections: ANIMAL, PAI, MÃE, AVÔ PATERNO, AVÔ MATERNO, AVÔ PATERNO DA MÃE, AVÔ MATERNO DA MÃE.
        Each section has the same sub-columns (NOME, RGN, SERIE/RGD, etc.).
        We map each to UNIQUE column names to avoid pandas duplicate key error.
        """
        
        rename_map = {}
        
        section_map = {
            "ANIMAL": "animal",
            "PAI": "pai", 
            "MÃE": "mae",
            "AVÔ PATERNO": "avo_paterno",
            "AVÔ MATERNO": "avo_materno",
            "AVÔ PATERNO DA MÃE": "avo_paterno_mae",
            "AVÔ MATERNO DA MÃE": "avo_materno_mae",
        }
        
        field_map = {
            "NOME": "nome",
            "RGN": "rgn",
            "SERIE / RGD": "serie_rgd",
        }
        
        for col in df.columns:
            col_str = str(col).strip()
            
            # Match section prefix
            for section_prefix, section_key in section_map.items():
                if col_str.startswith(section_prefix + " "):
                    subcol = col_str[len(section_prefix) + 1:].strip()
                    if subcol in field_map:
                        rename_map[col] = f"{section_key}_{field_map[subcol]}"
                        break
            
            # Animal-level traits (no section prefix)
            if col_str == "ANIMAL NOME":
                rename_map[col] = "nome_animal"
            elif col_str == "ANIMAL SERIE / RGD":
                rename_map[col] = "pmg_serie_rgd"
            elif col_str == "ANIMAL RGN":
                rename_map[col] = "rgn_animal"
            elif col_str == "ANIMAL SEXO":
                rename_map[col] = "sexo"
            elif col_str == "ANIMAL NASC":
                rename_map[col] = "data_nascimento"
            elif "iABCZg" in col_str:
                rename_map[col] = "pmg_iabc"
            elif "DECA" in col_str:
                rename_map[col] = "pmg_deca"
            elif "P %" in col_str:
                rename_map[col] = "pmg_p_percent"
            elif "F %" in col_str:
                rename_map[col] = "pmg_f_percent"
            elif "GENOTIPADO" in col_str:
                rename_map[col] = "genotipado"
            elif "CSG" in col_str:
                rename_map[col] = "csg"
            elif "FILHOS" in col_str:
                rename_map[col] = "pmg_filhos"
            elif "REBANHOS" in col_str:
                rename_map[col] = "pmg_rebanhos"
            elif "NETOS" in col_str:
                rename_map[col] = "pmg_netos"
            elif "Peso ao nascimento" in col_str or "PN-EDg" in col_str:
                if "DEP" in col_str:
                    rename_map[col] = "pmg_pn_dep"
                elif "AC %" in col_str:
                    rename_map[col] = "pmg_pn_ac"
                elif "DECA" in col_str:
                    rename_map[col] = "pmg_pn_deca"
                elif "P %" in col_str:
                    rename_map[col] = "pmg_pn_p_percent"
            elif "P210" in col_str or "Peso à desmama" in col_str or "PD-EDg" in col_str:
                if "DEP" in col_str:
                    rename_map[col] = "pmg_pd_dep"
                elif "AC %" in col_str:
                    rename_map[col] = "pmg_pd_ac"
                elif "DECA" in col_str:
                    rename_map[col] = "pmg_pd_deca"
                elif "P %" in col_str:
                    rename_map[col] = "pmg_pd_p_percent"
            elif "Peso ao ano" in col_str or "P365" in col_str or "PA-EDg" in col_str:
                if "DEP" in col_str:
                    rename_map[col] = "pmg_pa_dep"
                elif "AC %" in col_str:
                    rename_map[col] = "pmg_pa_ac"
                elif "DECA" in col_str:
                    rename_map[col] = "pmg_pa_deca"
                elif "P %" in col_str:
                    rename_map[col] = "pmg_pa_p_percent"
            elif "Peso ao sobreano" in col_str or "P450" in col_str or "PS-EDg" in col_str:
                if "DEP" in col_str:
                    rename_map[col] = "pmg_ps_dep"
                elif "AC %" in col_str:
                    rename_map[col] = "pmg_ps_ac"
                elif "DECA" in col_str:
                    rename_map[col] = "pmg_ps_deca"
                elif "P %" in col_str:
                    rename_map[col] = "pmg_ps_p_percent"
            elif "Peso maternal" in col_str or "PM-EMg" in col_str:
                if "DEP" in col_str:
                    rename_map[col] = "pmg_pm_dep"
                elif "AC %" in col_str:
                    rename_map[col] = "pmg_pm_ac"
                elif "DECA" in col_str:
                    rename_map[col] = "pmg_pm_deca"
                elif "P %" in col_str:
                    rename_map[col] = "pmg_pm_p_percent"
            elif "Idade ao primeiro parto" in col_str or "IPPg" in col_str:
                if "DEP" in col_str:
                    rename_map[col] = "pmg_ipp_dep"
                elif "AC %" in col_str:
                    rename_map[col] = "pmg_ipp_ac"
                elif "DECA" in col_str:
                    rename_map[col] = "pmg_ipp_deca"
                elif "P %" in col_str:
                    rename_map[col] = "pmg_ipp_p_percent"
            elif "Stayability" in col_str or "STAYg" in col_str:
                if "DEP" in col_str:
                    rename_map[col] = "pmg_stay_dep"
                elif "AC %" in col_str:
                    rename_map[col] = "pmg_stay_ac"
                elif "DECA" in col_str:
                    rename_map[col] = "pmg_stay_deca"
                elif "P %" in col_str:
                    rename_map[col] = "pmg_stay_p_percent"
            elif "PE-365" in col_str or "Perímetro escrotal" in col_str or "PE-365g" in col_str:
                if "DEP" in col_str:
                    rename_map[col] = "pmg_pe365_dep"
                elif "AC %" in col_str:
                    rename_map[col] = "pmg_pe365_ac"
                elif "DECA" in col_str:
                    rename_map[col] = "pmg_pe365_deca"
                elif "P %" in col_str:
                    rename_map[col] = "pmg_pe365_p_percent"
            elif "AOL" in col_str or "Área de olho" in col_str or "AOLg" in col_str:
                if "DEP" in col_str:
                    rename_map[col] = "pmg_aol_dep"
                elif "AC %" in col_str:
                    rename_map[col] = "pmg_aol_ac"
                elif "DECA" in col_str:
                    rename_map[col] = "pmg_aol_deca"
                elif "P %" in col_str:
                    rename_map[col] = "pmg_aol_p_percent"
            elif "Acabamento" in col_str or "ACABg" in col_str:
                if "DEP" in col_str:
                    rename_map[col] = "pmg_acab_dep"
                elif "AC %" in col_str:
                    rename_map[col] = "pmg_acab_ac"
                elif "DECA" in col_str:
                    rename_map[col] = "pmg_acab_deca"
                elif "P %" in col_str:
                    rename_map[col] = "pmg_acab_p_percent"
            elif "Marmoreio" in col_str:
                if "DEP" in col_str:
                    rename_map[col] = "pmg_mar_dep"
                elif "AC %" in col_str:
                    rename_map[col] = "pmg_mar_ac"
                elif "DECA" in col_str:
                    rename_map[col] = "pmg_mar_deca"
                elif "P %" in col_str:
                    rename_map[col] = "pmg_mar_p_percent"
            elif "Estrutura" in col_str:
                if "DEP" in col_str:
                    rename_map[col] = "pmg_eg_dep"
                elif "AC %" in col_str:
                    rename_map[col] = "pmg_eg_ac"
                elif "DECA" in col_str:
                    rename_map[col] = "pmg_eg_deca"
                elif "P %" in col_str:
                    rename_map[col] = "pmg_eg_p_percent"
            elif "Precocidade sexual" in col_str or "PSNg" in col_str:
                if "DEP" in col_str:
                    rename_map[col] = "pmg_psn_dep"
                elif "AC %" in col_str:
                    rename_map[col] = "pmg_psn_ac"
                elif "DECA" in col_str:
                    rename_map[col] = "pmg_psn_deca"
                elif "P %" in col_str:
                    rename_map[col] = "pmg_psn_p_percent"
        
        df = df.rename(columns=rename_map)
        
        # Remove duplicate columns (keep first occurrence) - CRITICAL to avoid pandas error
        seen = set()
        unique_cols = []
        for col in df.columns:
            col_str = str(col)
            if col_str not in seen:
                unique_cols.append(col_str)
                seen.add(col_str)
        if len(unique_cols) < len(df.columns):
            logger.info(f"Deduplicating columns: {len(df.columns)} -> {len(unique_cols)}")
            df = df[unique_cols]
        
        logger.info(f"_map_pmgz_columns: Mapped {len(rename_map)} columns, final: {list(df.columns)[:30]}")
        
        return df
        
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
            old_str = str(old_name)
            new_str = str(new_name)
            if old_str in df.columns and new_str not in df.columns:
                new_cols[old_str] = new_str
        
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
        
        fonte_str = str("fonte_origem")
        if fonte_str not in df.columns:
            df["fonte_origem"] = source_system
        
        logger.info(f"_clean_data: Columns before cleaning: {list(df.columns)}")
        
        # DEBUG: Sample of raw values before conversion
        for col in list(df.columns)[:10]:
            try:
                sample_vals = df[col].head(2).astype(str).tolist()
                logger.info(f"_clean_data: {col} sample BEFORE: {sample_vals} (type: {df[col].dtype})")
            except Exception as e:
                logger.info(f"_clean_data: {col} sample BEFORE: <error: {e}>")
        
        # First: convert ALL columns to string to handle Brazilian number format (comma decimal)
        for col in df.columns:
            col_dtype = df[col].dtype
            # Skip if column is a DataFrame (duplicate column issue)
            if hasattr(col_dtype, 'dtype'):
                continue
        
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

    def _upsert_genetics_animals(self, df: pd.DataFrame, source_system: str) -> Tuple[int, int, int]:
        """Upsert animals directly into genetics schema using raw SQL."""
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

    def _upsert_genetics_animals(self, df: pd.DataFrame, source_system: str) -> Tuple[int, int, int]:
        """Upsert animals directly into genetics schema using raw SQL."""
        from sqlalchemy import text
        import uuid
        import json
        
        inserted = 0
        updated = 0
        failed = 0
        
        # Map farm_id (silver) to genetics farm
        farm = self.db.query(GeneticsFarm).first()
        if not farm:
            logger.error("No farm found in genetics.farms")
            return 0, 0, len(df)
        
        genetics_farm_id = farm.id
        
        for _, row in df.iterrows():
            try:
                rgn = row.get('rgn_animal')
                if not rgn:
                    failed += 1
                    continue
                
                # Check if animal exists
                existing = self.db.query(GeneticsAnimal).filter(
                    GeneticsAnimal.rgn == rgn,
                    GeneticsAnimal.farm_id == genetics_farm_id
                ).first()
                
                animal_id = existing.id if existing else uuid.uuid4()
                
                # Build animal data
                animal_data = {
                    'id': str(animal_id),
                    'farm_id': str(genetics_farm_id),
                    'rgn': str(rgn),
                    'nome': row.get('nome_animal'),
                    'serie': row.get('serie'),
                    'sexo': row.get('sexo'),
                    'nascimento': row.get('data_nascimento').isoformat() if row.get('data_nacimiento') else None,
                    'genotipado': True if str(row.get('genotipado', '')).upper() == 'SIM' else False,
                    'csg': True if str(row.get('csg', '')).upper() == 'SIM' else False,
                }
                
                if existing:
                    self.db.execute(
                        text("""
                            UPDATE genetics.animals 
                            SET nome = :nome, serie = :serie, sexo = :sexo, 
                                nascimento = :nascimento, genotipado = :genotipado, csg = :csg
                            WHERE id = :id
                        """),
                        animal_data
                    )
                    updated += 1
                else:
                    self.db.execute(
                        text("""
                            INSERT INTO genetics.animals (id, farm_id, rgn, nome, serie, sexo, nascimento, genotipado, csg)
                            VALUES (:id, :farm_id, :rgn, :nome, :serie, :sexo, :nascimento, :genotipado, :csg)
                        """),
                        animal_data
                    )
                    inserted += 1
                
                # Now insert genetic evaluation if we have DEP data
                if row.get('pmg_iabc'):
                    eval_data = {
                        'id': str(uuid.uuid4()),
                        'animal_id': str(animal_id),
                        'farm_id': str(genetics_farm_id),
                        'safra': 2026,
                        'fonte_origem': source_system,
                        'iabczg': float(row.get('pmg_iabc', 0)) if row.get('pmg_iabc') else None,
                        'pn_ed': json.dumps({'dep': row.get('pmg_pn_dep'), 'ac': row.get('pmg_pn_ac'), 'deca': row.get('pmg_pn_deca'), 'p_percent': row.get('pmg_pn_p_percent')}),
                        'pd_ed': json.dumps({'dep': row.get('pmg_pd_dep'), 'ac': row.get('pmg_pd_ac'), 'deca': row.get('pmg_pd_deca'), 'p_percent': row.get('pmg_pd_p_percent')}),
                        'ps_ed': json.dumps({'dep': row.get('pmg_ps_dep'), 'ac': row.get('pmg_ps_ac'), 'deca': row.get('pmg_ps_deca'), 'p_percent': row.get('pmg_ps_p_percent')}),
                    }
                    
                    self.db.execute(
                        text("""
                            INSERT INTO genetics.genetic_evaluations 
                            (id, animal_id, farm_id, safra, fonte_origem, iabczg, pn_ed, pd_ed, ps_ed)
                            VALUES (:id, :animal_id, :farm_id, :safra, :fonte_origem, :iabczg, :pn_ed, :pd_ed, :ps_ed)
                            ON CONFLICT (id) DO UPDATE SET
                            iabczg = EXCLUDED.iabczg, pn_ed = EXCLUDED.pn_ed, pd_ed = EXCLUDED.pd_ed, ps_ed = EXCLUDED.ps_ed
                        """),
                        eval_data
                    )
                
                self.db.commit()
                
            except Exception as e:
                self.db.rollback()
                logger.error(f"Error processing animal {rgn}: {e}")
                failed += 1
        
        logger.info(f"Genetics upsert: inserted={inserted}, updated={updated}, failed={failed}")
        return inserted, updated, failed

    def generate_formatted_excel(self, df: pd.DataFrame) -> bytes:
        """Export cleaned DataFrame to formatted Excel."""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Melhora+_Clean")
        return output.getvalue()
