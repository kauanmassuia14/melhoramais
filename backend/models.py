from sqlalchemy import Column, Integer, String, Float, Date, CHAR, DateTime, UniqueConstraint
import os
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Identificamos que você está usando schemas diferentes para cada tabela
# Dados de produção vão para 'silver' e configurações de mapeamento para 'config'
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
IS_SQLITE = DB_URL.startswith("sqlite")

Base = declarative_base()

class Animal(Base):
    __tablename__ = "animais"
    __table_args__ = ({"schema": "silver"} if not IS_SQLITE else {})

    id_animal = Column(Integer, primary_key=True, index=True)
    rgn_animal = Column(String(50), unique=True, nullable=False)
    nome_animal = Column(String(255))
    raca = Column(String(50))
    sexo = Column(String(1))
    data_nascimento = Column(Date)
    mae_rgn = Column(String(50))
    pai_rgn = Column(String(50))
    
    # Índices Genéticos (Padronizados)
    p210_peso_desmama = Column(Float)
    p365_peso_ano = Column(Float)
    p450_peso_sobreano = Column(Float)
    pe_perimetro_escrotal = Column(Float)
    a_area_olho_lombo = Column(Float)
    eg_espessura_gordura = Column(Float)
    im_idade_primeiro_parto = Column(Float)
    
    fonte_origem = Column(String(50))
    data_processamento = Column(DateTime, default=datetime.utcnow)

class ColumnMapping(Base):
    __tablename__ = "column_mapping"
    __table_args__ = (
        UniqueConstraint("source_system", "source_column", name="uix_source_system_column"),
        {"schema": "config"} if not IS_SQLITE else {}
    )

    id = Column(Integer, primary_key=True, index=True)
    source_system = Column(String(50), nullable=False)
    source_column = Column(String(100), nullable=False)
    target_column = Column(String(100), nullable=False)
    data_type = Column(String(20), default="float")
