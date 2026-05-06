from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class BaseLoader(ABC):
    """Classe abstrata base para loaders de dados genéticos."""

    def __init__(self, farm_id: int = 1):
        self.farm_id = farm_id

    @abstractmethod
    def load(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Lê o arquivo e retorna DataFrame processado."""
        pass

    def _detectar_separador(self, content: bytes) -> str:
        """Detecta o separador do arquivo CSV."""
        sample = content[:500].decode('utf-8', errors='ignore')
        if '\t' in sample:
            return '\t'
        if ';' in sample:
            return ';'
        return ','

    def _converter_numero_brasileiro(self, valor: Any) -> float | None:
        """Converte número no formato brasileiro (1.234,56) para float."""
        if pd.isna(valor):
            return None

        s = str(valor).strip()
        if s in ['-', '', 'nan', 'None', 'NaN']:
            return None

        s = s.replace('.', '').replace(',', '.')

        try:
            return float(s)
        except (ValueError, TypeError):
            return None

    def _converter_data(self, valor: Any) -> Any:
        """Converte data para formato adequado."""
        if pd.isna(valor):
            return None

        s = str(valor).strip()
        if s in ['-', '', 'nan', 'None']:
            return None

        try:
            return pd.to_datetime(valor, dayfirst=True).date()
        except:
            return None

    def _converter_booleanos(self, df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
        """Converte colunas SIM/NÃO para booleanos."""
        for col in colunas:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: True if str(x).upper().strip() == 'SIM'
                    else (False if str(x).upper().strip() in ['NÃO', 'NAO', 'N', 'NÃO']
                    else None)
                )
        return df

    def _aplicar_tipos_numericos(self, df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
        """Converte colunas específicas para float."""
        for col in colunas:
            if col in df.columns:
                df[col] = df[col].apply(self._converter_numero_brasileiro)
        return df

    def _aplicar_tipos_inteiros(self, df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
        """Converte colunas específicas para inteiro."""
        for col in colunas:
            if col in df.columns:
                df[col] = df[col].apply(self._converter_numero_brasileiro)
                df[col] = df[col].astype('Int64')
        return df