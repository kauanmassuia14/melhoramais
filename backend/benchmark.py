from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timezone
import statistics
import json
from uuid import UUID

from .database import get_db, get_max_completed_safra
from .models import GeneticsAnimal, GeneticsFarm, GeneticsGeneticEvaluation, User
from .auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


# Platform metadata
PLATFORMS = {
    "ANCP": {
        "name": "ANCP",
        "description": "Associação Nacional de Criadores e Prodembros",
        "index_column": "anc_mg",  # Main index column for sorting (legacy)
        "index_name": "MG (Média Genética)",
        "characteristics": [
            {"code": "mg", "name": "Média Genética", "column": "anc_mg", "description": "Média ponderada das DEPs do animal. Quanto maior, melhor o valor genético."},
            {"code": "te", "name": "Tamanho", "column": "anc_te", "description": "DEP de tamanho adulto (cm). Previsão do tamanho dos descendentes."},
            {"code": "m", "name": "Maternidade", "column": "anc_m", "description": "DEP de habilidade materna. Previsão do peso dos bezerros ao desmame via matrizes."},
            {"code": "p", "name": "Peso", "column": "anc_p", "description": "DEP de peso. Previsão do peso dos descendentes."},
            {"code": "dp", "name": "Desvio Padrão", "column": "anc_dp", "description": "Precisão da estimativa (quanto menor, mais preciso)."},
            {"code": "sp", "name": "Sobreano", "column": "anc_sp", "description": "DEP de peso aos 365 dias. Previsão do peso aos 365 dias dos descendentes."},
            {"code": "e", "name": "Eficiência", "column": "anc_e", "description": "DEP de eficiência alimentar. Previsão da conversão alimentar dos descendentes."},
            {"code": "sao", "name": "Área Olho Lombo", "column": "anc_sao", "description": "DEP de área de olho de lombo (cm²). Previsão da musculosidade dos descendentes."},
            {"code": "leg", "name": "Legume", "column": "anc_leg", "description": "DEP de gordura (mm). Previsão da espessura de gordura dos descendentes."},
            {"code": "sh", "name": "Sexo Hack", "column": "anc_sh", "description": "DEP de sexo hack. Previsão da proporção de machos/fêmeas nos descendentes."},
            {"code": "pp30", "name": "Produção Prioritária 30", "column": "anc_pp30", "description": "DEP de produção prioritária 30. Índice composto de características econômicas."},
        ]
    },
    "GENEPLUS": {
        "name": "GENEPLUS",
        "description": "Sistema de melhoramento genético",
        "index_column": "gen_iqg",
        "index_name": "IQG (Índice Qualidade Genética)",
        "characteristics": [
            {"code": "iqg", "name": "Índice Qualidade Genética", "column": "gen_iqg", "description": "Índice composto que resume a qualidade genética geral do animal."},
            {"code": "pmm", "name": "Peso Maternidade", "column": "gen_pmm", "description": "DEP de peso materno. Previsão do peso dos bezerros ao desmame."},
            {"code": "p", "name": "Peso", "column": "gen_p", "description": "DEP de peso. Previsão do peso dos descendentes."},
            {"code": "dp", "name": "Desvio Padrão", "column": "gen_dp", "description": "Precisão da estimativa (quanto menor, mais preciso)."},
            {"code": "sp", "name": "Sobreano", "column": "gen_sp", "description": "DEP de peso aos 365 dias. Previsão do peso aos 365 dias dos descendentes."},
            {"code": "e", "name": "Eficiência", "column": "gen_e", "description": "DEP de eficiência alimentar. Previsão da conversão alimentar dos descendentes."},
            {"code": "sao", "name": "Área Olho Lombo", "column": "gen_sao", "description": "DEP de área de olho de lombo (cm²). Previsão da musculosidade dos descendentes."},
            {"code": "leg", "name": "Legume", "column": "gen_leg", "description": "DEP de gordura (mm). Previsão da espessura de gordura dos descendentes."},
            {"code": "sh", "name": "Sexo Hack", "column": "gen_sh", "description": "DEP de sexo hack. Previsão da proporção de machos/fêmeas nos descendentes."},
            {"code": "pp30", "name": "Produção Prioritária 30", "column": "gen_pp30", "description": "DEP de produção prioritária 30. Índice composto de características econômicas."},
        ]
    },
    "PMGZ": {
        "name": "PMGZ",
        "description": "Programa de Melhoramento Genético Zootécnico",
        "index_column": "pmg_iabc",
        "index_name": "IABCZ (Índice ABCZ)",
        "characteristics": [
            {"code": "iabc", "name": "Índice ABCZ", "column": "pmg_iabc", "description": "Índice composto da ABCZ que resume a qualidade genética geral."},
            {"code": "zpmm", "name": "Zootecnia Peso Materno", "column": "pmg_zpmm", "description": "DEP de peso materno. Previsão do peso dos bezerros ao desmame."},
            {"code": "p", "name": "Peso", "column": "pmg_p", "description": "DEP de peso. Previsão do peso dos descendentes."},
            {"code": "dp", "name": "Desvio Padrão", "column": "pmg_dp", "description": "Precisão da estimativa (quanto menor, mais preciso)."},
            {"code": "sp", "name": "Sobreano", "column": "pmg_sp", "description": "DEP de peso aos 365 dias. Previsão do peso aos 365 dias dos descendentes."},
            {"code": "e", "name": "Eficiência", "column": "pmg_e", "description": "DEP de eficiência alimentar. Previsão da conversão alimentar dos descendentes."},
            {"code": "sao", "name": "Área Olho Lombo", "column": "pmg_sao", "description": "DEP de área de olho de lombo (cm²). Previsão da musculosidade dos descendentes."},
            {"code": "leg", "name": "Legume", "column": "pmg_leg", "description": "DEP de gordura (mm). Previsão da espessura de gordura dos descendentes."},
            {"code": "sh", "name": "Sexo Hack", "column": "pmg_sh", "description": "DEP de sexo hack. Previsão da proporção de machos/fêmeas nos descendentes."},
            {"code": "pp30", "name": "Produção Prioritária 30", "column": "pmg_pp30", "description": "DEP de produção prioritária 30. Índice composto de características econômicas."},
        ]
    }
}


