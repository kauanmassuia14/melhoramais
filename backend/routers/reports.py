"""
Router de Relatórios PDF Customizáveis.
Permite gerar relatórios por fazenda com seleção de colunas e filtros.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import Session, aliased, load_only
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from uuid import UUID
import io
import json
import statistics

from backend.database import get_db, get_max_completed_safra, IS_SQLITE
from backend.models import User, Upload, ProcessingLog, RawAnimalData
from backend.models import GeneticsAnimal, GeneticsGeneticEvaluation, GeneticsFarm
from backend.schemas import UploadDetailResponse, ProcessingLogResponse, AnimalResponse

class ReportAnimal:
    """Mock class that supports both attribute access and dict-like get() access
    for compatibility with ReportGenerator.
    """
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
            
    def get(self, key, default=None):
        return getattr(self, key, default)
from backend.auth.dependencies import get_current_user
from backend.report_generator import ReportGenerator
from backend.report_generator_v2 import ReportGeneratorV2

router = APIRouter(prefix="/reports", tags=["Reports"])
router_no_prefix = APIRouter(tags=["Reports"])


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
    farm_id: str = Query(..., description="ID da fazenda"),
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
    
    # Verificar acesso à fazenda (Genetics)
    try:
        farm_uuid = UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de fazenda inválido")
        
    genetics_farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
    if not genetics_farm:
        raise HTTPException(status_code=404, detail="Fazenda não encontrada")
    
    # Usuário não-admin só pode ver sua própria fazenda
    if current_user.role != "admin" and current_user.id_farm != farm_id:
        raise HTTPException(status_code=403, detail="Acesso negado a esta fazenda")
    
    # Validar plataformas
    valid_platforms = [p for p in platforms if p in PLATFORMS]
    if not valid_platforms:
        raise HTTPException(status_code=400, detail="Nenhuma plataforma válida informada")
    # Travas de segurança DoS - se não houver filtros restritivos de peso, forçar limite menor
    if min_p210 is None and max_p210 is None:
        limit = min(limit, 200)

    # Configurar timeout de query no PostgreSQL para proteger o pool de conexões
    if not IS_SQLITE:
        db.execute(text("SET statement_timeout = 10000"))

    # Buscar animais
    query = db.query(GeneticsAnimal).filter(GeneticsAnimal.farm_id == genetics_farm.id)
    
    if sexo:
        query = query.filter(GeneticsAnimal.sexo == sexo)
    
    max_safra = get_max_completed_safra()

    # 1. Filtro por plataforma - usar EXISTS correlacionado no banco de dados
    if valid_platforms:
        query = query.filter(
            db.query(GeneticsGeneticEvaluation.id)
            .filter(
                GeneticsGeneticEvaluation.animal_id == GeneticsAnimal.id,
                GeneticsGeneticEvaluation.fonte_origem.in_(valid_platforms),
                GeneticsGeneticEvaluation.safra <= max_safra
            ).exists()
        )
    
    # 2. Filtro por peso (min_p210 / max_p210) via EXISTS na avaliação mais recente
    if min_p210 is not None or max_p210 is not None:
        # Subquery para pegar a safra mais recente do animal
        latest_safra_sub = db.query(func.max(GeneticsGeneticEvaluation.safra))\
                             .filter(
                                 GeneticsGeneticEvaluation.animal_id == GeneticsAnimal.id,
                                 GeneticsGeneticEvaluation.safra <= max_safra
                             ).correlate(GeneticsAnimal).scalar_subquery()

        # Coalesce das chaves de peso no JSONB/JSON de métricas
        pd_edg_val = GeneticsGeneticEvaluation.metrics['PD-EDg']['dep'].as_float()
        dp210_val = GeneticsGeneticEvaluation.metrics['DP210']['dep'].as_float()
        dp120_val = GeneticsGeneticEvaluation.metrics['DP120']['dep'].as_float()
        pd_val = func.coalesce(pd_edg_val, dp210_val, dp120_val)

        # EXISTS garantindo que a última avaliação atende ao critério de peso
        weight_exists = db.query(GeneticsGeneticEvaluation.id).filter(
            GeneticsGeneticEvaluation.animal_id == GeneticsAnimal.id,
            GeneticsGeneticEvaluation.safra == latest_safra_sub
        )

        if min_p210 is not None:
            weight_exists = weight_exists.filter(pd_val >= min_p210)
        if max_p210 is not None:
            weight_exists = weight_exists.filter(pd_val <= max_p210)

        query = query.filter(weight_exists.exists())
    
    # 3. Otimizações de ORM (Read-Only): load_only + yield_per + limit
    query = query.options(load_only(
        GeneticsAnimal.id,
        GeneticsAnimal.rgn,
        GeneticsAnimal.nome,
        GeneticsAnimal.sexo,
        GeneticsAnimal.nascimento,
        GeneticsAnimal.genotipado,
        GeneticsAnimal.sire_id,
        GeneticsAnimal.dam_id
    ))

    animals = query.limit(limit).all()
    
    if not animals:
        raise HTTPException(status_code=404, detail="Nenhum animal encontrado com os filtros informados")
    
    # 4. Busca das avaliações mais recentes em lote (Batch Query) com Window Function para deduplicação
    animal_ids = [a.id for a in animals]
    eval_map = {}
    
    if animal_ids:
        # Window function subquery para enumerar avaliações por animal ordenadas por safra e criação desc
        row_num_col = func.row_number().over(
            partition_by=GeneticsGeneticEvaluation.animal_id,
            order_by=(GeneticsGeneticEvaluation.safra.desc(), GeneticsGeneticEvaluation.created_at.desc())
        ).label("row_num")
        
        subq = db.query(
            GeneticsGeneticEvaluation.id.label("eval_id"),
            row_num_col
        ).filter(
            GeneticsGeneticEvaluation.animal_id.in_(animal_ids),
            GeneticsGeneticEvaluation.safra <= max_safra
        ).subquery()
        
        # Junta a subquery de linha 1 com a tabela principal para carregar os objetos completos
        latest_evals = db.query(GeneticsGeneticEvaluation).join(
            subq,
            and_(
                GeneticsGeneticEvaluation.id == subq.c.eval_id,
                subq.c.row_num == 1
            )
        ).all()
        
        for ev in latest_evals:
            eval_map[ev.animal_id] = ev

    # Preparar dados estruturados para o relatório
    animal_data = []
    for a in animals:
        latest = eval_map.get(a.id)
        
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
                try:
                    metrics = json.loads(metrics)
                except Exception:
                    metrics = {}
                
            # Mapeia métricas para o formato esperado pelo gerador de PDF
            for key, val in metrics.items():
                if isinstance(val, dict):
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
        animals=animal_data,
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
            
    return result


# ==============================================================================
# SCHEMAS E ROTAS DE RELATÓRIOS AVANÇADOS
# ==============================================================================

class CompareAnimalsRequest(BaseModel):
    animal_ids: List[UUID]


class CompareFarmsRequest(BaseModel):
    farm_ids: List[UUID]
    safra: int


def _extract_trait(metrics, keys):
    if not metrics:
        return None
    for key in keys:
        part = metrics.get(key)
        if isinstance(part, dict) and part.get("dep") is not None:
            try:
                return float(part["dep"])
            except ValueError:
                pass
    return None


@router.post("/compare/animals")
def compare_animals(
    request: CompareAnimalsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if len(request.animal_ids) < 2 or len(request.animal_ids) > 5:
        raise HTTPException(status_code=400, detail="Selecione de 2 a 5 animais para comparar")
        
    if not IS_SQLITE:
        db.execute(text("SET statement_timeout = 10000"))
        
    animals = db.query(GeneticsAnimal).filter(GeneticsAnimal.id.in_(request.animal_ids)).all()
    if len(animals) != len(request.animal_ids):
        raise HTTPException(status_code=404, detail="Um ou mais animais não foram encontrados")
        
    if current_user.role != "admin":
        for a in animals:
            if current_user.id_farm and a.farm_id != current_user.id_farm:
                raise HTTPException(status_code=403, detail="Acesso negado a um ou mais animais selecionados")

    farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == animals[0].farm_id).first()
    farm_name = farm.nome if farm else "Minha Fazenda"

    eval_map = {}
    animal_ids = [a.id for a in animals]
    max_safra = get_max_completed_safra()
    
    if animal_ids:
        row_num_col = func.row_number().over(
            partition_by=GeneticsGeneticEvaluation.animal_id,
            order_by=(GeneticsGeneticEvaluation.safra.desc(), GeneticsGeneticEvaluation.created_at.desc())
        ).label("row_num")
        
        subq = db.query(
            GeneticsGeneticEvaluation.id.label("eval_id"),
            row_num_col
        ).filter(
            GeneticsGeneticEvaluation.animal_id.in_(animal_ids),
            GeneticsGeneticEvaluation.safra <= max_safra
        ).subquery()
        
        latest_evals = db.query(GeneticsGeneticEvaluation).join(
            subq,
            and_(
                GeneticsGeneticEvaluation.id == subq.c.eval_id,
                subq.c.row_num == 1
            )
        ).all()
        
        for ev in latest_evals:
            eval_map[ev.animal_id] = ev

    animals_data = []
    for a in animals:
        latest = eval_map.get(a.id)
        metrics = {}
        if latest and latest.metrics:
            metrics = latest.metrics
            if isinstance(metrics, str):
                try:
                    metrics = json.loads(metrics)
                except Exception:
                    metrics = {}

        pd = _extract_trait(metrics, ["PD-EDg", "DP210", "DP120"])
        ps = _extract_trait(metrics, ["PS-EDg", "DP450"])
        pm = _extract_trait(metrics, ["PM-EMg", "DIPM", "PMM"])
        pe = _extract_trait(metrics, ["PE-365g", "DPE"])
        aol = _extract_trait(metrics, ["AOLg", "DAOL", "AOL"])

        animals_data.append({
            "nome_animal": a.nome or "—",
            "rgn_animal": a.rgn,
            "pd": pd or 0.0,
            "ps": ps or 0.0,
            "pm": pm or 0.0,
            "pe": pe or 0.0,
            "aol": aol or 0.0
        })

    generator = ReportGeneratorV2()
    pdf_bytes = generator.generate_animal_comparison_report(
        farm_name=farm_name,
        animals=animals_data
    )

    filename = f"comparativo_animais_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        },
    )


@router.post("/compare/farms")
def compare_farms(
    request: CompareFarmsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not request.farm_ids:
        raise HTTPException(status_code=400, detail="Selecione pelo menos uma fazenda para comparar")
        
    if current_user.role != "admin":
        for f_id in request.farm_ids:
            if current_user.id_farm and f_id != current_user.id_farm:
                raise HTTPException(status_code=403, detail="Acesso negado a uma ou mais fazendas selecionadas")

    if not IS_SQLITE:
        db.execute(text("SET statement_timeout = 10000"))

    farms = db.query(GeneticsFarm).filter(GeneticsFarm.id.in_(request.farm_ids)).all()
    farm_name_map = {f.id: f.nome for f in farms}

    # Query 1: Farm comparison for the selected crop year
    farms_data = []
    if IS_SQLITE:
        stmt = text("""
            SELECT id, farm_id, indice_principal, metrics
            FROM genetic_evaluations
            WHERE farm_id IN :farm_ids AND safra = :safra
        """)
        rows = db.execute(stmt, {"farm_ids": tuple(request.farm_ids), "safra": request.safra}).fetchall()
        
        farm_groups = {}
        for r in rows:
            f_id = UUID(r[1]) if isinstance(r[1], str) else r[1]
            ind = float(r[2]) if r[2] is not None else None
            m_str = r[3]
            metrics = {}
            if m_str:
                if isinstance(m_str, dict):
                    metrics = m_str
                else:
                    try:
                        metrics = json.loads(m_str)
                    except Exception:
                        metrics = {}
                        
            p210 = _extract_trait(metrics, ["PD-EDg", "DP210", "DP120"])
            p450 = _extract_trait(metrics, ["PS-EDg", "DP450"])
            
            if f_id not in farm_groups:
                farm_groups[f_id] = {"indices": [], "p210s": [], "p450s": [], "count": 0}
            
            farm_groups[f_id]["count"] += 1
            if ind is not None:
                farm_groups[f_id]["indices"].append(ind)
            if p210 is not None:
                farm_groups[f_id]["p210s"].append(p210)
            if p450 is not None:
                farm_groups[f_id]["p450s"].append(p450)
                
        for f_id, data in farm_groups.items():
            name = farm_name_map.get(f_id) or "Fazenda"
            avg_idx = statistics.mean(data["indices"]) if data["indices"] else 0.0
            avg_p210 = statistics.mean(data["p210s"]) if data["p210s"] else None
            avg_p450 = statistics.mean(data["p450s"]) if data["p450s"] else None
            
            farms_data.append({
                "farm_id": f_id,
                "farm_name": name,
                "total_animals": data["count"],
                "avg_index": avg_idx,
                "avg_p210": avg_p210,
                "avg_p450": avg_p450,
            })
    else:
        stmt = text("""
            SELECT 
                farm_id,
                AVG(indice_principal) as avg_index,
                COUNT(id) as total_animals,
                AVG(COALESCE(
                    NULLIF(metrics['PD-EDg'] ->> 'dep', '')::double precision,
                    NULLIF(metrics['DP210'] ->> 'dep', '')::double precision,
                    NULLIF(metrics['DP120'] ->> 'dep', '')::double precision
                )) as avg_p210,
                AVG(COALESCE(
                    NULLIF(metrics['PS-EDg'] ->> 'dep', '')::double precision,
                    NULLIF(metrics['DP450'] ->> 'dep', '')::double precision
                )) as avg_p450
            FROM genetics.genetic_evaluations
            WHERE farm_id IN :farm_ids AND safra = :safra
            GROUP BY farm_id
        """)
        results = db.execute(stmt, {"farm_ids": tuple(request.farm_ids), "safra": request.safra}).fetchall()
        for row in results:
            farms_data.append({
                "farm_id": row[0],
                "farm_name": farm_name_map.get(row[0]) or "Fazenda",
                "total_animals": int(row[2]) if row[2] is not None else 0,
                "avg_index": float(row[1]) if row[1] is not None else 0.0,
                "avg_p210": float(row[3]) if row[3] is not None else None,
                "avg_p450": float(row[4]) if row[4] is not None else None,
            })

    # Query 2: System-wide average for benchmark
    if IS_SQLITE:
        sys_stmt = text("""
            SELECT AVG(indice_principal) as global_avg
            FROM genetic_evaluations
            WHERE safra = :safra
        """)
    else:
        sys_stmt = text("""
            SELECT AVG(indice_principal) as global_avg
            FROM genetics.genetic_evaluations
            WHERE safra = :safra
        """)
    sys_result = db.execute(sys_stmt, {"safra": request.safra}).fetchone()
    system_avg = float(sys_result[0]) if sys_result and sys_result[0] is not None else 0.0

    # Query 3: 3-safra evolution comparison
    safra_years = [request.safra - 2, request.safra - 1, request.safra]
    if IS_SQLITE:
        evol_stmt = text("""
            SELECT farm_id, safra, AVG(indice_principal) as avg_index
            FROM genetic_evaluations
            WHERE farm_id IN :farm_ids AND safra BETWEEN :min_safra AND :safra
            GROUP BY farm_id, safra
        """)
    else:
        evol_stmt = text("""
            SELECT farm_id, safra, AVG(indice_principal) as avg_index
            FROM genetics.genetic_evaluations
            WHERE farm_id IN :farm_ids AND safra BETWEEN :min_safra AND :safra
            GROUP BY farm_id, safra
        """)
        
    evol_results = db.execute(evol_stmt, {
        "farm_ids": tuple(request.farm_ids),
        "min_safra": request.safra - 2,
        "safra": request.safra
    }).fetchall()

    evol_map = {}
    for row in evol_results:
        f_id = UUID(row[0]) if isinstance(row[0], str) else row[0]
        s_yr = int(row[1])
        val = float(row[2]) if row[2] is not None else 0.0
        if f_id not in evol_map:
            evol_map[f_id] = {}
        evol_map[f_id][s_yr] = val

    for fd in farms_data:
        f_id = fd["farm_id"]
        y_vals = []
        for yr in safra_years:
            y_vals.append(evol_map.get(f_id, {}).get(yr, 0.0))
        fd["values"] = y_vals

    generator = ReportGeneratorV2()
    pdf_bytes = generator.generate_farm_benchmark_report(
        farms_data=farms_data,
        system_avg=system_avg,
        safra=request.safra,
        safra_years=safra_years
    )

    filename = f"benchmark_fazendas_{request.safra}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        },
    )


@router.get("/animal/{id}")
def get_animal_datasheet(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    animal = db.query(GeneticsAnimal).filter(GeneticsAnimal.id == id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
        
    if current_user.role != "admin" and current_user.id_farm and animal.farm_id != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Acesso negado a este animal")

    farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == animal.farm_id).first()
    farm_name = farm.nome if farm else "Minha Fazenda"

    max_safra = get_max_completed_safra()
    latest_eval = db.query(GeneticsGeneticEvaluation).filter(
        GeneticsGeneticEvaluation.animal_id == animal.id,
        GeneticsGeneticEvaluation.safra <= max_safra
    ).order_by(
        GeneticsGeneticEvaluation.safra.desc(),
        GeneticsGeneticEvaluation.created_at.desc()
    ).first()

    animal_dict = {
        "nome": animal.nome or "—",
        "rgn": animal.rgn,
        "sexo": animal.sexo,
        "raca": animal.raca,
        "serie": animal.serie,
        "nascimento": animal.nascimento.strftime("%d/%m/%Y") if animal.nascimento else "—",
        "genotipado": animal.genotipado,
        "csg": animal.csg,
        "safra": latest_eval.safra if latest_eval else None,
        "fonte_origem": latest_eval.fonte_origem if latest_eval else None,
        "indice_principal": float(latest_eval.indice_principal) if latest_eval and latest_eval.indice_principal else None,
        "percentil_principal": float(latest_eval.percentil_principal) if latest_eval and latest_eval.percentil_principal else None,
    }

    parents_map = {}
    parent_ids = [uid for uid in [animal.sire_id, animal.dam_id] if uid]
    if parent_ids:
        parents = db.query(GeneticsAnimal).filter(GeneticsAnimal.id.in_(parent_ids)).all()
        parents_map = {p.id: p for p in parents}

    sire = parents_map.get(animal.sire_id) if animal.sire_id else None
    dam = parents_map.get(animal.dam_id) if animal.dam_id else None

    grandparent_ids = []
    if sire:
        if sire.sire_id: grandparent_ids.append(sire.sire_id)
        if sire.dam_id: grandparent_ids.append(sire.dam_id)
    if dam:
        if dam.sire_id: grandparent_ids.append(dam.sire_id)
        if dam.dam_id: grandparent_ids.append(dam.dam_id)

    grandparents_map = {}
    if grandparent_ids:
        grandparents = db.query(GeneticsAnimal).filter(GeneticsAnimal.id.in_(grandparent_ids)).all()
        grandparents_map = {g.id: g for g in grandparents}

    def fmt_anc_dict(anc):
        if not anc:
            return None
        return {"nome": anc.nome or "—", "rgn": anc.rgn}

    pedigree = {
        "sire": fmt_anc_dict(sire),
        "dam": fmt_anc_dict(dam),
        "sire_sire": fmt_anc_dict(grandparents_map.get(sire.sire_id)) if sire and sire.sire_id else None,
        "sire_dam": fmt_anc_dict(grandparents_map.get(sire.dam_id)) if sire and sire.dam_id else None,
        "dam_sire": fmt_anc_dict(grandparents_map.get(dam.sire_id)) if dam and dam.sire_id else None,
        "dam_dam": fmt_anc_dict(grandparents_map.get(dam.dam_id)) if dam and dam.dam_id else None,
    }

    generator = ReportGeneratorV2()
    pdf_bytes = generator.generate_individual_animal_report(
        farm_name=farm_name,
        animal=animal_dict,
        pedigree=pedigree
    )

    filename = f"ficha_animal_{animal.rgn}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        },
    )


# ==============================================================================
# REPORT ENDPOINTS FROM MAIN.PY (MODULARIZED & REFACTORED TO V2)
# ==============================================================================

@router_no_prefix.get("/report/dashboard")
def generate_dashboard_report(
    farm_id: Optional[str] = Query(None),
    include_animals: bool = Query(False),
    include_logs: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid as _uuid
    import statistics
    import json

    # Access Control
    if current_user.role != "admin" and current_user.id_farm:
        farm_id = str(current_user.id_farm)

    if not farm_id:
        raise HTTPException(status_code=400, detail="Farm ID is required")

    try:
        farm_uuid = _uuid.UUID(str(farm_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Farm UUID")

    farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    farm_name = farm.nome

    # Get all animals in the farm
    animal_query = db.query(GeneticsAnimal).filter(GeneticsAnimal.farm_id == farm_uuid)
    total_animals = animal_query.count()

    # Sex Breakdown
    sex_counts_query = (
        db.query(GeneticsAnimal.sexo, func.count(GeneticsAnimal.id))
        .filter(GeneticsAnimal.farm_id == farm_uuid)
        .group_by(GeneticsAnimal.sexo)
        .all()
    )
    animals_by_sex = {s or "unknown": c for s, c in sex_counts_query}

    # Source Platform Breakdown & Evaluations
    eval_query = db.query(GeneticsGeneticEvaluation).filter(GeneticsGeneticEvaluation.farm_id == farm_uuid)
    source_counts_query = (
        db.query(GeneticsGeneticEvaluation.fonte_origem, func.count(GeneticsGeneticEvaluation.id))
        .filter(GeneticsGeneticEvaluation.farm_id == farm_uuid)
        .group_by(GeneticsGeneticEvaluation.fonte_origem)
        .all()
    )
    animals_by_source = {s or "unknown": c for s, c in source_counts_query}

    # Calculate weight statistics (P210, P365, P450)
    all_evals = eval_query.all()

    p210_list = []
    p365_list = []
    p450_list = []

    for ev in all_evals:
        metrics = ev.metrics if isinstance(ev.metrics, dict) else {}
        if isinstance(ev.metrics, str):
            try:
                metrics = json.loads(ev.metrics)
            except Exception:
                metrics = {}

        pd_m = metrics.get("PD-EDg") or metrics.get("DP210") or metrics.get("DP120")
        if pd_m and pd_m.get("dep") is not None:
            p210_list.append(float(pd_m["dep"]))

        pa_m = metrics.get("PA-EDg") or metrics.get("DP365")
        if pa_m and pa_m.get("dep") is not None:
            p365_list.append(float(pa_m["dep"]))

        ps_m = metrics.get("PS-EDg") or metrics.get("DP450")
        if ps_m and ps_m.get("dep") is not None:
            p450_list.append(float(ps_m["dep"]))

    avg_p210 = statistics.mean(p210_list) if p210_list else None
    avg_p365 = statistics.mean(p365_list) if p365_list else None
    avg_p450 = statistics.mean(p450_list) if p450_list else None

    # Recent Uploads (past 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_uploads = (
        db.query(ProcessingLog)
        .filter(ProcessingLog.id_farm == farm_id, ProcessingLog.started_at >= thirty_days_ago)
        .count()
    )

    stats = {
        "total_animals": total_animals,
        "total_farms": 1,
        "animals_by_source": animals_by_source,
        "animals_by_sex": animals_by_sex,
        "recent_uploads": recent_uploads,
        "avg_p210": avg_p210,
        "avg_p365": avg_p365,
        "avg_p450": avg_p450,
    }

    # Fetch animals if requested
    animals_data = None
    if include_animals:
        animals_list = animal_query.all()
        animals_data = []
        
        # Optimize N+1 Query: Fetch all evaluations in a single query
        animal_ids = [a.id for a in animals_list]
        eval_map = {}
        if animal_ids:
            all_evals_for_list = (
                db.query(GeneticsGeneticEvaluation)
                .filter(GeneticsGeneticEvaluation.animal_id.in_(animal_ids))
                .all()
            )
            for ev in all_evals_for_list:
                existing = eval_map.get(ev.animal_id)
                if not existing or (ev.safra and (not existing.safra or ev.safra > existing.safra)):
                    eval_map[ev.animal_id] = ev

        for a in animals_list:
            latest_eval = eval_map.get(a.id)

            p210_val = None
            p365_val = None
            p450_val = None
            metrics = {}
            if latest_eval:
                metrics = latest_eval.metrics if isinstance(latest_eval.metrics, dict) else {}
                if isinstance(latest_eval.metrics, str):
                    try:
                        metrics = json.loads(latest_eval.metrics)
                    except Exception:
                        metrics = {}

                pd_m = metrics.get("PD-EDg") or metrics.get("DP210") or metrics.get("DP120")
                if pd_m and pd_m.get("dep") is not None:
                    p210_val = float(pd_m["dep"])
                pa_m = metrics.get("PA-EDg") or metrics.get("DP365")
                if pa_m and pa_m.get("dep") is not None:
                    p365_val = float(pa_m["dep"])
                ps_m = metrics.get("PS-EDg") or metrics.get("DP450")
                if ps_m and ps_m.get("dep") is not None:
                    p450_val = float(ps_m["dep"])

            animals_data.append({
                "rgn_animal": a.rgn,
                "nome_animal": a.nome or "—",
                "sexo": a.sexo or "—",
                "raca": a.serie or "—",
                "p210_peso_desmama": p210_val,
                "p365_peso_ano": p365_val,
                "p450_peso_sobreano": p450_val,
                "fonte_origem": latest_eval.fonte_origem if latest_eval else "—",
                "metrics": metrics,
            })

    # Generate PDF
    generator = ReportGeneratorV2()
    pdf_bytes = generator.generate_dashboard_report(
        stats=stats,
        animals=animals_data,
        farm_name=farm_name,
    )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=relatorio_dashboard_{datetime.now(timezone(timedelta(hours=-3))).strftime('%Y%m%d_%H%M')}.pdf"
        },
    )


@router.get("/upload/{log_id}", response_model=UploadDetailResponse)
def get_upload_detail(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(ProcessingLog).filter(ProcessingLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Processing log not found")
    
    if current_user.role != "admin" and log.id_farm != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Refactored to query GeneticsAnimal
    try:
        farm_uuid = UUID(log.id_farm)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid Farm ID in log")

    # We try to get animals from genetics.animals that match the farm
    # Filtering by source_system from the evaluations is more robust
    from sqlalchemy import exists
    animals_query = db.query(GeneticsAnimal).filter(
        GeneticsAnimal.farm_id == farm_uuid,
        exists().where(
            (GeneticsGeneticEvaluation.animal_id == GeneticsAnimal.id) &
            (GeneticsGeneticEvaluation.fonte_origem == log.source_system)
        )
    ).order_by(GeneticsAnimal.created_at.desc()).limit(100)
    animals = animals_query.all()
    
    # Map to legacy AnimalResponse fields
    mapped_animals = [
        AnimalResponse(
            id_animal=0,
            id_farm=0,
            rgn_animal=a.rgn,
            nome_animal=a.nome,
            sexo=a.sexo,
            raca=a.raca or a.serie,
            data_nascimento=a.nascimento,
            upload_id=a.upload_id
        ) for a in animals
    ]
    
    return UploadDetailResponse(
        log=ProcessingLogResponse.model_validate(log),
        animals_preview=mapped_animals,
        total_count=log.total_rows,
    )


@router.get("/upload/{log_id}/pdf")
def generate_upload_report(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(ProcessingLog).filter(ProcessingLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Processing log not found")
    
    if current_user.role != "admin" and log.id_farm != current_user.id_farm:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        farm_uuid = UUID(log.id_farm)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid Farm ID in log")

    from sqlalchemy import exists
    animals = db.query(GeneticsAnimal).filter(
        GeneticsAnimal.farm_id == farm_uuid,
        exists().where(
            (GeneticsGeneticEvaluation.animal_id == GeneticsAnimal.id) &
            (GeneticsGeneticEvaluation.fonte_origem == log.source_system)
        )
    ).all()
    
    # Map to ReportAnimal properties for ReportGenerator
    mapped_animals = [
        ReportAnimal(
            rgn_animal=a.rgn,
            nome_animal=a.nome or "—",
            sexo=a.sexo or "—",
            raca=a.raca or a.serie or "—",
            data_nascimento=a.nascimento,
            upload_id=a.upload_id,
            p210_peso_desmama=None,
            p365_peso_ano=None,
            p450_peso_sobreano=None,
            fonte_origem=log.source_system
        ) for a in animals
    ]
    
    farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
    farm_name = farm.nome if farm else None
    
    generator = ReportGenerator()
    pdf_bytes = generator.generate_upload_report(
        log=log,
        animals=mapped_animals,
        farm_name=farm_name,
    )
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=relatorio_upload_{log_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        },
    )


@router.get("/benchmark/pdf")
def generate_benchmark_report(
    platform_code: str = Query(..., description="Platform code (ANCP, GENEPLUS, PMGZ)"),
    characteristic: str = Query(..., description="Characteristic code"),
    farm_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.benchmark import PLATFORMS, get_evaluation_value
    
    if platform_code not in PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Platform {platform_code} not found")
    
    platform = PLATFORMS[platform_code]
    char_info = None
    for char in platform["characteristics"]:
        if char["code"] == characteristic:
            char_info = char
            break
    
    if not char_info:
        raise HTTPException(status_code=404, detail=f"Characteristic {characteristic} not found")
    
    column_name = char_info["column"]
    
    query = db.query(GeneticsGeneticEvaluation, GeneticsAnimal).join(
        GeneticsAnimal, GeneticsGeneticEvaluation.animal_id == GeneticsAnimal.id
    ).filter(
        GeneticsGeneticEvaluation.fonte_origem == platform_code
    )
    if farm_id:
        query = query.filter(GeneticsAnimal.farm_id == farm_id)
    elif current_user.role != "admin" and current_user.id_farm:
        query = query.filter(GeneticsAnimal.farm_id == str(current_user.id_farm))
    
    evaluations_and_animals = query.all()
    
    max_safra = get_max_completed_safra()
    latest_map = {}
    for ev, anim in evaluations_and_animals:
        if ev.safra > max_safra:
            continue
        if anim.id not in latest_map:
            latest_map[anim.id] = (ev, anim)
        else:
            existing_ev, _ = latest_map[anim.id]
            if (ev.safra, ev.created_at) > (existing_ev.safra, existing_ev.created_at):
                latest_map[anim.id] = (ev, anim)
                
    class BenchmarkItem:
        def __init__(self, animal_id, sexo, value, column_name):
            self.animal_id = animal_id
            self.sexo = sexo
            setattr(self, column_name, value)
            
    items = []
    for ev, anim in latest_map.values():
        val = get_evaluation_value(ev, characteristic)
        if val is not None:
            items.append(BenchmarkItem(
                animal_id=anim.rgn,
                sexo=anim.sexo or "—",
                value=val,
                column_name=column_name
            ))
    
    farm_name = None
    if farm_id:
        try:
            farm_uuid = UUID(farm_id)
            farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
            farm_name = farm.nome if farm else None
        except ValueError:
            pass
    elif current_user.id_farm:
        try:
            farm_uuid = UUID(str(current_user.id_farm))
            farm = db.query(GeneticsFarm).filter(GeneticsFarm.id == farm_uuid).first()
            farm_name = farm.nome if farm else None
        except ValueError:
            pass
    
    generator = ReportGenerator()
    pdf_bytes = generator.generate_benchmark_report(
        platform_code=platform_code,
        platform_name=platform["name"],
        characteristic=char_info,
        evaluations=items,
        farm_name=farm_name,
    )
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=relatorio_benchmark_{platform_code}_{characteristic}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        },
    )