import pandas as pd
import io
from typing import Dict, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.models import ColumnMapping, Animal, ProcessingLog, IS_SQLITE


class GeneticDataProcessor:
    def __init__(self, db: Session, farm_id: int = 1):
        self.db = db
        self.farm_id = farm_id

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
        """
        # Build lookup: normalized_name -> actual column name in file
        file_lookup: Dict[str, str] = {}
        for col in df.columns:
            # normalize: lowercase, strip, replace spaces with _
            norm = str(col).strip().lower().replace(" ", "_")
            # Also keep the pandas-suffixed version as-is (e.g. "rgn.1")
            file_lookup[norm] = col

        # Build rename dict: actual_file_col -> target_db_col
        rename: Dict[str, str] = {}
        missing: List[str] = []

        for source_col, target_col in col_map.items():
            norm_source = source_col.strip().lower().replace(" ", "_")
            actual = file_lookup.get(norm_source)

            if actual is not None:
                rename[actual] = target_col
            elif source_col in required:
                missing.append(source_col)

        if missing:
            available = list(df.columns)
            raise ValueError(
                f"Required columns missing for mapping: {missing}\n"
                f"Columns found in file: {available}\n"
                f"Tip: check the column names in your Excel file match the mapping."
            )

        return df, rename

    def process_file(
        self, file_content: bytes, filename: str, source_system: str
    ) -> Tuple[pd.DataFrame, ProcessingLog]:
        """Full pipeline: read → map → clean → persist.
        
        Uses two separate transactions:
        1. First creates the ProcessingLog entry (committed immediately)
        2. Then processes and upserts animals (committed separately)
        
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
            self.db.commit()
            return df, log

        except Exception as e:
            # Rollback failed animal transaction
            self.db.rollback()
            
            # Transaction 3: Update log status in a FRESH session
            # This avoids the 'transaction aborted' state entirely
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
        df = self._read_file(file_content, filename, source_system)
        col_map = self.get_mappings(source_system)
        required = self.get_required_columns(source_system)
        df, rename = self._match_columns(df, col_map, required)
        df = df.rename(columns=rename)
        valid_targets = set(Animal.__table__.columns.keys())
        keep = [c for c in df.columns if c in valid_targets]
        df = df[keep]
        df = self._clean_data(df, source_system)
        df["id_farm"] = self.farm_id
        inserted, updated, failed = self._upsert_animals(df)
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
        PMGZ Excel files have multiple header rows before the real column names.
        Auto-detects header row by finding the row that contains the most
        known column names (RGN, NOME, SEXO, NASC, etc.).
        """
        # Read raw first 20 rows (no header)
        raw = pd.read_excel(
            io.BytesIO(file_content), header=None, nrows=20
        )

        # Known header indicators for PMGZ files
        header_keywords = {"RGN", "NOME", "SEXO", "NASC", "SERIE", "DECA", "iABCZg", "DEP", "FILHOS"}

        # Score each row: how many header keywords does it contain?
        best_row = None
        best_score = 0

        for i, row in raw.iterrows():
            score = 0
            for val in row.values:
                val_str = str(val).strip().upper()
                if val_str in header_keywords:
                    score += 1
            if score > best_score:
                best_score = score
                best_row = i

        if best_row is None or best_score < 2:
            raise ValueError(
                "Could not find header row in PMGZ file. "
                f"Scanned {len(raw)} rows, best score was {best_score}. "
                "Expected row with column names like RGN, NOME, SEXO, NASC."
            )

        # Read using the detected header row
        # Use header=None + skiprows to get exact control
        df = pd.read_excel(
            io.BytesIO(file_content),
            header=None,
            skiprows=best_row + 1,  # skip everything up to and including header_row
        )
        # Set the skipped row as column names
        header_names = raw.loc[best_row].values
        # Ensure unique column names (handle duplicates from pandas)
        seen = {}
        unique_names = []
        for name in header_names:
            name_str = str(name).strip() if pd.notna(name) else "Unnamed"
            if name_str in seen:
                seen[name_str] += 1
                unique_names.append(f"{name_str}.{seen[name_str] - 1}")
            else:
                seen[name_str] = 0
                unique_names.append(name_str)
        df.columns = unique_names

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

        if "fonte_origem" not in df.columns:
            df["fonte_origem"] = source_system

        return df

    def _upsert_animals(
        self, df: pd.DataFrame
    ) -> Tuple[int, int, int]:
        """UPSERT animals. Returns (inserted, updated, failed).
        
        Uses nested transactions (SAVEPOINT) per row to prevent
        transaction abortion when individual rows fail.
        """
        inserted = 0
        updated = 0
        failed = 0

        if not IS_SQLITE:
            for _, row in df.iterrows():
                # Create a savepoint for this row
                nested = self.db.begin_nested()
                try:
                    values = row.to_dict()
                    values = {
                        k: (None if pd.isna(v) else v) for k, v in values.items()
                    }

                    stmt = pg_insert(Animal.__table__).values(**values)
                    stmt = stmt.on_conflict_do_update(
                        constraint="uix_farm_rgn",
                        set_={
                            k: stmt.excluded[k]
                            for k in values
                            if k not in ("id_animal", "id_farm", "rgn_animal")
                        },
                    )
                    self.db.execute(stmt)
                    nested.commit()
                    inserted += 1
                except Exception:
                    nested.rollback()
                    failed += 1
        else:
            for _, row in df.iterrows():
                nested = self.db.begin_nested()
                try:
                    values = row.to_dict()
                    values = {
                        k: (None if pd.isna(v) else v) for k, v in values.items()
                    }

                    existing = (
                        self.db.query(Animal)
                        .filter(
                            Animal.id_farm == self.farm_id,
                            Animal.rgn_animal == values.get("rgn_animal"),
                        )
                        .first()
                    )

                    if existing:
                        for k, v in values.items():
                            if k not in ("id_animal", "id_farm", "rgn_animal"):
                                setattr(existing, k, v)
                        updated += 1
                    else:
                        animal = Animal(**values)
                        self.db.add(animal)
                        inserted += 1
                    nested.commit()
                except Exception:
                    nested.rollback()
                    failed += 1

        return inserted, updated, failed

    def generate_formatted_excel(self, df: pd.DataFrame) -> bytes:
        """Export cleaned DataFrame to formatted Excel."""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Melhora+_Clean")
        return output.getvalue()
