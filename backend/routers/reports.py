"""
Router de Relatórios PDF Customizáveis.
Permite gerar relatórios por fazenda com seleção de colunas e filtros.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import io
import statistics

from backend.database import get_db
from backend.models import Animal, Farm, User, Upload
from backend.auth.dependencies import get_current_user
from backend.report_generator_v2 import ReportGeneratorV2


router = APIRouter(prefix="/reports", tags=["Reports"])


# ==============================================================================
# CONFIGURAÇÕES DISPONÍVEIS
# ==============================================================================

PLATFORMS = {
    "ANCP": {
        "name": "ANCP",
        "characteristics": [
            {"code": "anc_mg", "name": "Média Genética (MG)", "type": "index"},
            {"code": "anc_te", "name": "Tamanho (TE)", "type": "index"},
            {"code": "anc_m", "name": "Maternidade (M)", "type": "index"},
            {"code": "anc_p", "name": "Peso (P)", "type": "dep"},
            {"code": "anc_sp", "name": "Sobreano (SP)", "type": "dep"},
            {"code": "anc_e", "name": "Eficiência (E)", "type": "dep"},
            {"code": "anc_sao", "name": "Área Olho Lombo (SAO)", "type": "dep"},
            {"code": "anc_leg", "name": "Espessura Gordura (LEG)", "type": "dep"},
            {"code": "anc_dp", "name": "Desvio Padrão (DP)", "type": "accuracy"},
            {"code": "anc_sh", "name": "Sexo Hack (SH)", "type": "dep"},
            {"code": "anc_pp30", "name": "Produção Prioritária 30", "type": "index"},
        ]
    },
    "GENEPLUS": {
        "name": "GENEPLUS",
        "characteristics": [
            {"code": "gen_iqg", "name": "Índice Qualidade Genética (IQG)", "type": "index"},
            {"code": "gen_pmm", "name": "Peso Maternidade (PMM)", "type": "index"},
            {"code": "gen_p", "name": "Peso (P)", "type": "dep"},
            {"code": "gen_sp", "name": "Sobreano (SP)", "type": "dep"},
            {"code": "gen_e", "name": "Eficiência (E)", "type": "dep"},
            {"code": "gen_sao", "name": "Área Olho Lombo (SAO)", "type": "dep"},
            {"code": "gen_leg", "name": "Espessura Gordura (LEG)", "type": "dep"},
            {"code": "gen_dp", "name": "Desvio Padrão (DP)", "type": "accuracy"},
            {"code": "gen_sh", "name": "Sexo Hack (SH)", "type": "dep"},
            {"code": "gen_pp30", "name": "Produção Prioritária 30", "type": "index"},
        ]
    },
    "PMGZ": {
        "name": "PMGZ",
        "characteristics": [
            {"code": "pmg_iabc", "name": "Índice ABCZ (IABC)", "type": "index"},
            {"code": "pmg_zpmm", "name": "Zootecnia Peso Materno (ZPmm)", "type": "index"},
            {"code": "pmg_p", "name": "Peso (P)", "type": "dep"},
            {"code": "pmg_sp", "name": "Sobreano (SP)", "type": "dep"},
            {"code": "pmg_e", "name": "Eficiência (E)", "type": "dep"},
            {"code": "pmg_sao", "name": "Área Olho Lombo (SAO)", "type": "dep"},
            {"code": "pmg_leg", "name": "Espessura Gordura (LEG)", "type": "dep"},
            {"code": "pmg_dp", "name": "Desvio Padrão (DP)", "type": "accuracy"},
            {"code": "pmg_sh", "name": "Sexo Hack (SH)", "type": "dep"},
            {"code": "pmg_pp30", "name": "Produção Prioritária 30", "type": "index"},
        ]
    }
}

# Colunas básicas disponíveis (não específicas de plataforma)
BASIC_COLUMNS = [
    {"code": "rgn_animal", "name": "RGN", "category": "identification"},
    {"code": "nome_animal", "name": "Nome", "category": "identification"},
    {"code": "sexo", "name": "Sexo", "category": "basic"},
    {"code": "raca", "name": "Raça", "category": "basic"},
    {"code": "data_nascimento", "name": "Data Nascimento", "category": "basic"},
    {"code": "peso_nascimento", "name": "Peso Nascimento", "category": "weight"},
    {"code": "p210_peso_desmama", "name": "P210 Desmama", "category": "weight"},
    {"code": "p365_peso_ano", "name": "P365 Ano", "category": "weight"},
    {"code": "p450_peso_sobreano", "name": "P450 Sobreano", "category": "weight"},
    {"code": "mae_rgn", "name": "Mãe (RGN)", "category": "genealogy"},
    {"code": "pai_rgn", "name": "Pai (RGN)", "category": "genealogy"},
]


@router.get("/options")
def get_report_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna todas as opções disponíveis para customizar o relatório."""
    
    # Listar fazendas доступíveis
    farms_query = db.query(Farm)
    if current_user.role != "admin" and current_user.id_farm:
        farms_query = farms_query.filter(Farm.id_farm == current_user.id_farm)
    
    farms = farms_query.all()
    
    return {
        "farms": [
            {"id": f.id_farm, "name": f.nome_farm, "cnpj": f.cnpj}
            for f in farms
        ],
        "platforms": PLATFORMS,
        "basic_columns": BASIC_COLUMNS
    }


@router.get("/columns/{platform}")
def get_platform_columns(
    platform: str,
    current_user: User = Depends(get_current_user),
):
    """Retorna colunas disponíveis para uma plataforma específica."""
    
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Plataforma {platform} não encontrada")
    
    return PLATFORMS[platform]


