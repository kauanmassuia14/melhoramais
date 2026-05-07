from pydantic import BaseModel, Field, EmailStr, field_validator
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


class FarmUpdate(BaseModel):
    nome_farm: Optional[str] = Field(None, min_length=1, max_length=255)
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
    upload_id: Optional[str] = None
    rgn_animal: str
    nome_animal: Optional[str] = None
    raca: Optional[str] = None
    sexo: Optional[str] = None
    data_nascimento: Optional[date] = None
    
    # Genealogy - 1ª geração
    mae_rgn: Optional[str] = None
    pai_rgn: Optional[str] = None
    
    # Genealogy - 2ª geração
    avo_paterno_rgn: Optional[str] = None
    avo_paterno_mae_rgn: Optional[str] = None
    avo_materno_rgn: Optional[str] = None
    avo_materno_mae_rgn: Optional[str] = None
    
    # Genealogy - 3ª geração
    bisavo_paterno_pai_rgn: Optional[str] = None
    bisavo_paterno_mae_pai_rgn: Optional[str] = None
    bisavo_materno_pai_rgn: Optional[str] = None
    bisavo_materno_mae_pai_rgn: Optional[str] = None
    bisavo_paterno_mae_rgn: Optional[str] = None
    bisavo_paterno_mae_mae_rgn: Optional[str] = None
    bisavo_materno_mae_rgn: Optional[str] = None
    bisavo_materno_mae_mae_rgn: Optional[str] = None
    
    # Genealogy - 4ª geração
    trisavo_paterno_pai_rgn: Optional[str] = None
    trisavo_paterno_mae_pai_rgn: Optional[str] = None
    trisavo_materno_pai_rgn: Optional[str] = None
    trisavo_materno_mae_pai_rgn: Optional[str] = None
    trisavo_paterno_mae_rgn: Optional[str] = None
    trisavo_paterno_mae_mae_rgn: Optional[str] = None
    trisavo_materno_mae_rgn: Optional[str] = None
    trisavo_materno_mae_mae_rgn: Optional[str] = None
    
    # Pesos
    peso_nascimento: Optional[float] = None
    p210_peso_desmama: Optional[float] = None
    p365_peso_ano: Optional[float] = None
    p450_peso_sobreano: Optional[float] = None
    peso_final: Optional[float] = None
    
    # Medidas
    pe_perimetro_escrotal: Optional[float] = None
    a_area_olho_lombo: Optional[float] = None
    eg_espessura_gordura: Optional[float] = None
    altura: Optional[float] = None
    circumference: Optional[float] = None
    
    # Reprodução
    im_idade_primeiro_parto: Optional[float] = None
    intervalo_partos: Optional[float] = None
    dias_gestacao: Optional[float] = None
    
    # ANCP - Benchmarking
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
    
    # ANCP - DEP Individuais
    anc_dipp: Optional[float] = None
    anc_d3p: Optional[float] = None
    anc_dstay: Optional[float] = None
    anc_dpn: Optional[float] = None
    anc_dp12: Optional[float] = None
    anc_dpe: Optional[float] = None
    anc_daol: Optional[float] = None
    anc_dacab: Optional[float] = None
    
    # ANCP - AC
    anc_ac_mg: Optional[float] = None
    anc_ac_te: Optional[float] = None
    anc_ac_m: Optional[float] = None
    anc_ac_p: Optional[float] = None
    
    # GENEPLUS - Benchmarking
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
    
    # GENEPLUS - DEP Individuais
    gen_pn: Optional[float] = None
    gen_p120: Optional[float] = None
    gen_tmd: Optional[float] = None
    gen_pd: Optional[float] = None
    gen_tm120: Optional[float] = None
    gen_ps: Optional[float] = None
    gen_gpd: Optional[float] = None
    gen_cfd: Optional[float] = None
    gen_cfs: Optional[float] = None
    gen_hp_stay: Optional[float] = None
    gen_rd: Optional[float] = None
    gen_egs: Optional[float] = None
    gen_acab: Optional[float] = None
    gen_mar: Optional[float] = None
    
    # GENEPLUS - AC
    gen_ac_iqg: Optional[float] = None
    gen_ac_pmm: Optional[float] = None
    gen_ac_p: Optional[float] = None
    
    # PMGZ - Benchmarking
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
    
    # PMGZ - DEP Individuais
    pmg_pn: Optional[float] = None
    pmg_pa: Optional[float] = None
    pmg_ps: Optional[float] = None
    pmg_pm: Optional[float] = None
    pmg_ipp: Optional[float] = None
    pmg_stay: Optional[float] = None
    pmg_pe: Optional[float] = None
    pmg_aol: Optional[float] = None
    pmg_acab: Optional[float] = None
    pmg_mar: Optional[float] = None
    
    # PMGZ - DECA
    pmg_deca: Optional[str] = None
    pmg_deca_pn: Optional[str] = None
    pmg_deca_p12: Optional[str] = None
    pmg_deca_ps: Optional[str] = None
    pmg_deca_stay: Optional[str] = None
    pmg_deca_pe: Optional[str] = None
    pmg_deca_aol: Optional[str] = None
    
    # PMGZ - Metas
    pmg_meta_p: Optional[float] = None
    pmg_meta_m: Optional[float] = None
    pmg_meta_t: Optional[float] = None
    
    # PMGZ - DEP (Direct Predicted)
    pmg_pn_dep: Optional[float] = None
    pmg_pn_ac: Optional[int] = None
    pmg_pn_deca: Optional[str] = None
    pmg_pn_p_percent: Optional[float] = None
    pmg_pd_dep: Optional[float] = None
    pmg_pd_ac: Optional[int] = None
    pmg_pd_deca: Optional[str] = None
    pmg_pd_p_percent: Optional[float] = None
    pmg_pa_dep: Optional[float] = None
    pmg_pa_ac: Optional[int] = None
    pmg_pa_deca: Optional[str] = None
    pmg_pa_p_percent: Optional[float] = None
    pmg_ps_dep: Optional[float] = None
    pmg_ps_ac: Optional[int] = None
    pmg_ps_deca: Optional[str] = None
    pmg_ps_p_percent: Optional[float] = None
    pmg_pm_dep: Optional[float] = None
    pmg_pm_ac: Optional[int] = None
    pmg_pm_deca: Optional[str] = None
    pmg_pm_p_percent: Optional[float] = None
    pmg_ipp_dep: Optional[float] = None
    pmg_ipp_ac: Optional[int] = None
    pmg_ipp_deca: Optional[str] = None
    pmg_ipp_p_percent: Optional[float] = None
    pmg_stay_dep: Optional[float] = None
    pmg_stay_ac: Optional[int] = None
    pmg_stay_deca: Optional[str] = None
    pmg_stay_p_percent: Optional[float] = None
    pmg_pe365_dep: Optional[float] = None
    pmg_pe365_ac: Optional[int] = None
    pmg_pe365_deca: Optional[str] = None
    pmg_pe365_p_percent: Optional[float] = None
    
    # PMGZ - Características de Carcaça
    pmg_aol_dep: Optional[float] = None
    pmg_aol_ac: Optional[int] = None
    pmg_aol_deca: Optional[str] = None
    pmg_acab_dep: Optional[float] = None
    pmg_acab_ac: Optional[int] = None
    pmg_acab_deca: Optional[str] = None
    pmg_mar_dep: Optional[float] = None
    pmg_mar_ac: Optional[int] = None
    pmg_mar_deca: Optional[str] = None
    
    # PMGZ - Morfológicas
    pmg_eg_dep: Optional[float] = None
    pmg_eg_ac: Optional[int] = None
    pmg_eg_deca: Optional[str] = None
    pmg_p_dep: Optional[float] = None
    pmg_p_ac: Optional[int] = None
    pmg_p_deca: Optional[str] = None
    pmg_m_dep: Optional[float] = None
    pmg_m_ac: Optional[int] = None
    pmg_m_deca: Optional[str] = None
    pmg_psn_dep: Optional[float] = None
    pmg_psn_ac: Optional[int] = None
    pmg_psn_deca: Optional[str] = None
    
    # PMGZ - Extras
    pmg_p_percent: Optional[float] = None
    pmg_f_percent: Optional[float] = None
    
    # PMGZ - AC (Accuracy)
    pmg_ac_iabc: Optional[float] = None
    pmg_ac_p: Optional[float] = None
    pmg_ac_m: Optional[float] = None
    
    fonte_origem: Optional[str] = None
    data_processamento: Optional[datetime] = None
    
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


