import pandas as pd
import io
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from backend.models import ColumnMapping, Animal  # IMPORT ABSOLUTO

class GeneticDataProcessor:
    def __init__(self, db: Session):
        self.db = db

    def get_mappings(self, source_system: str) -> Dict[str, str]:
        """Fetch column mappings from the database for a specific source system."""
        mappings = self.db.query(ColumnMapping).filter(
            ColumnMapping.source_system == source_system
        ).all()
        return {m.source_column: m.target_column for m in mappings}

    def process_file(self, file_content: bytes, filename: str, source_system: str) -> pd.DataFrame:
        """
        Main pipeline:
        1. Read file into Pandas
        2. Apply dynamic mapping
        3. Clean data
        4. Standardize types
        """
        # 1. Read file
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_content))
        elif filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith('.PAG'):
            # Basic .PAG parsing (assuming space-separated or fixed-width)
            # This is a placeholder for real .PAG logic which is format-dependent
            df = pd.read_csv(io.BytesIO(file_content), sep=None, engine='python')
        else:
            raise ValueError("Unsupported file format")

        # 2. Fetch and apply mappings
        col_map = self.get_mappings(source_system)
        
        # Rename only columns that exist in the mapping
        df = df.rename(columns=col_map)
        
        # Keep only the target columns that exist in our Master Table
        valid_columns = [col for col in df.columns if col in Animal.__table__.columns.keys()]
        df = df[valid_columns]

        # 3. Data Cleaning & Standardizing
        if 'sexo' in df.columns:
            # Standardize sex to 'M' or 'F'
            df['sexo'] = df['sexo'].astype(str).str.upper().str.strip()
            # Mapping common variations
            sex_map = {'MACHO': 'M', 'FEMEA': 'F', 'FÊMEA': 'F', '1': 'M', '2': 'F'}
            df['sexo'] = df['sexo'].replace(sex_map)
            df['sexo'] = df['sexo'].apply(lambda x: x[0] if len(x) > 0 and x[0] in ['M', 'F'] else None)

        if 'data_nascimento' in df.columns:
            df['data_nascimento'] = pd.to_datetime(df['data_nascimento'], errors='coerce')

        # Add Source tagging
        df['fonte_origem'] = source_system
        
        return df

    def generate_formatted_excel(self, df: pd.DataFrame) -> bytes:
        """Export the cleaned dataframe to a nicely formatted Excel file."""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Cattle_Genetics_Clean')
            # Here we could add auto-filtering, column width adjustment, etc.
        return output.getvalue()