@router.post("/generate")
def generate_custom_report(
    farm_id: int = Query(..., description="ID da fazenda"),
    platforms: List[str] = Query(..., description="Plataformas a incluir (ANCP, GENEPLUS, PMGZ)"),
    include_basic: bool = Query(True, description="Incluir dados básicos (RGN, sexo, pesos)"),
    include_genealogy: bool = Query(False, description="Incluir genealogia"),
    columns: Optional[str] = Query(None, description="Colunas separadas por vírgula"),
    sexo: Optional[str] = Query(None, description="Filtrar por sexo (M/F)"),
    raca: Optional[str] = Query(None, description="Filtrar por raça"),
    min_p210: Optional[float] = Query(None, description="P210 mínimo"),
    max_p210: Optional[float] = Query(None, description="P210 máximo"),
    limit: int = Query(500, ge=1, le=1000, description="Limite de animais no PDF"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gera relatório PDF customizável para uma fazenda.
    
    Exemplo de uso:
    - platforms=ANCP&include_basic=true&include_genealogy=true
    - platforms=ANCP,PMGZ&columns=anc_mg,pmg_iabc
    """
    
    # Verificar acesso à fazenda
    farm = db.query(Farm).filter(Farm.id_farm == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Fazenda não encontrada")
    
    # Usuário não-admin só pode ver sua própria fazenda
    if current_user.role != "admin" and current_user.id_farm != farm_id:
        raise HTTPException(status_code=403, detail="Acesso negado a esta fazenda")
    
    # Validar plataformas
    valid_platforms = [p for p in platforms if p in PLATFORMS]
    if not valid_platforms:
        raise HTTPException(status_code=400, detail="Nenhuma plataforma válida informada")
    
    # Buscar animais
    query = db.query(Animal).filter(Animal.id_farm == farm_id)
    
    if sexo:
        query = query.filter(Animal.sexo == sexo)
    if raca:
        query = query.filter(Animal.raca == raca)
    if min_p210:
        query = query.filter(Animal.p210_peso_desmama >= min_p210)
    if max_p210:
        query = query.filter(Animal.p210_peso_desmama <= max_p210)
    
    # Se não tem filtro de plataforma, buscar todos
    # Se tem, buscar os que têm dados de pelo menos uma das plataformas
    if valid_platforms:
        platform_conditions = []
        for p in valid_platforms:
            platform = PLATFORMS[p]
            # animals com pelo menos uma coluna dessa plataforma
            for char in platform["characteristics"]:
                col = char["code"]
                if hasattr(Animal, col):
                    platform_conditions.append(getattr(Animal, col).isnot(None))
        
        if platform_conditions:
            from sqlalchemy import or_ as sql_or
            query = query.filter(sql_or(*platform_conditions))
    
    animals = query.limit(limit).all()
    
    if not animals:
        raise HTTPException(status_code=404, detail="Nenhum animal encontrado com os filtros informados")
    
    # Escolher colunas a incluir
    selected_columns = _select_columns(platforms, columns, include_basic, include_genealogy)
    
    # Gerar PDF
    generator = ReportGeneratorV2()
    pdf_bytes = generator.generate_custom_report(
        farm_name=farm.nome_farm,
        animals=animals,
        platforms=valid_platforms,
        selected_columns=selected_columns,
        include_genealogy=include_genealogy,
    )
    
    filename = f"relatorio_{farm.nome_farm.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        },
    )


@router.get("/generate")
def generate_report_get(
    farm_id: int = Query(..., description="ID da fazenda"),
    platforms: str = Query("ANCP", description="Plataformas separadas por vírgula"),
    include_basic: bool = Query(True),
    include_genealogy: bool = Query(False),
    columns: Optional[str] = Query(None, description="Colunas separadas por vírgula"),
    sexo: Optional[str] = Query(None),
    raca: Optional[str] = Query(None),
    limit: int = Query(500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Versão GET do generate_custom_report"""
    
    # Parse platforms
    platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
    
    # Parse columns
    column_list = None
    if columns:
        column_list = [c.strip() for c in columns.split(",") if c.strip()]
    
    return generate_custom_report(
        farm_id=farm_id,
        platforms=platform_list,
        include_basic=include_basic,
        include_genealogy=include_genealogy,
        columns=column_list,
        sexo=sexo,
        raca=raca,
        limit=limit,
        db=db,
        current_user=current_user,
    )


def _select_columns(platforms: List[str], selected: Optional[str], include_basic: bool, include_genealogy: bool) -> dict:
    """Seleciona as colunas a incluir no relatório."""
    
    # Parse selected columns if provided as comma-separated string
    selected_list = []
    if selected:
        selected_list = [c.strip() for c in selected.split(",") if c.strip()]
    
    result = {
        "basic": [],
        "genealogy": [],
        "platforms": {}
    }
    
    # Colunas básicas
    if include_basic:
        result["basic"] = [
            "rgn_animal", "nome_animal", "sexo", "raca", "data_nascimento",
            "peso_nascimento", "p210_peso_desmama", "p365_peso_ano", "p450_peso_sobreano"
        ]
    
    # Genealogia
    if include_genealogy:
        result["genealogy"] = [
            "mae_rgn", "pai_rgn",
            "avo_paterno_rgn", "avo_paterno_mae_rgn", "avo_materno_rgn", "avo_materno_mae_rgn"
        ]
    
    # Colunas por plataforma
    for platform in platforms:
        if platform in PLATFORMS:
            if selected_list:
                # Filtrar apenas as selecionadas
                platform_cols = [
                    char["code"] for char in PLATFORMS[platform]["characteristics"]
                    if char["code"] in selected_list
                ]
            else:
                # Todas as colunas da plataforma
                platform_cols = [
                    char["code"] for char in PLATFORMS[platform]["characteristics"]
                ]
            
            result["platforms"][platform] = platform_cols
    
    return result