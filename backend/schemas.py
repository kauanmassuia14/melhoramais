from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


# ============================================
# Farm Schemas
# ============================================
class FarmCreate(BaseModel):
    nome_farm: str = Field(..., min_length=1, max_length=255)
    cnpj: Optional[str] = None
    responsavel: Optional[str] = None
    email: Optional[str] = None


class FarmResponse(BaseModel):
    id_farm: int
    nome_farm: str
    cnpj: Optional[str]
    responsavel: Optional[str]
    email: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================
# Animal Schemas
# ============================================
class AnimalResponse(BaseModel):
    id_animal: int
    id_farm: int
    rgn_animal: str
    nome_animal: Optional[str]
    raca: Optional[str]
    sexo: Optional[str]
    data_nascimento: Optional[date]
    mae_rgn: Optional[str]
    pai_rgn: Optional[str]
    p210_peso_desmama: Optional[float]
    p365_peso_ano: Optional[float]
    p450_peso_sobreano: Optional[float]
    pe_perimetro_escrotal: Optional[float]
    a_area_olho_lombo: Optional[float]
    eg_espessura_gordura: Optional[float]
    im_idade_primeiro_parto: Optional[float]
    fonte_origem: Optional[str]
    data_processamento: Optional[datetime]

    class Config:
        from_attributes = True


class AnimalFilter(BaseModel):
    farm_id: Optional[int] = None
    source: Optional[str] = None
    raca: Optional[str] = None
    sexo: Optional[str] = None
    search: Optional[str] = None  # search by rgn or nome
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


# ============================================
# Column Mapping Schemas
# ============================================
class ColumnMappingCreate(BaseModel):
    source_system: str = Field(..., min_length=1, max_length=50)
    source_column: str = Field(..., min_length=1, max_length=100)
    target_column: str = Field(..., min_length=1, max_length=100)
    data_type: str = Field(default="float")
    is_required: bool = False


class ColumnMappingResponse(BaseModel):
    id: int
    source_system: str
    source_column: str
    target_column: str
    data_type: str
    is_required: bool

    class Config:
        from_attributes = True


# ============================================
# Processing Log Schemas
# ============================================
class ProcessingLogResponse(BaseModel):
    id: int
    id_farm: int
    source_system: str
    filename: Optional[str]
    total_rows: int
    rows_inserted: int
    rows_updated: int
    rows_failed: int
    status: str
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================
# Processing Result (returned after upload)
# ============================================
class ProcessingResult(BaseModel):
    log_id: int
    source_system: str
    total_rows: int
    rows_inserted: int
    rows_updated: int
    rows_failed: int
    status: str


# ============================================
# Stats / Dashboard
# ============================================
class DashboardStats(BaseModel):
    total_animals: int
    total_farms: int
    animals_by_source: dict[str, int]
    animals_by_sex: dict[str, int]
    recent_uploads: int  # last 30 days
    avg_p210: Optional[float]
    avg_p365: Optional[float]
    avg_p450: Optional[float]


class ReportRequest(BaseModel):
    farm_id: Optional[int] = None
    source_system: Optional[str] = None
    raca: Optional[str] = None
