from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import statistics

from .database import get_db
from .models import Animal, Farm, ColumnMapping, User
from .auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


# Platform metadata
PLATFORMS = {
    "ANCP": {
        "name": "ANCP",
        "description": "Associação Nacional de Criadores e Prodembros",
        "index_column": "anc_mg",  # Main index column for sorting
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
    farm_id: Optional[int] = Query(None, description="Farm ID filter"),
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
    
    column_name = char_info["column"]
    
    # Base query
    query = db.query(Animal)
    
    # Apply filters
    if farm_id:
        query = query.filter(Animal.id_farm == farm_id)
    elif current_user.role != "admin" and current_user.id_farm:
        query = query.filter(Animal.id_farm == current_user.id_farm)
    
    if sexo:
        query = query.filter(Animal.sexo == sexo)
    
    if situacao:
        # Assuming there's a situacao column, but we don't have one yet
        # For now, ignore this filter
        pass
    
    if start_date:
        query = query.filter(Animal.data_nascimento >= start_date)
    if end_date:
        query = query.filter(Animal.data_nascimento <= end_date)
    
    # Get only animals with the characteristic value
    query = query.filter(getattr(Animal, column_name).isnot(None))
    
    # Get all animals for calculations
    all_animals = query.all()
    
    if not all_animals:
        return {
            "platform": platform_code,
            "characteristic": char_info["name"],
            "groups": [],
            "total_animals": 0
        }
    
    # Calculate general average (Group C)
    values = [getattr(a, column_name) for a in all_animals if getattr(a, column_name) is not None]
    general_avg = statistics.mean(values) if values else 0
    general_std = statistics.stdev(values) if len(values) > 1 else 0
    
    # Group by farm to get "clients"
    farm_groups = {}
    for animal in all_animals:
        farm_id = animal.id_farm
        if farm_id not in farm_groups:
            farm_groups[farm_id] = []
        farm_groups[farm_id].append(getattr(animal, column_name))
    
    # Calculate average per farm
    farm_averages = []
    for farm_id, farm_values in farm_groups.items():
        farm_avg = statistics.mean(farm_values)
        farm_averages.append({
            "farm_id": farm_id,
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
    farm_ids = [fa["farm_id"] for fa in farm_averages]
    if farm_ids:
        farms = db.query(Farm).filter(Farm.id_farm.in_(farm_ids)).all()
        for farm in farms:
            farm_names[farm.id_farm] = farm.nome_farm
    
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
        "count": all_animals.__len__(),
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
        "total_animals": len(all_animals),
        "total_farms": all_farms_count
    }


@router.get("/compare")
async def compare_characteristics(
    platform_code: str = Query(..., description="Platform code"),
    characteristics: str = Query(..., description="Comma-separated characteristic codes"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    sexo: Optional[str] = Query(None),
    farm_id: Optional[int] = Query(None),
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
    
    # Base query
    query = db.query(Animal)
    if farm_id:
        query = query.filter(Animal.id_farm == farm_id)
    elif current_user.role != "admin" and current_user.id_farm:
        query = query.filter(Animal.id_farm == current_user.id_farm)
    
    if sexo:
        query = query.filter(Animal.sexo == sexo)
    if start_date:
        query = query.filter(Animal.data_nascimento >= start_date)
    if end_date:
        query = query.filter(Animal.data_nascimento <= end_date)
    
    # Filter animals with at least one characteristic
    column_names = [char_map[code]["column"] for code in char_map]
    for col in column_names:
        query = query.filter(getattr(Animal, col).isnot(None))
    
    animals = query.all()
    
    if not animals:
        return {"message": "No animals found with the selected characteristics"}
    
    # Calculate statistics for each characteristic
    results = []
    for code, char in char_map.items():
        values = [getattr(a, char["column"]) for a in animals if getattr(a, char["column"]) is not None]
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
    farm_id: Optional[int] = Query(None),
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
    
    column_name = char_info["column"]
    
    # Base query
    query = db.query(Animal)
    if farm_id:
        query = query.filter(Animal.id_farm == farm_id)
    elif current_user.role != "admin" and current_user.id_farm:
        query = query.filter(Animal.id_farm == current_user.id_farm)
    
    # Get animals with the characteristic, order by value descending
    query = query.filter(getattr(Animal, column_name).isnot(None))
    query = query.order_by(getattr(Animal, column_name).desc())
    query = query.limit(limit)
    
    animals = query.all()
    
    # Get farm names
    farm_ids = [a.id_farm for a in animals]
    farms = db.query(Farm).filter(Farm.id_farm.in_(farm_ids)).all()
    farm_names = {farm.id_farm: farm.nome_farm for farm in farms}
    
    # Calculate percentiles for ranking
    all_query = db.query(Animal).filter(getattr(Animal, column_name).isnot(None))
    all_values = [getattr(a, column_name) for a in all_query.all()]
    all_values.sort()
    
    # Build auction list
    auction_animals = []
    for animal in animals:
        value = getattr(animal, column_name)
        # Calculate percentile
        if all_values:
            rank = sum(1 for v in all_values if v <= value)
            percentile = (rank / len(all_values)) * 100
        else:
            percentile = 0
        
        auction_animals.append({
            "id": animal.id_animal,
            "rgn": animal.rgn_animal,
            "nome": animal.nome_animal,
            "sexo": animal.sexo,
            "raca": animal.raca,
            "farm_id": animal.id_farm,
            "farm_name": farm_names.get(animal.id_farm, f"Fazenda {animal.id_farm}"),
            "value": round(value, 3),
            "percentile": round(percentile, 1),
            "top_percent": f"TOP {round(100 - percentile, 1)}%" if percentile > 50 else f"TOP {round(percentile, 1)}%",
            "characteristics": {
                char["code"]: round(getattr(animal, char["column"]), 3)
                for char in platform["characteristics"]
                if hasattr(animal, char["column"]) and getattr(animal, char["column"]) is not None
            }
        })
    
    return {
        "platform": platform_code,
        "characteristic": char_info["name"],
        "animals": auction_animals,
        "total_selected": len(auction_animals),
        "average_value": round(statistics.mean([a["value"] for a in auction_animals]), 3) if auction_animals else 0
    }