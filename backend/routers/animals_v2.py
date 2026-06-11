from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Optional
import json
import logging

from backend.models import GeneticsAnimal, GeneticsGeneticEvaluation, GeneticsFarm
from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/animals", tags=["Animals V2"])


def parse_metric_block(mb_value) -> Optional[dict]:
    """Parse metric_block: suporta JSON, tuple PostgreSQL '(dep,ac,deca,p_pct)' e None."""
    if mb_value is None:
        return None
    if isinstance(mb_value, str):
        mb_value = mb_value.strip()
        if not mb_value:
            return None
        # Formato tuple PostgreSQL: '(0.87,36.0,10,)'
        if mb_value.startswith('(') and mb_value.endswith(')'):
            try:
                inner = mb_value[1:-1]  # remove parênteses
                parts = inner.split(',')
                return {
                    "dep": float(parts[0]) if parts[0].strip() else None,
                    "ac": float(parts[1]) if len(parts) > 1 and parts[1].strip() else None,
                    "deca": int(float(parts[2])) if len(parts) > 2 and parts[2].strip() else None,
                    "p_percent": float(parts[3]) if len(parts) > 3 and parts[3].strip() else None,
                }
            except Exception as e:
                logger.warning(f"Error parsing tuple metric_block '{mb_value}': {e}")
                return None
        # Formato JSON
        try:
            return json.loads(mb_value)
        except Exception as e:
            logger.warning(f"Error parsing JSON metric_block '{mb_value[:30]}': {e}")
            return None
    # Tuple Python já parsed
    if isinstance(mb_value, tuple):
        try:
            return {
                "dep": float(mb_value[0]) if mb_value[0] is not None else None,
                "ac": float(mb_value[1]) if len(mb_value) > 1 and mb_value[1] is not None else None,
                "deca": int(mb_value[2]) if len(mb_value) > 2 and mb_value[2] is not None else None,
                "p_percent": float(mb_value[3]) if len(mb_value) > 3 and mb_value[3] is not None else None,
            }
        except Exception as e:
            logger.warning(f"Error parsing tuple: {e}")
            return None
    return None


def animal_to_dict(a: GeneticsAnimal, latest_eval: Optional[GeneticsGeneticEvaluation] = None) -> dict:
    """Converte GeneticsAnimal para dict compatível com o frontend."""
    result = {
        "id": str(a.id),
        "rgn": a.rgn,
        "serie": a.serie,
        "nome": a.nome,
        "sexo": a.sexo,
        "nascimento": a.nascimento.isoformat() if a.nascimento else None,
        "genotipado": True if a.genotipado == "SIM" or a.genotipado is True else False,
        "csg": True if a.csg == "SIM" or a.csg is True else False,
        "sire_id": str(a.sire_id) if a.sire_id else None,
        "dam_id": str(a.dam_id) if a.dam_id else None,
        "farm_id": str(a.farm_id) if a.farm_id else None,
        "evaluations": [],
    }

    if latest_eval:
        eval_dict = eval_to_dict(latest_eval)
        result["evaluations"] = [eval_dict]
        # Helper fields for the list view
        result["latest_eval"] = eval_dict
    else:
        result["latest_eval"] = None

    return result


def normalize_metric(m) -> Optional[dict]:
    """Traduz as chaves do banco (processor.py) para o formato do frontend."""
    if not m or not isinstance(m, dict):
        return None
    return {
        "dep": m.get("dep"),
        "ac": m.get("acc") or m.get("ac"),   # No banco pode ser 'acc' ou 'ac'
        "deca": m.get("top"),                  # No banco é 'top', no front é 'deca'
        "p_percent": m.get("perc")             # No banco é 'perc', no front é 'p_percent'
    }


def _first_metric(metrics: dict, *keys) -> Optional[dict]:
    """Retorna o primeiro metric block encontrado dentre as chaves fornecidas."""
    for k in keys:
        val = metrics.get(k)
        if val and isinstance(val, dict):
            return val
    return None


def eval_to_dict(e: GeneticsGeneticEvaluation) -> dict:
    # Basic metrics mapping for frontend backward compatibility
    metrics = e.metrics if isinstance(e.metrics, dict) else {}
    if isinstance(e.metrics, str):
        try:
            metrics = json.loads(e.metrics)
        except:
            metrics = {}

    # Compatibility mapping: map standardized names (from processor.py) to standard frontend fields
    # Suporta PMGZ (PN-EDg), ANCP (DPN), e GENEPLUS (PN) side-by-side
    return {
        "id": str(e.id),
        "safra": e.safra,
        "fonte_origem": e.fonte_origem,
        "iabczg": float(e.indice_principal) if e.indice_principal is not None else (float(e.iabczg) if hasattr(e, 'iabczg') and e.iabczg is not None else None),
        "deca_index": float(e.percentil_principal) if e.percentil_principal is not None else (e.rank_principal if e.rank_principal is not None else None),
        "metrics": metrics,
        # Pesos — PMGZ / ANCP / GENEPLUS
        "pn": normalize_metric(_first_metric(metrics, "PN-EDg", "DPN", "PN")),
        "pd": normalize_metric(_first_metric(metrics, "PD-EDg", "DP210", "DP120", "PD")),
        "pa": normalize_metric(_first_metric(metrics, "PA-EDg", "DP365")),
        "ps": normalize_metric(_first_metric(metrics, "PS-EDg", "DP450", "PS")),
        "pm": normalize_metric(_first_metric(metrics, "PM-EMg", "DIPM", "PMm")),
        # Reprodução
        "ipp": normalize_metric(_first_metric(metrics, "IPPg", "DIPP", "IPP")),
        "stay": normalize_metric(_first_metric(metrics, "STAYg", "DSTAY", "STAY")),
        "pe_365": normalize_metric(_first_metric(metrics, "PE-365g", "DPE365", "PES")),
        "psn": normalize_metric(_first_metric(metrics, "PSNg")),
        # Carcaça
        "aol": normalize_metric(_first_metric(metrics, "AOLg", "DAOL", "AOL")),
        "acab": normalize_metric(_first_metric(metrics, "ACABg", "DACAB", "EGS")),
        "marmoreio": normalize_metric(_first_metric(metrics, "MARg", "DMAR", "MAR")),
        # Conformação
        "eg": normalize_metric(_first_metric(metrics, "Eg", "DES")),
        "pg": normalize_metric(_first_metric(metrics, "Pg", "DPS")),
        "mg": normalize_metric(_first_metric(metrics, "Mg", "DMS")),
    }



# ============================================================
# ROTAS ESTÁTICAS — devem vir ANTES de /{animal_id}
# ============================================================

