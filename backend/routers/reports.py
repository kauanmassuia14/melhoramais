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
from backend.models import Farm as SilverFarm, User, Upload
from backend.models import GeneticsAnimal, GeneticsGeneticEvaluation, GeneticsFarm
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
    
    # Listar fazendas disponíveis (genetics.farms)
    farms_query = db.query(GeneticsFarm)
    if current_user.role != "admin" and current_user.id_farm:
        import uuid as _uuid
        try:
            farm_uuid = _uuid.UUID(str(current_user.id_farm))
            farms_query = farms_query.filter(GeneticsFarm.id == farm_uuid)
        except (ValueError, AttributeError):
            farms_query = farms_query.filter(False)  # retorna vazio se id inválido
    
    farms = farms_query.all()
    
    return {
        "farms": [
            {"id": str(f.id), "name": f.nome, "cnpj": f.documento}
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
    
    # Verificar acesso à fazenda (silver)
    farm = db.query(SilverFarm).filter(SilverFarm.id_farm == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Fazenda não encontrada")
    
    # Usuário não-admin só pode ver sua própria fazenda
    if current_user.role != "admin" and current_user.id_farm != farm_id:
        raise HTTPException(status_code=403, detail="Acesso negado a esta fazenda")
    
    # Validar plataformas
    valid_platforms = [p for p in platforms if p in PLATFORMS]
    if not valid_platforms:
        raise HTTPException(status_code=400, detail="Nenhuma plataforma válida informada")
    
    # Mapear para genetics
    genetics_farm = db.query(GeneticsFarm).filter(
        GeneticsFarm.nome.ilike(f"%{farm.nome_farm}%")
    ).first()
    
    if not genetics_farm:
        raise HTTPException(status_code=404, detail="Fazenda não encontrada no genetics - importe dados primeiro")
    
    # Buscar animais
    import json
    query = db.query(GeneticsAnimal).filter(GeneticsAnimal.farm_id == genetics_farm.id)
    
    if sexo:
        query = query.filter(GeneticsAnimal.sexo == sexo)
    
    # raca não existe em genetics - usar genotipado como filtro alternativo
    # min/max p210 filtrar após buscar
    if min_p210 or max_p210:
        all_animals = query.all()
        filtered_ids = []
        for a in all_animals:
            latest = db.query(GeneticsGeneticEvaluation).filter(
                GeneticsGeneticEvaluation.animal_id == a.id
            ).order_by(GeneticsGeneticEvaluation.safra.desc()).first()
            if latest:
                metrics = latest.metrics or {}
                if isinstance(metrics, str):
                    try: metrics = json.loads(metrics)
                    except: metrics = {}
                
                # Procura PD em PMGZ ou ANCP
                pd = metrics.get('PD-EDg') or metrics.get('DP210') or metrics.get('DP120')
                if pd:
                    try:
                        pd_val = float(pd.get('dep', 0)) if pd.get('dep') else 0
                        if min_p210 and pd_val < min_p210:
                            continue
                        if max_p210 and pd_val > max_p210:
                            continue
                        filtered_ids.append(a.id)
                    except:
                        pass
        query = query.filter(GeneticsAnimal.id.in_(filtered_ids))
    
    # Filtrar por plataforma - verificar se tem avaliações
    if valid_platforms:
        all_animals = query.all()
        animal_ids_with_evals = []
        for a in all_animals:
            evals = db.query(GeneticsGeneticEvaluation).filter(
                GeneticsGeneticEvaluation.animal_id == a.id,
                GeneticsGeneticEvaluation.fonte_origem.in_(valid_platforms)
            ).first()
            if evals:
                animal_ids_with_evals.append(a.id)
        query = query.filter(GeneticsAnimal.id.in_(animal_ids_with_evals))
    
    animals = query.limit(limit).all()
    
    if not animals:
        raise HTTPException(status_code=404, detail="Nenhum animal encontrado com os filtros informados")
    
    # Preparar dados para o relatório - buscar avaliações
    animal_data = []
    for a in animals:
        latest = db.query(GeneticsGeneticEvaluation).filter(
            GeneticsGeneticEvaluation.animal_id == a.id
        ).order_by(GeneticsGeneticEvaluation.safra.desc()).first()
        
        data = {
            "rgn_animal": a.rgn,
            "nome_animal": a.nome,
            "sexo": a.sexo,
            "data_nascimento": a.nascimento.isoformat() if a.nascimento else None,
            "genotipado": a.genotipado,
            "sire_id": str(a.sire_id) if a.sire_id else None,
            "dam_id": str(a.dam_id) if a.dam_id else None,
        }
        
        if latest:
            data["fonte_origem"] = latest.fonte_origem
            data["iabczg"] = float(latest.indice_principal) if latest.indice_principal else None
            
            metrics = latest.metrics or {}
            if isinstance(metrics, str):
                try: metrics = json.loads(metrics)
                except: metrics = {}
                
            # Mapeia métricas para o formato esperado pelo gerador de PDF
            for key, val in metrics.items():
                if isinstance(val, dict):
                    # Simplifica o nome para compatibilidade com templates antigos
                    # e.g. PN-EDg -> pmg_pn_ed_dep
                    clean_key = key.lower().replace("-", "_").replace("_g", "")
                    for k, v in val.items():
                        data[f"pmg_{clean_key}_{k}"] = v
        
        animal_data.append(data)
    
    # Escolher colunas a incluir
    selected_columns = _select_columns(platforms, columns, include_basic, include_genealogy)
    
    # Gerar PDF
    generator = ReportGeneratorV2()
    pdf_bytes = generator.generate_custom_report(
        farm_name=farm.nome_farm,
        animals=animal_data,  # Passar dados formatados
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