def normalize_char_code(char_code: str) -> str:
    code = char_code.lower()
    for prefix in ("anc_", "gen_", "pmg_"):
        if code.startswith(prefix):
            return code[len(prefix):]
    return code


def get_evaluation_value(evaluation: GeneticsGeneticEvaluation, char_code: str) -> Optional[float]:
    metrics = evaluation.metrics if isinstance(evaluation.metrics, dict) else {}
    char_code_lower = normalize_char_code(char_code)
    
    # 1. Main Indices
    if char_code_lower in ("mg", "iqg", "iabc"):
        if evaluation.indice_principal is not None:
            return float(evaluation.indice_principal)
            
    # 2. Platform-specific mappings
    platform = evaluation.fonte_origem
    keys_to_try = []
    
    if platform == "ANCP":
        if char_code_lower == "mg":
            keys_to_try = ["MGTe", "MG"]
        elif char_code_lower == "te":
            keys_to_try = ["TE"]
        elif char_code_lower == "m":
            keys_to_try = ["MP120", "DIPM"]
        elif char_code_lower == "p":
            keys_to_try = ["DP210", "DP120"]
        elif char_code_lower == "sp":
            keys_to_try = ["DP450", "DP365"]
        elif char_code_lower == "e":
            keys_to_try = ["CAR", "IMS"]
        elif char_code_lower == "sao":
            keys_to_try = ["DAOL"]
        elif char_code_lower == "leg":
            keys_to_try = ["DACAB"]
        elif char_code_lower == "pp30":
            keys_to_try = ["D3P"]
    elif platform == "GENEPLUS":
        if char_code_lower == "iqg":
            keys_to_try = ["IQG"]
        elif char_code_lower == "pmm":
            keys_to_try = ["PMm"]
        elif char_code_lower == "p":
            keys_to_try = ["PD", "PD120"]
        elif char_code_lower == "sp":
            keys_to_try = ["PS"]
        elif char_code_lower == "e":
            keys_to_try = ["CAR"]
        elif char_code_lower == "sao":
            keys_to_try = ["AOL"]
        elif char_code_lower == "leg":
            keys_to_try = ["EGS", "ACAB"]
        elif char_code_lower == "pp30":
            keys_to_try = ["PP30"]
    elif platform == "PMGZ":
        if char_code_lower == "iabc":
            keys_to_try = ["IABCZ"]
        elif char_code_lower == "zpmm":
            keys_to_try = ["PM-EMg"]
        elif char_code_lower == "p":
            keys_to_try = ["PD-EDg"]
        elif char_code_lower == "sp":
            keys_to_try = ["PS-EDg"]
        elif char_code_lower == "sao":
            keys_to_try = ["AOLg"]
        elif char_code_lower == "leg":
            keys_to_try = ["ACABg"]
            
    # Try defined keys in metrics
    for k in keys_to_try:
        metric_block = metrics.get(k)
        if isinstance(metric_block, dict):
            val = metric_block.get("dep")
            if val is not None:
                return float(val)
                
    # Generic fallback: search keys case-insensitively
    for k, block in metrics.items():
        if k.lower() == char_code_lower and isinstance(block, dict):
            val = block.get("dep")
            if val is not None:
                return float(val)
                
    return None


