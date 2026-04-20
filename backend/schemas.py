from pydantic import BaseModel, Field, EmailStr
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
    anc_mg: Optional[float] = None
    anc_te: Optional[float] = None
    anc_m: Optional[float] = None
    anc_p: Optional[float] = None
    anc_dp: Optional[float] = None
    anc_sp: Optional[float] = None
    anc_e: Optional[float] = None
    anc_sao: Optional[float] = None
    anc_leg: Optional[float] = None
    anc_sh: Optional[float] = None
    anc_pp30: Optional[float] = None
    gen_iqg: Optional[float] = None
    gen_pmm: Optional[float] = None
    gen_p: Optional[float] = None
    gen_dp: Optional[float] = None
    gen_sp: Optional[float] = None
    gen_e: Optional[float] = None
    gen_sao: Optional[float] = None
    gen_leg: Optional[float] = None
    gen_sh: Optional[float] = None
    gen_pp30: Optional[float] = None
    pmg_iabc: Optional[float] = None
    pmg_zpmm: Optional[float] = None
    pmg_p: Optional[float] = None
    pmg_dp: Optional[float] = None
    pmg_sp: Optional[float] = None
    pmg_e: Optional[float] = None
    pmg_sao: Optional[float] = None
    pmg_leg: Optional[float] = None
    pmg_sh: Optional[float] = None
    pmg_pp30: Optional[float] = None

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


class ColumnMappingUpdate(BaseModel):
    source_system: Optional[str] = Field(None, min_length=1, max_length=50)
    source_column: Optional[str] = Field(None, min_length=1, max_length=100)
    target_column: Optional[str] = Field(None, min_length=1, max_length=100)
    data_type: Optional[str] = Field(None)
    is_required: Optional[bool] = None


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


# ============================================
# User / Auth Schemas
# ============================================
class UserCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    senha: str = Field(..., min_length=6, max_length=128)
    id_farm: Optional[int] = None
    role: Optional[str] = "user"


class UserLogin(BaseModel):
    email: EmailStr
    senha: str


class UserResponse(BaseModel):
    id: int
    nome: str
    email: str
    id_farm: Optional[int]
    role: str
    ativo: bool
    ultimo_login: Optional[datetime]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    senha_atual: str
    senha_nova: str = Field(..., min_length=6, max_length=128)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ============================================
# Report Schemas
# ============================================
class ReportJobResponse(BaseModel):
    id: int
    id_farm: Optional[int]
    report_type: str
    status: str
    file_path: Optional[str]
    parameters: Optional[dict]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class ReportHistoryItem(BaseModel):
    id: int
    report_type: str
    status: str
    created_at: Optional[datetime]
    file_name: Optional[str]
    parameters: Optional[dict]

    class Config:
        from_attributes = True


class UploadDetailResponse(BaseModel):
    log: ProcessingLogResponse
    animals_preview: list[AnimalResponse]
    total_count: int


class NotificationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    type: str = Field(default="info")
    link: Optional[str] = None


class NotificationResponse(BaseModel):
    id: int
    id_user: int
    title: str
    message: str
    type: str
    is_read: bool
    link: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