# ============================================
# Genetics Farm Schemas
# ============================================
class GeneticsFarmCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    documento: Optional[str] = None


class GeneticsFarmUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    documento: Optional[str] = None


class GeneticsFarmResponse(BaseModel):
    id: str
    nome: Optional[str]
    documento: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        return str(v) if v is not None else v


# ============================================
# Upload Schemas
# ============================================
class UploadCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    id_farm: int
    fonte_origem: str = Field(..., pattern="^(ANCP|PMGZ|GENEPLUS|PMG)$")
    arquivo_nome_original: Optional[str] = None
    arquivo_hash: Optional[str] = None


class UploadResponse(BaseModel):
    upload_id: str
    nome: str
    id_farm: int
    fonte_origem: str
    arquivo_nome_original: Optional[str]
    arquivo_hash: Optional[str]
    total_registros: int
    rows_inserted: int
    rows_updated: int
    status: str
    error_message: Optional[str]
    usuario_id: Optional[int]
    data_upload: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class UploadWithAnimalsResponse(BaseModel):
    upload: UploadResponse
    farm_nome: str
    animais_preview: list[AnimalResponse]
    total_animais: int


class UploadFilter(BaseModel):
    farm_id: Optional[int] = None
    fonte_origem: Optional[str] = None
    status: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