@router.get("/platforms")
async def get_platforms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get available benchmarking platforms"""
    platforms = []
    for key, platform in PLATFORMS.items():
        platforms.append({
            "code": key,
            "name": platform["name"],
            "description": platform["description"],
            "characteristics_count": len(platform["characteristics"])
        })
    return platforms


@router.get("/characteristics/{platform_code}")
async def get_characteristics(
    platform_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get characteristics for a specific platform"""
    if platform_code not in PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Platform {platform_code} not found")
    
    platform = PLATFORMS[platform_code]
    return {
        "platform": platform["name"],
        "characteristics": platform["characteristics"]
    }


@router.get("/groups")
async def get_benchmark_groups(
    platform_code: str = Query(..., description="Platform code (ANCP, GENEPLUS, PMGZ)"),
    characteristic: str = Query(..., description="Characteristic code (mg, te, etc.)"),
    start_date: Optional[date] = Query(None, description="Start date for filter"),
    end_date: Optional[date] = Query(None, description="End date for filter"),
    sexo: Optional[str] = Query(None, description="Sex filter (M, F)"),
    situacao: Optional[str] = Query(None, description="Status filter (ATIVO, INATIVO)"),
    farm_id: Optional[str] = Query(None, description="Farm ID filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get benchmark groups (Top 5 clients, all clients, general average)"""
    
    if platform_code not in PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Platform {platform_code} not found")
    
    platform = PLATFORMS[platform_code]
    
    # Find the column for the characteristic
    char_info = None
    for char in platform["characteristics"]:
        if char["code"] == characteristic:
            char_info = char
            break
    
    if not char_info:
        raise HTTPException(status_code=404, detail=f"Characteristic {characteristic} not found")
    
    # Base query for GeneticsAnimal
    query = db.query(GeneticsAnimal)
    
    # Apply filters
    if farm_id:
        query = query.filter(GeneticsAnimal.farm_id == farm_id)
    elif current_user.role != "admin" and current_user.id_farm:
        query = query.filter(GeneticsAnimal.farm_id == str(current_user.id_farm))
    
    if sexo:
        query = query.filter(GeneticsAnimal.sexo == sexo)
    
    if start_date:
        query = query.filter(GeneticsAnimal.nascimento >= start_date)
    if end_date:
        query = query.filter(GeneticsAnimal.nascimento <= end_date)
    
    all_animals = query.all()
    if not all_animals:
        return {
            "platform": platform_code,
            "characteristic": char_info["name"],
            "groups": [],
            "total_animals": 0
        }
        
    animal_ids = [a.id for a in all_animals]
    max_safra = get_max_completed_safra()
    
    # Fetch all evaluations for these animals
    evals = db.query(GeneticsGeneticEvaluation).filter(
        GeneticsGeneticEvaluation.animal_id.in_(animal_ids),
        GeneticsGeneticEvaluation.fonte_origem == platform_code,
        GeneticsGeneticEvaluation.safra <= max_safra
    ).order_by(
        GeneticsGeneticEvaluation.safra.desc(),
        GeneticsGeneticEvaluation.created_at.desc()
    ).all()
    
    # Map to latest eval per animal in memory
    eval_map = {}
    for ev in evals:
        if ev.animal_id not in eval_map:
            eval_map[ev.animal_id] = ev
            
    # Compile animals that actually have a value for this characteristic
    animals_with_val = []
    for animal in all_animals:
        ev = eval_map.get(animal.id)
        if ev:
            val = get_evaluation_value(ev, characteristic)
            if val is not None:
                animals_with_val.append((animal, val))
                
    if not animals_with_val:
        return {
            "platform": platform_code,
            "characteristic": char_info["name"],
            "groups": [],
            "total_animals": 0
        }
        
    # Calculate general average (Group C)
    values = [val for _, val in animals_with_val]
    general_avg = statistics.mean(values) if values else 0
    general_std = statistics.stdev(values) if len(values) > 1 else 0
    
    # Group by farm to get "clients"
    farm_groups = {}
    for animal, val in animals_with_val:
        f_id = str(animal.farm_id) if animal.farm_id else None
        if not f_id:
            continue
        if f_id not in farm_groups:
            farm_groups[f_id] = []
        farm_groups[f_id].append(val)
        
    # Calculate average per farm
    farm_averages = []
    for f_id, farm_values in farm_groups.items():
        farm_avg = statistics.mean(farm_values)
        farm_averages.append({
            "farm_id": f_id,
            "average": farm_avg,
            "count": len(farm_values)
        })
        
    # Sort by average descending
    farm_averages.sort(key=lambda x: x["average"], reverse=True)
    
    # Top 5 farms (Group A)
    top_5_farms = farm_averages[:5]
    
    # All farms average (Group B)
    all_farms_avg = statistics.mean([fa["average"] for fa in farm_averages]) if farm_averages else 0
    all_farms_count = len(farm_averages)
    
    # Get farm names
    farm_names = {}
    farm_uuids = [UUID(fa["farm_id"]) for fa in farm_averages if fa["farm_id"]]
    if farm_uuids:
        farms = db.query(GeneticsFarm).filter(GeneticsFarm.id.in_(farm_uuids)).all()
        for farm in farms:
            farm_names[str(farm.id)] = farm.nome
            
    # Build response
    groups = []
    
    # Group A: Top 5
    top_5_total = 0
    top_5_avg = 0
    if top_5_farms:
        top_5_total = sum([fa["count"] for fa in top_5_farms])
        top_5_avg = statistics.mean([fa["average"] for fa in top_5_farms])
        
    groups.append({
        "name": "Top 5 Clientes",
        "description": "5 clientes com maior média do índice principal",
        "average": round(top_5_avg, 3),
        "count": top_5_total,
        "farms": [
            {
                "id": fa["farm_id"],
                "name": farm_names.get(fa["farm_id"], f"Fazenda {fa['farm_id']}"),
                "average": round(fa["average"], 3),
                "animal_count": fa["count"]
            }
            for fa in top_5_farms
        ]
    })
    
    # Group B: All clients
    groups.append({
        "name": "Todos os Clientes",
        "description": "Todos os clientes cadastrados no sistema",
        "average": round(all_farms_avg, 3),
        "count": len(animals_with_val),
        "farm_count": all_farms_count
    })
    
    # Group C: General average
    groups.append({
        "name": "Média Geral",
        "description": "Média geral do banco de dados (base de comparação)",
        "average": round(general_avg, 3),
        "std_dev": round(general_std, 3),
        "count": len(values)
    })
    
    return {
        "platform": platform_code,
        "characteristic": char_info["name"],
        "characteristic_description": char_info["description"],
        "groups": groups,
        "total_animals": len(animals_with_val),
        "total_farms": all_farms_count
    }


@router.get("/compare")
async def compare_characteristics(
    platform_code: str = Query(..., description="Platform code"),
    characteristics: str = Query(..., description="Comma-separated characteristic codes"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    sexo: Optional[str] = Query(None),
    farm_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare multiple characteristics across groups"""
    
    if platform_code not in PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Platform {platform_code} not found")
    
    platform = PLATFORMS[platform_code]
    char_codes = [c.strip() for c in characteristics.split(",")]
    
    # Validate characteristics
    char_map = {}
    for char in platform["characteristics"]:
        if char["code"] in char_codes:
            char_map[char["code"]] = char
            
    if not char_map:
        raise HTTPException(status_code=400, detail="No valid characteristics provided")
        
    # Base query for GeneticsAnimal
    query = db.query(GeneticsAnimal)
    if farm_id:
        query = query.filter(GeneticsAnimal.farm_id == farm_id)
    elif current_user.role != "admin" and current_user.id_farm:
        query = query.filter(GeneticsAnimal.farm_id == str(current_user.id_farm))
        
    if sexo:
        query = query.filter(GeneticsAnimal.sexo == sexo)
    if start_date:
        query = query.filter(GeneticsAnimal.nascimento >= start_date)
    if end_date:
        query = query.filter(GeneticsAnimal.nascimento <= end_date)
        
    animals = query.all()
    if not animals:
        return {"message": "No animals found with the selected characteristics"}
        
    # Get latest evaluations
    animal_ids = [a.id for a in animals]
    max_safra = get_max_completed_safra()
    
    evals = db.query(GeneticsGeneticEvaluation).filter(
        GeneticsGeneticEvaluation.animal_id.in_(animal_ids),
        GeneticsGeneticEvaluation.fonte_origem == platform_code,
        GeneticsGeneticEvaluation.safra <= max_safra
    ).order_by(
        GeneticsGeneticEvaluation.safra.desc(),
        GeneticsGeneticEvaluation.created_at.desc()
    ).all()
    
    # Map to latest eval per animal in memory
    eval_map = {}
    for ev in evals:
        if ev.animal_id not in eval_map:
            eval_map[ev.animal_id] = ev
            
    # Calculate statistics for each characteristic
    results = []
    for code, char in char_map.items():
        values = []
        for animal in animals:
            ev = eval_map.get(animal.id)
            if ev:
                val = get_evaluation_value(ev, code)
                if val is not None:
                    values.append(val)
                    
        if not values:
            continue
            
        results.append({
            "code": code,
            "name": char["name"],
            "description": char["description"],
            "mean": round(statistics.mean(values), 3),
            "median": round(statistics.median(values), 3),
            "std_dev": round(statistics.stdev(values), 3) if len(values) > 1 else 0,
            "min": round(min(values), 3),
            "max": round(max(values), 3),
            "count": len(values),
            "percentiles": {
                "10": round(sorted(values)[int(len(values) * 0.1)], 3) if len(values) > 10 else None,
                "25": round(sorted(values)[int(len(values) * 0.25)], 3) if len(values) > 4 else None,
                "50": round(statistics.median(values), 3),
                "75": round(sorted(values)[int(len(values) * 0.75)], 3) if len(values) > 4 else None,
                "90": round(sorted(values)[int(len(values) * 0.9)], 3) if len(values) > 10 else None,
                "95": round(sorted(values)[int(len(values) * 0.95)], 3) if len(values) > 20 else None,
                "99": round(sorted(values)[int(len(values) * 0.99)], 3) if len(values) > 100 else None,
            }
        })
        
    return {
        "platform": platform_code,
        "total_animals": len(animals),
        "characteristics": results
    }


@router.get("/auction")
async def get_auction_data(
    platform_code: str = Query(..., description="Platform code"),
    characteristic: str = Query(..., description="Characteristic code"),
    limit: int = Query(50, ge=1, le=200),
    farm_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get animals selected for auction (top performers)"""
    
    if platform_code not in PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Platform {platform_code} not found")
        
    platform = PLATFORMS[platform_code]
    
    # Find characteristic
    char_info = None
    for char in platform["characteristics"]:
        if char["code"] == characteristic:
            char_info = char
            break
            
    if not char_info:
        raise HTTPException(status_code=404, detail=f"Characteristic {characteristic} not found")
        
    # Get latest evaluations of all animals for this platform to calculate global percentiles
    max_safra = get_max_completed_safra()
    all_evals = db.query(GeneticsGeneticEvaluation).filter(
        GeneticsGeneticEvaluation.fonte_origem == platform_code,
        GeneticsGeneticEvaluation.safra <= max_safra
    ).order_by(
        GeneticsGeneticEvaluation.safra.desc(),
        GeneticsGeneticEvaluation.created_at.desc()
    ).all()
    
    # In-memory deduplication to get latest evaluation per animal
    all_eval_map = {}
    for ev in all_evals:
        if ev.animal_id not in all_eval_map:
            all_eval_map[ev.animal_id] = ev
            
    # Extract values for the characteristic across the entire population
    all_values = []
    for ev in all_eval_map.values():
        val = get_evaluation_value(ev, characteristic)
        if val is not None:
            all_values.append(val)
    all_values.sort()
    
    # Query target animals (by farm filter)
    target_animals_query = db.query(GeneticsAnimal)
    if farm_id:
        target_animals_query = target_animals_query.filter(GeneticsAnimal.farm_id == farm_id)
    elif current_user.role != "admin" and current_user.id_farm:
        target_animals_query = target_animals_query.filter(GeneticsAnimal.farm_id == str(current_user.id_farm))
    target_animals = target_animals_query.all()
    
    # Associate target animals with their values
    animals_with_values = []
    for animal in target_animals:
        ev = all_eval_map.get(animal.id)
        if ev:
            val = get_evaluation_value(ev, characteristic)
            if val is not None:
                animals_with_values.append((animal, ev, val))
                
    # Sort target animals by value descending
    animals_with_values.sort(key=lambda x: x[2], reverse=True)
    
    # Apply limit
    selected_subset = animals_with_values[:limit]
    
    # Get farm names for the subset
    subset_farm_ids = {UUID(str(a.farm_id)) for a, _, _ in selected_subset if a.farm_id}
    farm_names = {}
    if subset_farm_ids:
        farms = db.query(GeneticsFarm).filter(GeneticsFarm.id.in_(list(subset_farm_ids))).all()
        farm_names = {str(farm.id): farm.nome for farm in farms}
        
    # Build auction list
    auction_animals = []
    for animal, ev, value in selected_subset:
        # Calculate percentile
        if all_values:
            rank = sum(1 for v in all_values if v <= value)
            percentile = (rank / len(all_values)) * 100
        else:
            percentile = 0
            
        # Extract all characteristics for the animal
        char_dict = {}
        for char in platform["characteristics"]:
            char_val = get_evaluation_value(ev, char["code"])
            if char_val is not None:
                char_dict[char["code"]] = round(char_val, 3)
                
        auction_animals.append({
            "id": str(animal.id),
            "rgn": animal.rgn,
            "nome": animal.nome or "—",
            "sexo": animal.sexo,
            "raca": animal.raca,
            "farm_id": str(animal.farm_id) if animal.farm_id else None,
            "farm_name": farm_names.get(str(animal.farm_id), f"Fazenda {animal.farm_id}") if animal.farm_id else "—",
            "value": round(value, 3),
            "percentile": round(percentile, 1),
            "top_percent": f"TOP {round(100 - percentile, 1)}%" if percentile > 50 else f"TOP {round(percentile, 1)}%",
            "characteristics": char_dict
        })
        
    return {
        "platform": platform_code,
        "characteristic": char_info["name"],
        "animals": auction_animals,
        "total_selected": len(auction_animals),
        "average_value": round(statistics.mean([a["value"] for a in auction_animals]), 3) if auction_animals else 0
    }