# ── Comparação cross-platform de um animal ─────────────────────
@router.get("/compare/{animal_id}")
def get_animal_comparison(
    animal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna dados de comparação cross-platform para um animal específico.
    Formato compatível com AnimalComparisonData do frontend."""
    import uuid as _uuid
    try:
        animal_uuid = _uuid.UUID(animal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"ID inválido: '{animal_id}'")

    animal = db.query(GeneticsAnimal).filter(GeneticsAnimal.id == animal_uuid).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")

    evaluations = (
        db.query(GeneticsGeneticEvaluation)
        .filter(GeneticsGeneticEvaluation.animal_id == animal.id)
        .order_by(GeneticsGeneticEvaluation.safra.desc())
        .all()
    )

    # Monta o dict por plataforma (mais recente de cada fonte)
    platforms: dict = {}
    seen_sources: set = set()
    available_metrics_set: set = set()

    # Mapeamento de chaves JSONB para chaves frontend normalizadas
    METRIC_KEY_MAP = {
        # PMGZ
        "PN-EDg": "pn", "PD-EDg": "pd", "PA-EDg": "pa", "PS-EDg": "ps", "PM-EMg": "pm",
        "IPPg": "ipp", "STAYg": "stay", "PE-365g": "pe365", "PSNg": "psn",
        "AOLg": "aol", "ACABg": "acab", "MARg": "mar",
        "Eg": "eg", "Pg": "pg", "Mg": "mg",
        # ANCP
        "DPN": "pn", "DP210": "pd", "DP120": "pd", "DP365": "pa", "DP450": "ps", "DIPM": "pm",
        "DIPP": "ipp", "DSTAY": "stay", "DPE365": "pe365",
        "DAOL": "aol", "DACAB": "acab", "DMAR": "mar",
        "DES": "eg", "DPS": "pg", "DMS": "mg",
        # GENEPLUS
        "PN": "pn", "PD": "pd", "PS": "ps", "PMm": "pm",
        "IPP": "ipp", "STAY": "stay", "PES": "pe365",
        "AOL": "aol", "EGS": "acab", "MAR": "mar", "CAR": "car",
        "GPD": "gpd", "CFD": "cfd", "CFS": "cfs", "PP30": "pp30", "RD": "rd",
        "TMm": "tmm", "TMD": "tmd",
    }

    for ev in evaluations:
        fonte = ev.fonte_origem
        if fonte in seen_sources:
            continue
        seen_sources.add(fonte)

        raw_metrics = ev.metrics if isinstance(ev.metrics, dict) else {}
        if isinstance(ev.metrics, str):
            try:
                raw_metrics = json.loads(ev.metrics)
            except:
                raw_metrics = {}

        normalized_metrics: dict = {}
        for raw_key, block in raw_metrics.items():
            if not isinstance(block, dict):
                continue
            front_key = METRIC_KEY_MAP.get(raw_key, raw_key.lower())
            normalized_metrics[front_key] = {
                "dep": block.get("dep"),
                "acc": block.get("acc") or block.get("ac"),
                "deca": block.get("top"),
                "p_percent": block.get("perc"),
            }
            available_metrics_set.add(front_key)

        platforms[fonte] = {
            "fonte": fonte,
            "safra": ev.safra,
            "indice_principal": float(ev.indice_principal) if ev.indice_principal else None,
            "rank": ev.rank_principal,
            "metrics": normalized_metrics,
        }

    # Sempre incluir MELHORA_PLUS como null (para o formulário de dados manuais)
    if "MELHORA_PLUS" not in platforms:
        platforms["MELHORA_PLUS"] = None

    CANONICAL_METRICS = ["pn", "pd", "pa", "ps", "pm", "ipp", "stay", "pe365", "aol", "acab", "mar", "eg", "pg", "mg"]

    return {
        "animal": {
            "id": str(animal.id),
            "rgn": animal.rgn,
            "nome": animal.nome,
        },
        "platforms": platforms,
        "available_metrics": sorted(list(available_metrics_set | set(CANONICAL_METRICS))),
    }


from fastapi import BackgroundTasks
from backend.models import DashboardStatsCache
from datetime import datetime, timezone, timedelta

# ── Funções de Computação Interna de Estatísticas ──────────────────
def compute_stats_v2_internal(db: Session, farm_id: Optional[str]) -> dict:
    query = db.query(GeneticsAnimal)

    if farm_id:
        query = query.filter(GeneticsAnimal.farm_id == farm_id)

    total_animals = query.count()

    sex_counts = (
        query.with_entities(GeneticsAnimal.sexo, func.count())
        .group_by(GeneticsAnimal.sexo)
        .all()
    )
    animals_by_sex = {s or "unknown": c for s, c in sex_counts}

    # Subconsulta para filtrar animais
    animal_subq = query.with_entities(GeneticsAnimal.id).subquery()
    
    eval_counts = (
        db.query(GeneticsGeneticEvaluation.fonte_origem, func.count())
        .filter(GeneticsGeneticEvaluation.animal_id.in_(animal_subq))
        .group_by(GeneticsGeneticEvaluation.fonte_origem)
        .all()
    )
    source_counts = {s or "unknown": c for s, c in eval_counts}

    # Médias de pesos
    p210 = db.execute(
        text("""
            SELECT AVG(
                CASE 
                    WHEN fonte_origem = 'PMGZ' THEN (metrics->'PD-EDg'->>'dep')::numeric
                    WHEN fonte_origem = 'ANCP' THEN (metrics->'DP210'->>'dep')::numeric
                    WHEN fonte_origem = 'GENEPLUS' THEN (metrics->'PD'->>'dep')::numeric
                    ELSE NULL
                END
            )
            FROM genetics.genetic_evaluations
            WHERE animal_id IN (SELECT id FROM genetics.animals WHERE farm_id = :fid OR :is_admin)
        """),
        {"fid": farm_id, "is_admin": farm_id is None}
    ).scalar()
    
    # P365 (Ano)
    p365 = db.execute(
        text("""
            SELECT AVG(
                CASE 
                    WHEN fonte_origem = 'PMGZ' THEN (metrics->'PA-EDg'->>'dep')::numeric
                    WHEN fonte_origem = 'ANCP' THEN (metrics->'DP365'->>'dep')::numeric
                    WHEN fonte_origem = 'GENEPLUS' THEN NULL
                    ELSE NULL
                END
            )
            FROM genetics.genetic_evaluations
            WHERE animal_id IN (SELECT id FROM genetics.animals WHERE farm_id = :fid OR :is_admin)
        """),
        {"fid": farm_id, "is_admin": farm_id is None}
    ).scalar()

    # P450 (Sobreano)
    p450 = db.execute(
        text("""
            SELECT AVG(
                CASE 
                    WHEN fonte_origem = 'PMGZ' THEN (metrics->'PS-EDg'->>'dep')::numeric
                    WHEN fonte_origem = 'ANCP' THEN (metrics->'DP450'->>'dep')::numeric
                    WHEN fonte_origem = 'GENEPLUS' THEN (metrics->'PS'->>'dep')::numeric
                    ELSE NULL
                END
            )
            FROM genetics.genetic_evaluations
            WHERE animal_id IN (SELECT id FROM genetics.animals WHERE farm_id = :fid OR :is_admin)
        """),
        {"fid": farm_id, "is_admin": farm_id is None}
    ).scalar()

    avg_p210 = round(float(p210), 2) if p210 else None
    avg_p365 = round(float(p365), 2) if p365 else None
    avg_p450 = round(float(p450), 2) if p450 else None

    if farm_id is None:
        total_farms = db.query(GeneticsFarm).count()
    else:
        total_farms = 1

    from backend.models import Upload
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    uploads_query = db.query(Upload).filter(Upload.data_upload >= thirty_days_ago)
    if farm_id:
        uploads_query = uploads_query.filter(Upload.id_farm == farm_id)
    recent_uploads = uploads_query.count()

    return {
        "total_animals": total_animals,
        "total_farms": total_farms,
        "recent_uploads": recent_uploads,
        "animals_by_sex": animals_by_sex,
        "animals_by_source": source_counts,
        "avg_p210": avg_p210,
        "avg_p365": avg_p365,
        "avg_p450": avg_p450,
    }


def compute_platform_comparison_internal(db: Session, farm_id: Optional[str]) -> dict:
    METRIC_CONFIG = {
        "pn":    {"PMGZ": "PN-EDg",  "ANCP": "DPN",   "GENEPLUS": "PN"},
        "pd":    {"PMGZ": "PD-EDg",  "ANCP": "DP210", "GENEPLUS": "PD"},
        "ps":    {"PMGZ": "PS-EDg",  "ANCP": "DP450", "GENEPLUS": "PS"},
        "pm":    {"PMGZ": "PM-EMg",  "ANCP": "DIPM",  "GENEPLUS": "PMm"},
        "ipp":   {"PMGZ": "IPPg",    "ANCP": "DIPP",  "GENEPLUS": "IPP"},
        "stay":  {"PMGZ": "STAYg",   "ANCP": "DSTAY", "GENEPLUS": "STAY"},
        "pe365": {"PMGZ": "PE-365g", "ANCP": "DPE365","GENEPLUS": "PES"},
        "aol":   {"PMGZ": "AOLg",    "ANCP": "DAOL",  "GENEPLUS": "AOL"},
        "acab":  {"PMGZ": "ACABg",   "ANCP": "DACAB", "GENEPLUS": "EGS"},
        "mar":   {"PMGZ": "MARg",    "ANCP": "DMAR",  "GENEPLUS": "MAR"},
    }

    farm_filter = ""
    params: dict = {}
    if farm_id:
        farm_filter = "AND ge.farm_id = :farm_id"
        params["farm_id"] = farm_id

    INDICE_LABELS = {"ANCP": "MGTe", "PMGZ": "IABCZ", "GENEPLUS": "IQG"}

    select_fields = [
        "fonte_origem",
        "COUNT(DISTINCT animal_id) as cnt",
        "AVG(indice_principal) as avg_indice"
    ]
    
    for metric_key, keys_by_fonte in METRIC_CONFIG.items():
        cases = []
        for fonte, json_key in keys_by_fonte.items():
            cases.append(f"WHEN fonte_origem = '{fonte}' THEN (metrics->'{json_key}'->>'dep')::numeric")
        cases_sql = " ".join(cases)
        
        select_fields.append(f"AVG(CASE {cases_sql} END) as avg_{metric_key}")
        select_fields.append(f"MIN(CASE {cases_sql} END) as min_{metric_key}")
        select_fields.append(f"MAX(CASE {cases_sql} END) as max_{metric_key}")

    fields_clause = ",\n            ".join(select_fields)
    agg_sql = text(f"""
        SELECT 
            {fields_clause}
        FROM genetics.genetic_evaluations ge
        WHERE 1=1 {farm_filter}
        GROUP BY fonte_origem
    """)

    rows = db.execute(agg_sql, params).fetchall()

    result_platforms: dict = {}
    for row in rows:
        row_dict = row._asdict() if hasattr(row, "_asdict") else dict(zip([f.split(" as ")[-1].strip() for f in select_fields], row))
        
        fonte = row_dict.get("fonte_origem")
        if not fonte or fonte not in ["PMGZ", "ANCP", "GENEPLUS"]:
            continue

        averages: dict = {}
        for metric_key in METRIC_CONFIG.keys():
            avg_val = row_dict.get(f"avg_{metric_key}")
            min_val = row_dict.get(f"min_{metric_key}")
            max_val = row_dict.get(f"max_{metric_key}")
            
            if avg_val is not None:
                averages[metric_key] = {
                    "avg": round(float(avg_val), 2),
                    "min": round(float(min_val), 2),
                    "max": round(float(max_val), 2),
                }

        avg_indice = row_dict.get("avg_indice")
        result_platforms[fonte] = {
            "total_animals": row_dict.get("cnt", 0),
            "avg_indice_principal": round(float(avg_indice), 2) if avg_indice is not None else None,
            "indice_label": INDICE_LABELS.get(fonte),
            "averages": averages,
        }

    for f in ["PMGZ", "ANCP", "GENEPLUS"]:
        if f not in result_platforms:
            result_platforms[f] = {
                "total_animals": 0,
                "avg_indice_principal": None,
                "indice_label": INDICE_LABELS.get(f),
                "averages": {}
            }

    return {
        "metrics": list(METRIC_CONFIG.keys()),
        "platforms": result_platforms,
    }


def compute_analytics_internal(db: Session, farm_id: Optional[str]) -> dict:
    farm_filter_animals = ""
    farm_filter_evals = ""
    params = {}
    if farm_id:
        farm_filter_animals = "WHERE farm_id = :farm_id"
        farm_filter_evals = "WHERE farm_id = :farm_id"
        params["farm_id"] = farm_id

    # Summary
    summary_sql = text(f"""
        SELECT 
            COUNT(*) as total_animals,
            COUNT(CASE WHEN genotipado::text = 'SIM' THEN 1 END) as genotyped,
            COUNT(CASE WHEN csg::text = 'SIM' THEN 1 END) as csg_count,
            COUNT(DISTINCT COALESCE(NULLIF(raca, ''), 'Não Informado')) as total_breeds
        FROM genetics.animals
        {farm_filter_animals}
    """)
    summary_row = db.execute(summary_sql, params).fetchone()
    total_animals = summary_row[0] if summary_row else 0
    genotyped = summary_row[1] if summary_row else 0
    csg_count = summary_row[2] if summary_row else 0
    total_breeds = summary_row[3] if summary_row else 0

    genotyping_rate = round((genotyped / total_animals * 100), 2) if total_animals > 0 else 0.0
    csg_rate = round((csg_count / total_animals * 100), 2) if total_animals > 0 else 0.0

    eval_summary_sql = text(f"""
        SELECT 
            COUNT(*) as total_evaluations,
            ARRAY_AGG(DISTINCT fonte_origem) as platforms
        FROM genetics.genetic_evaluations
        {farm_filter_evals}
    """)
    eval_row = db.execute(eval_summary_sql, params).fetchone()
    total_evaluations = eval_row[0] if eval_row else 0
    raw_platforms = eval_row[1] if eval_row and eval_row[1] else []
    platforms = [p for p in raw_platforms if p]

    # Breed distribution
    breed_sql = text(f"""
        SELECT COALESCE(NULLIF(raca, ''), 'Não Informado') as breed, COUNT(*) as cnt
        FROM genetics.animals
        {farm_filter_animals}
        GROUP BY breed
        ORDER BY cnt DESC
    """)
    breed_rows = db.execute(breed_sql, params).fetchall()
    breed_dist = {r[0]: r[1] for r in breed_rows}

    # Sex distribution
    sex_sql = text(f"""
        SELECT 
            CASE 
                WHEN sexo::text IN ('M', 'MACHO', 'Macho') THEN 'M'
                WHEN sexo::text IN ('F', 'FEMEA', 'FÊMEA', 'Fêmea', 'Femea') THEN 'F'
                ELSE 'Outros'
            END as sex,
            COUNT(*) as cnt
        FROM genetics.animals
        {farm_filter_animals}
        GROUP BY sex
    """)
    sex_rows = db.execute(sex_sql, params).fetchall()
    sex_dist = {r[0]: r[1] for r in sex_rows}

    # Weight metrics (P210, P365, P450)
    weight_metrics = {}
    for metric_name, mappings in [
        ("p210", [("PMGZ", "PD-EDg"), ("ANCP", "DP210"), ("GENEPLUS", "PD")]),
        ("p365", [("PMGZ", "PA-EDg"), ("ANCP", "DP365")]),
        ("p450", [("PMGZ", "PS-EDg"), ("ANCP", "DP450"), ("GENEPLUS", "PS")])
    ]:
        case_clauses = " ".join([
            f"WHEN fonte_origem = '{platform}' THEN (metrics->'{field}'->>'dep')::numeric"
            for platform, field in mappings
        ])
        sql = text(f"""
            SELECT 
                AVG(CASE {case_clauses} END) as avg_val,
                MIN(CASE {case_clauses} END) as min_val,
                MAX(CASE {case_clauses} END) as max_val,
                COUNT(CASE WHEN { " OR ".join([f"(fonte_origem = '{platform}' AND metrics->'{field}' IS NOT NULL)" for platform, field in mappings]) } THEN 1 END) as cnt
            FROM genetics.genetic_evaluations
            {farm_filter_evals}
        """)
        row = db.execute(sql, params).fetchone()
        if row and row[3] > 0:
            weight_metrics[metric_name] = {
                "avg": round(float(row[0]), 2) if row[0] is not None else None,
                "min": round(float(row[1]), 2) if row[1] is not None else None,
                "max": round(float(row[2]), 2) if row[2] is not None else None,
                "count": row[3]
            }

    # Platform index averages
    index_sql = text(f"""
        SELECT 
            fonte_origem,
            AVG(indice_principal) as avg_idx,
            MIN(indice_principal) as min_idx,
            MAX(indice_principal) as max_idx,
            COUNT(*) as cnt
        FROM genetics.genetic_evaluations
        {farm_filter_evals}
        GROUP BY fonte_origem
    """)
    index_rows = db.execute(index_sql, params).fetchall()
    index_by_platform = {}
    labels = {"ANCP": "MGTe", "PMGZ": "IABCZ", "GENEPLUS": "IQG"}
    for r in index_rows:
        platform = r[0] or "unknown"
        index_by_platform[platform] = {
            "label": labels.get(platform, "Índice"),
            "avg": round(float(r[1]), 2) if r[1] is not None else None,
            "min": round(float(r[2]), 2) if r[2] is not None else None,
            "max": round(float(r[3]), 2) if r[3] is not None else None,
            "count": r[4]
        }

    # Top animals
    top_sql = text(f"""
        SELECT 
            a.rgn,
            a.nome,
            a.sexo,
            e.fonte_origem,
            e.indice_principal,
            e.percentil_principal
        FROM genetics.genetic_evaluations e
        JOIN genetics.animals a ON e.animal_id = a.id
        WHERE {"e.farm_id = :farm_id" if farm_id else "1=1"} AND e.indice_principal IS NOT NULL
        ORDER BY e.indice_principal DESC
        LIMIT 10
    """)
    top_rows = db.execute(top_sql, params).fetchall()
    top_animals = []
    for r in top_rows:
        platform = r[3] or "unknown"
        top_animals.append({
            "rgn": r[0],
            "nome": r[1] or "Sem Nome",
            "sexo": r[2] or "unknown",
            "fonte": platform,
            "indice": round(float(r[4]), 2) if r[4] is not None else None,
            "indice_label": labels.get(platform, "Índice"),
            "percentil": round(float(r[5]), 2) if r[5] is not None else None
        })

    # Breed averages comparison
    breed_avg_sql = text(f"""
        WITH latest_evals AS (
            SELECT 
                animal_id,
                indice_principal,
                fonte_origem,
                metrics,
                ROW_NUMBER() OVER(PARTITION BY animal_id ORDER BY safra DESC) as rn
            FROM genetics.genetic_evaluations
            {"WHERE farm_id = :farm_id" if farm_id else ""}
        )
        SELECT 
            COALESCE(NULLIF(a.raca, ''), 'Não Informado') as breed,
            AVG(le.indice_principal) as avg_idx,
            AVG(CASE 
                WHEN le.fonte_origem = 'PMGZ' THEN (le.metrics->'PD-EDg'->>'dep')::numeric
                WHEN le.fonte_origem = 'ANCP' THEN (le.metrics->'DP210'->>'dep')::numeric
                WHEN le.fonte_origem = 'GENEPLUS' THEN (le.metrics->'PD'->>'dep')::numeric
            END) as avg_p210,
            AVG(CASE 
                WHEN le.fonte_origem = 'PMGZ' THEN (le.metrics->'PA-EDg'->>'dep')::numeric
                WHEN le.fonte_origem = 'ANCP' THEN (le.metrics->'DP365'->>'dep')::numeric
            END) as avg_p365,
            AVG(CASE 
                WHEN le.fonte_origem = 'PMGZ' THEN (le.metrics->'PS-EDg'->>'dep')::numeric
                WHEN le.fonte_origem = 'ANCP' THEN (le.metrics->'DP450'->>'dep')::numeric
                WHEN le.fonte_origem = 'GENEPLUS' THEN (le.metrics->'PS'->>'dep')::numeric
            END) as avg_p450
        FROM genetics.animals a
        LEFT JOIN latest_evals le ON a.id = le.animal_id AND le.rn = 1
        WHERE {"a.farm_id = :farm_id" if farm_id else "1=1"}
        GROUP BY breed
    """)
    breed_avg_rows = db.execute(breed_avg_sql, params).fetchall()
    breed_averages = {}
    for r in breed_avg_rows:
        breed_averages[r[0]] = {
            "indice": round(float(r[1]), 2) if r[1] is not None else None,
            "p210": round(float(r[2]), 2) if r[2] is not None else None,
            "p365": round(float(r[3]), 2) if r[3] is not None else None,
            "p450": round(float(r[4]), 2) if r[4] is not None else None,
        }

    # Upload activity
    from backend.models import Upload
    now = datetime.now(timezone.utc)
    
    uploads_q = db.query(Upload)
    if farm_id:
        uploads_q = uploads_q.filter(Upload.id_farm == farm_id)
        
    l30 = uploads_q.filter(Upload.data_upload >= now - timedelta(days=30)).count()
    l60 = uploads_q.filter(Upload.data_upload >= now - timedelta(days=60)).count()
    l90 = uploads_q.filter(Upload.data_upload >= now - timedelta(days=90)).count()
    
    upload_activity = {
        "last_30d": l30,
        "last_60d": l60,
        "last_90d": l90
    }

    return {
        "summary": {
            "total_animals": total_animals,
            "total_evaluations": total_evaluations,
            "total_breeds": total_breeds,
            "genotyping_rate": genotyping_rate,
            "csg_rate": csg_rate,
            "platforms": platforms
        },
        "breed_distribution": breed_dist,
        "sex_distribution": sex_dist,
        "weight_metrics": weight_metrics,
        "index_by_platform": index_by_platform,
        "top_animals": top_animals,
        "breed_averages": breed_averages,
        "upload_activity": upload_activity
    }


def refresh_dashboard_cache_task(db: Session, farm_id_key: str):
    """Calcula as estatísticas e as salva fisicamente no banco de dados cache."""
    logger.info(f"Recalculating dashboard stats for cache key: {farm_id_key}")
    actual_farm_id = None if farm_id_key == "ALL" else farm_id_key
    
    try:
        stats_v2_data = compute_stats_v2_internal(db, actual_farm_id)
        platform_data = compute_platform_comparison_internal(db, actual_farm_id)
        analytics_data = compute_analytics_internal(db, actual_farm_id)
        
        cache_row = db.query(DashboardStatsCache).filter(DashboardStatsCache.farm_id == farm_id_key).first()
        if not cache_row:
            cache_row = DashboardStatsCache(farm_id=farm_id_key)
            db.add(cache_row)
        
        cache_row.stats_v2 = stats_v2_data
        cache_row.platform_comparison = platform_data
        cache_row.analytics = analytics_data
        cache_row.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        logger.info(f"Dashboard stats cache updated successfully for key: {farm_id_key}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error in refresh_dashboard_cache_task for {farm_id_key}: {e}", exc_info=True)


def refresh_dashboard_cache_background(farm_id_key: str):
    """Executa a tarefa de recálculo de cache com sua própria sessão DB (Thread-safe)."""
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        refresh_dashboard_cache_task(db, farm_id_key)
    except Exception as e:
        logger.error(f"Background cache refresh failed for {farm_id_key}: {e}")
    finally:
        db.close()


def get_cached_field(db: Session, farm_id_key: str, field_name: str, background_tasks: BackgroundTasks) -> dict:
    """Retorna o campo do cache. Roda stale-while-revalidate assincronamente se expirado."""
    cache_row = db.query(DashboardStatsCache).filter(DashboardStatsCache.farm_id == farm_id_key).first()
    
    # 1. Se não existe cache nenhum, cria na hora de forma síncrona
    if not cache_row:
        logger.info(f"Cache MISS for key: {farm_id_key}. Building synchronously...")
        refresh_dashboard_cache_task(db, farm_id_key)
        cache_row = db.query(DashboardStatsCache).filter(DashboardStatsCache.farm_id == farm_id_key).first()
        if cache_row:
            return getattr(cache_row, field_name)
        else:
            # Fallback seguro caso de algum erro na gravação
            actual_farm_id = None if farm_id_key == "ALL" else farm_id_key
            if field_name == "stats_v2":
                return compute_stats_v2_internal(db, actual_farm_id)
            elif field_name == "platform_comparison":
                return compute_platform_comparison_internal(db, actual_farm_id)
            else:
                return compute_analytics_internal(db, actual_farm_id)
                
    # 2. Se existe cache, checa se expirou (10 minutos)
    now = datetime.now(timezone.utc)
    updated_at = cache_row.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
        
    if now - updated_at > timedelta(minutes=10):
        logger.info(f"Cache STALE for key: {farm_id_key} (age: {now - updated_at}). Triggering background refresh...")
        background_tasks.add_task(refresh_dashboard_cache_background, farm_id_key)
        
    # Retorna o valor atual do cache imediatamente (super rápido!)
    return getattr(cache_row, field_name)


# ── Comparação Fazenda vs ANCP Top 10 ────────────────────────────
@router.get("/stats/ancp-comparison")
def get_ancp_comparison(
    farm_id: Optional[str] = Query(None),
    safra: Optional[int] = Query(None, description="Ano da safra para comparação"),
    fonte_origem: Optional[str] = Query(None, description="Filtro por plataforma: ANCP, PMGZ, GENEPLUS ou null para todas"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compara as médias da fazenda com as médias ANCP Top 10 na safra selecionada com suporte multiplataforma."""
    from backend.ancp_reference import ANCP_TOP10_AVERAGES, find_top_percentile

    # Determina farm_id efetivo
    effective_farm_id = None
    if farm_id and farm_id not in ["all", "todas"]:
        effective_farm_id = farm_id
    elif not farm_id and current_user.role != "admin" and current_user.id_farm:
        effective_farm_id = str(current_user.id_farm)

    # Safras disponíveis (2000 até 2026 conforme solicitado)
    available_safras = list(range(2000, 2027))

    # Lista de DEPs para comparação com mapeamento multiplataforma
    DEP_CONFIG = {
        "MGTe":    {"type": "indice"},
        "D3P":     {"ANCP": "D3P"},
        "DIPP":    {"ANCP": "DIPP", "PMGZ": "IPPg", "GENEPLUS": "IPP"},
        "DPE365":  {"ANCP": "DPE365", "PMGZ": "PE-365g", "GENEPLUS": "PES"},
        "DPE450":  {"ANCP": "DPE450"},
        "DPN":     {"ANCP": "DPN", "PMGZ": "PN-EDg", "GENEPLUS": "PN"},
        "DSTAY":   {"ANCP": "DSTAY", "PMGZ": "STAYg", "GENEPLUS": "STAY"},
        "DSTAY54": {"ANCP": "DSTAY54"},
        "MP120":   {"ANCP": "MP120"},
        "DP210":   {"ANCP": "DP210", "PMGZ": "PD-EDg", "GENEPLUS": "PD"},
        "DP450":   {"ANCP": "DP450", "PMGZ": "PS-EDg", "GENEPLUS": "PS"},
        "DAOL":    {"ANCP": "DAOL", "PMGZ": "AOLg", "GENEPLUS": "AOL"},
        "DACAB":   {"ANCP": "DACAB", "PMGZ": "ACABg", "GENEPLUS": "EGS"},
        "DMAR":    {"ANCP": "DMAR", "PMGZ": "MARg", "GENEPLUS": "MAR"},
    }

    # Busca safras disponíveis na fazenda
    farm_filter = ""
    params = {}
    if effective_farm_id:
        farm_filter = "AND ge.farm_id = :farm_id"
        params["farm_id"] = effective_farm_id

    platform_filter = ""
    if fonte_origem:
        platform_filter = "AND ge.fonte_origem = :fonte"
        params["fonte"] = fonte_origem

    # Busca safras baseadas nos filtros
    safras_sql = text(f"""
        SELECT DISTINCT safra FROM genetics.genetic_evaluations ge
        WHERE 1=1 {farm_filter} {platform_filter}
        ORDER BY safra DESC
    """)
    farm_safras = [r[0] for r in db.execute(safras_sql, params).fetchall()]

    # Se não especificou safra, usa a mais recente
    target_safra = safra if safra else (farm_safras[0] if farm_safras else 2024)

    # Referência ANCP Top 10 para a safra (com limites entre 2015 e 2024)
    ref_safra = target_safra
    if ref_safra < 2015:
        ref_safra = 2015
    elif ref_safra > 2024:
        ref_safra = 2024
    ancp_ref = ANCP_TOP10_AVERAGES.get(ref_safra, {})

    # Determina as plataformas ativas para calcular as médias da fazenda
    active_platforms = [fonte_origem] if fonte_origem else ["ANCP", "PMGZ", "GENEPLUS"]

    # Calcula médias da fazenda para cada DEP
    dep_cases = []
    for dep, config in DEP_CONFIG.items():
        if config.get("type") == "indice":
            cases = []
            for platform in active_platforms:
                cases.append(f"WHEN ge.fonte_origem = '{platform}' THEN ge.indice_principal")
            if cases:
                cases_sql = " ".join(cases)
                dep_cases.append(f"AVG(CASE {cases_sql} END) as avg_{dep}")
            else:
                dep_cases.append(f"NULL as avg_{dep}")
        else:
            cases = []
            for platform in active_platforms:
                json_key = config.get(platform)
                if json_key:
                    cases.append(f"WHEN ge.fonte_origem = '{platform}' THEN (ge.metrics->'{json_key}'->>'dep')::numeric")
            if cases:
                cases_sql = " ".join(cases)
                dep_cases.append(f"AVG(CASE {cases_sql} END) as avg_{dep}")
            else:
                dep_cases.append(f"NULL as avg_{dep}")

    fields = ", ".join(dep_cases)
    avg_sql = text(f"""
        SELECT {fields}
        FROM genetics.genetic_evaluations ge
        WHERE safra = :safra {farm_filter} {platform_filter}
    """)
    params["safra"] = target_safra
    row = db.execute(avg_sql, params).fetchone()

    comparisons = {}
    if row:
        row_dict = row._asdict() if hasattr(row, "_asdict") else {}
        for dep in DEP_CONFIG.keys():
            col_name = f"avg_{dep}"
            farm_avg = row_dict.get(col_name.lower()) or row_dict.get(col_name)
            farm_avg_float = round(float(farm_avg), 3) if farm_avg is not None else None

            ancp_val = ancp_ref.get(dep)
            diff_pct = None
            if farm_avg_float is not None and ancp_val is not None and ancp_val != 0:
                diff_pct = round(((farm_avg_float - ancp_val) / abs(ancp_val)) * 100, 2)

            top_val = find_top_percentile(dep, farm_avg_float) if farm_avg_float is not None else None

            comparisons[dep] = {
                "fazenda_avg": farm_avg_float,
                "ancp_top10": ancp_val,
                "diff_pct": diff_pct,
                "top": top_val,
            }

    return {
        "safra": target_safra,
        "available_safras": available_safras,
        "farm_safras": farm_safras,
        "comparisons": comparisons,
    }


# ── Desempenho de DEPs (gráfico + tabela com TOP) ───────────────
@router.get("/stats/dep-performance")
def get_dep_performance(
    farm_id: Optional[str] = Query(None),
    fonte_origem: Optional[str] = Query(None, description="Filtro por plataforma: ANCP, PMGZ, GENEPLUS ou null para todas"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna avg/min/max de todas as DEPs com TOP percentil da média."""
    from backend.ancp_reference import find_top_percentile

    effective_farm_id = None
    if farm_id and farm_id not in ["all", "todas"]:
        effective_farm_id = farm_id
    elif not farm_id and current_user.role != "admin" and current_user.id_farm:
        effective_farm_id = str(current_user.id_farm)

    # Mapeamento de DEPs por plataforma (chaves no JSONB metrics)
    DEP_CONFIG = {
        "MGTe":    {"type": "indice", "label": "Mérito Genético Total"},
        "D3P":     {"ANCP": "D3P", "label": "Prob. Parto aos 3 anos"},
        "DIPP":    {"ANCP": "DIPP", "PMGZ": "IPPg", "GENEPLUS": "IPP", "label": "Idade 1º Parto"},
        "DPE365":  {"ANCP": "DPE365", "PMGZ": "PE-365g", "GENEPLUS": "PES", "label": "Perímetro Escrotal 365d"},
        "DPE450":  {"ANCP": "DPE450", "label": "Perímetro Escrotal 450d"},
        "DPN":     {"ANCP": "DPN", "PMGZ": "PN-EDg", "GENEPLUS": "PN", "label": "Peso Nascimento"},
        "DSTAY":   {"ANCP": "DSTAY", "PMGZ": "STAYg", "GENEPLUS": "STAY", "label": "Stayability"},
        "DSTAY54": {"ANCP": "DSTAY54", "label": "Stayability 54 meses"},
        "MP120":   {"ANCP": "MP120", "label": "Mat. Peso 120d"},
        "DP210":   {"ANCP": "DP210", "PMGZ": "PD-EDg", "GENEPLUS": "PD", "label": "Peso Desmama 210d"},
        "DP450":   {"ANCP": "DP450", "PMGZ": "PS-EDg", "GENEPLUS": "PS", "label": "Peso Sobreano 450d"},
        "DAOL":    {"ANCP": "DAOL", "PMGZ": "AOLg", "GENEPLUS": "AOL", "label": "Área Olho Lombo"},
        "DACAB":   {"ANCP": "DACAB", "PMGZ": "ACABg", "GENEPLUS": "EGS", "label": "Acabamento"},
        "DMAR":    {"ANCP": "DMAR", "PMGZ": "MARg", "GENEPLUS": "MAR", "label": "Marmoreio"},
    }

    filters = []
    params = {}

    if effective_farm_id:
        filters.append("ge.farm_id = :farm_id")
        params["farm_id"] = effective_farm_id

    if fonte_origem:
        filters.append("ge.fonte_origem = :fonte")
        params["fonte"] = fonte_origem

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""

    # Determina quais plataformas considerar
    active_platforms = [fonte_origem] if fonte_origem else ["ANCP", "PMGZ", "GENEPLUS"]

    select_parts = []
    for dep_name, config in DEP_CONFIG.items():
        if config.get("type") == "indice":
            # MGTe = indice_principal para ANCP
            cases = []
            if "ANCP" in active_platforms:
                cases.append("WHEN ge.fonte_origem = 'ANCP' THEN ge.indice_principal")
            cases_sql = " ".join(cases) if cases else "WHEN 1=0 THEN NULL"
            select_parts.append(f"AVG(CASE {cases_sql} END) as avg_{dep_name}")
            select_parts.append(f"MIN(CASE {cases_sql} END) as min_{dep_name}")
            select_parts.append(f"MAX(CASE {cases_sql} END) as max_{dep_name}")
            select_parts.append(f"COUNT(CASE {cases_sql} END) as cnt_{dep_name}")
        else:
            cases = []
            for platform in active_platforms:
                json_key = config.get(platform)
                if json_key:
                    cases.append(f"WHEN ge.fonte_origem = '{platform}' THEN (ge.metrics->'{json_key}'->>'dep')::numeric")
            if not cases:
                select_parts.append(f"NULL as avg_{dep_name}")
                select_parts.append(f"NULL as min_{dep_name}")
                select_parts.append(f"NULL as max_{dep_name}")
                select_parts.append(f"0 as cnt_{dep_name}")
                continue
            cases_sql = " ".join(cases)
            select_parts.append(f"AVG(CASE {cases_sql} END) as avg_{dep_name}")
            select_parts.append(f"MIN(CASE {cases_sql} END) as min_{dep_name}")
            select_parts.append(f"MAX(CASE {cases_sql} END) as max_{dep_name}")
            select_parts.append(f"COUNT(CASE {cases_sql} END) as cnt_{dep_name}")

    fields_clause = ",\n            ".join(select_parts)
    sql = text(f"""
        SELECT {fields_clause}
        FROM genetics.genetic_evaluations ge
        {where_clause}
    """)

    row = db.execute(sql, params).fetchone()
    dep_metrics = {}

    if row:
        row_dict = row._asdict() if hasattr(row, "_asdict") else {}
        for dep_name, config in DEP_CONFIG.items():
            avg_val = row_dict.get(f"avg_{dep_name}") or row_dict.get(f"avg_{dep_name}".lower())
            min_val = row_dict.get(f"min_{dep_name}") or row_dict.get(f"min_{dep_name}".lower())
            max_val = row_dict.get(f"max_{dep_name}") or row_dict.get(f"max_{dep_name}".lower())
            cnt_val = row_dict.get(f"cnt_{dep_name}") or row_dict.get(f"cnt_{dep_name}".lower()) or 0

            avg_float = round(float(avg_val), 3) if avg_val is not None else None
            top_val = find_top_percentile(dep_name, avg_float) if avg_float is not None else None

            dep_metrics[dep_name] = {
                "avg": avg_float,
                "min": round(float(min_val), 3) if min_val is not None else None,
                "max": round(float(max_val), 3) if max_val is not None else None,
                "count": int(cnt_val),
                "top": top_val,
                "label": config.get("label", dep_name),
            }

    return {"dep_metrics": dep_metrics}


# ── Estatísticas por plataforma (Dashboard Overview) ──────────
@router.get("/stats/platform-comparison")
def get_platform_comparison_stats(
    farm_id: Optional[str] = Query(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna médias, min e max por plataforma para o gráfico comparativo do dashboard."""
    if farm_id:
        farm_id_key = farm_id
    elif current_user.role != "admin" and current_user.id_farm:
        farm_id_key = str(current_user.id_farm)
    else:
        farm_id_key = "ALL"

    return get_cached_field(db, farm_id_key, "platform_comparison", background_tasks)


@router.get("/stats/by-farm")
def get_stats_by_farm(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farms = db.query(
        GeneticsFarm.id,
        GeneticsFarm.nome,
        func.count(GeneticsAnimal.id).label("total_animals")
    ).outerjoin(
        GeneticsAnimal, GeneticsAnimal.farm_id == GeneticsFarm.id
    ).group_by(
        GeneticsFarm.id, GeneticsFarm.nome
    ).all()

    return [
        {
            "farm_id": str(f.id),
            "farm_name": f.nome,
            "total_animals": f.total_animals,
        }
        for f in farms
    ]


@router.get("/stats/ranking")
def get_animal_ranking(
    farm_id: Optional[str] = Query(None),
    metric: str = Query("iabczg"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subquery = db.query(
        GeneticsGeneticEvaluation.animal_id,
        GeneticsGeneticEvaluation.iabczg,
        func.row_number().over(
            partition_by=GeneticsGeneticEvaluation.animal_id,
            order_by=GeneticsGeneticEvaluation.safra.desc()
        ).label("rn")
    ).subquery()

    query = db.query(
        GeneticsAnimal.id,
        GeneticsAnimal.rgn,
        GeneticsAnimal.nome,
        GeneticsAnimal.sexo,
        subquery.c.iabczg
    ).join(
        subquery, subquery.c.animal_id == GeneticsAnimal.id
    ).filter(subquery.c.rn == 1)

    if farm_id:
        query = query.filter(GeneticsAnimal.farm_id == farm_id)
    if metric == "iabczg":
        query = query.order_by(subquery.c.iabczg.desc())

    results = query.limit(limit).all()

    return [
        {
            "animal_id": str(r.id),
            "rgn": r.rgn,
            "nome": r.nome,
            "sexo": r.sexo,
            "iabczg": float(r.iabczg) if r.iabczg else None,
        }
        for r in results
    ]


@router.get("/stats")
def get_stats_v2(
    farm_id: Optional[str] = Query(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Estatísticas do dashboard vindas do schema genetics."""
    if farm_id:
        farm_id_key = farm_id
    elif current_user.role != "admin" and current_user.id_farm:
        farm_id_key = str(current_user.id_farm)
    else:
        farm_id_key = "ALL"

    return get_cached_field(db, farm_id_key, "stats_v2", background_tasks)


@router.get("/stats/analytics")
def get_analytics_stats(
    farm_id: Optional[str] = Query(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna estatísticas detalhadas e profundas sobre as avaliações genéticas e animais."""
    if farm_id and farm_id not in ["all", "todas"]:
        farm_id_key = farm_id
    elif not farm_id and current_user.role != "admin" and current_user.id_farm:
        farm_id_key = str(current_user.id_farm)
    else:
        farm_id_key = "ALL"

    return get_cached_field(db, farm_id_key, "analytics", background_tasks)


# ============================================================
# LISTAGEM
# ============================================================

@router.get("")
def list_animals(
    farm_id: Optional[str] = Query(None),
    fonte_origem: Optional[str] = Query(None),  # 'PMGZ' ou 'ANCP'
    sexo: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(GeneticsAnimal)

    # Filtro por Fonte (Plataforma) via subquery para evitar duplicidade
    if fonte_origem:
        from sqlalchemy import exists
        query = query.filter(
            exists().where(
                (GeneticsGeneticEvaluation.animal_id == GeneticsAnimal.id) &
                (GeneticsGeneticEvaluation.fonte_origem == fonte_origem)
            )
        )

    if farm_id:
        query = query.filter(GeneticsAnimal.farm_id == farm_id)
    elif current_user.role != "admin" and current_user.id_farm:
        query = query.filter(GeneticsAnimal.farm_id == current_user.id_farm)

    if sexo:
        query = query.filter(GeneticsAnimal.sexo == sexo)
    if search:
        query = query.filter(
            (GeneticsAnimal.rgn.ilike(f"%{search}%"))
            | (GeneticsAnimal.nome.ilike(f"%{search}%"))
        )

    total = query.count()
    animals = query.order_by(GeneticsAnimal.rgn).offset(offset).limit(limit).all()

    # Pre-fetch genetic evaluations for all returned animals in a single query
    animal_ids = [a.id for a in animals]
    all_evals = []
    if animal_ids:
        evals_query = db.query(GeneticsGeneticEvaluation).filter(GeneticsGeneticEvaluation.animal_id.in_(animal_ids))
        if fonte_origem:
            evals_query = evals_query.filter(GeneticsGeneticEvaluation.fonte_origem == fonte_origem)
        all_evals = evals_query.order_by(GeneticsGeneticEvaluation.safra.desc()).all()

    # Group evaluations by animal_id in memory
    from collections import defaultdict
    evals_by_animal = defaultdict(list)
    for ev in all_evals:
        evals_by_animal[ev.animal_id].append(ev)

    results = []
    for a in animals:
        animal_evals = evals_by_animal[a.id]
        latest_eval = animal_evals[0] if animal_evals else None
        
        animal_dict = animal_to_dict(a, latest_eval)
        animal_dict["evaluations"] = [eval_to_dict(e) for e in animal_evals]
        results.append(animal_dict)

    return {"total": total, "limit": limit, "offset": offset, "data": results}


@router.delete("/bulk", status_code=204)
def bulk_delete_animals(
    animal_ids: list[str] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exclui múltiplos animais e suas avaliações genéticas."""
    if not animal_ids:
        raise HTTPException(status_code=400, detail="Nenhum ID de animal fornecido")
    
    import uuid as _uuid
    try:
        uuids = [_uuid.UUID(aid) for aid in animal_ids]
    except ValueError:
        raise HTTPException(status_code=400, detail="Um ou mais IDs são inválidos")
    
    # Buscar animais para verificar permissão
    animals = db.query(GeneticsAnimal).filter(GeneticsAnimal.id.in_(uuids)).all()
    if not animals:
        raise HTTPException(status_code=404, detail="Animais não encontrados")
    
    # Verificar permissão
    for animal in animals:
        if current_user.role != "admin" and str(animal.farm_id) != str(current_user.id_farm):
            raise HTTPException(status_code=403, detail=f"Acesso negado para o animal {animal.rgn}")
    
    # Coleta fazendas afetadas antes de commitar/invalidar
    farm_ids = list(set(str(a.farm_id) for a in animals if a.farm_id))

    # Excluir avaliações primeiro
    db.query(GeneticsGeneticEvaluation).filter(GeneticsGeneticEvaluation.animal_id.in_(uuids)).delete(synchronize_session=False)
    
    # Excluir animais
    db.query(GeneticsAnimal).filter(GeneticsAnimal.id.in_(uuids)).delete(synchronize_session=False)
    
    db.commit()

    try:
        import threading
        for fid in farm_ids:
            threading.Thread(target=refresh_dashboard_cache_background, args=(fid,), daemon=True).start()
        threading.Thread(target=refresh_dashboard_cache_background, args=("ALL",), daemon=True).start()
    except Exception as cache_err:
        logger.error(f"Failed to trigger cache refresh after bulk delete: {cache_err}")

    return None


# ============================================================
# ROTA DINÂMICA — DEVE VIR POR ÚLTIMO
# ============================================================

@router.get("/{animal_id}")
def get_animal(
    animal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        import uuid as _uuid
        animal_uuid = _uuid.UUID(animal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"ID inválido: '{animal_id}' não é um UUID válido")

    animal = db.query(GeneticsAnimal).filter(GeneticsAnimal.id == animal_uuid).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")

    evaluations = (
        db.query(GeneticsGeneticEvaluation)
        .filter(GeneticsGeneticEvaluation.animal_id == animal.id)
        .order_by(GeneticsGeneticEvaluation.safra.desc())
        .all()
    )

    result = animal_to_dict(animal)
    result["evaluations"] = [eval_to_dict(e) for e in evaluations]
    return result