"""
Dados de referência ANCP: médias Top 10 por safra e tabela de percentil TOP.
Usado para comparações na Inteligência Genética.
"""

# Médias ANCP Top 10 por safra (2015-2024)
# Fonte: Dados fornecidos pelo cliente
ANCP_TOP10_AVERAGES = {
    2015: {"MGTe": 12.133, "D3P": 76.909, "DIPP": -0.684, "DPE365": 0.318, "DPE450": 0.376, "DPN": 0.545, "DSTAY": 68.461, "DSTAY54": 43.301, "MP120": 1.344, "DP210": 5.943, "DP450": 12.139, "DAOL": 0.766, "DACAB": 0, "DMAR": -0.01},
    2016: {"MGTe": 13.124, "D3P": 77.138, "DIPP": -0.72, "DPE365": 0.363, "DPE450": 0.435, "DPN": 0.552, "DSTAY": 69.972, "DSTAY54": 44.577, "MP120": 1.508, "DP210": 6.56, "DP450": 13.16, "DAOL": 0.916, "DACAB": 0.037, "DMAR": -0.009},
    2017: {"MGTe": 14.063, "D3P": 77.58, "DIPP": -0.622, "DPE365": 0.428, "DPE450": 0.508, "DPN": 0.566, "DSTAY": 71.425, "DSTAY54": 45.702, "MP120": 1.538, "DP210": 7.218, "DP450": 14.204, "DAOL": 1.109, "DACAB": 0.055, "DMAR": 0},
    2018: {"MGTe": 15.475, "D3P": 78.483, "DIPP": -0.792, "DPE365": 0.539, "DPE450": 0.643, "DPN": 0.587, "DSTAY": 73.336, "DSTAY54": 48.219, "MP120": 1.582, "DP210": 8.161, "DP450": 15.606, "DAOL": 1.432, "DACAB": 0.095, "DMAR": 0},
    2019: {"MGTe": 16.879, "D3P": 79.301, "DIPP": -0.719, "DPE365": 0.635, "DPE450": 0.773, "DPN": 0.603, "DSTAY": 75.538, "DSTAY54": 50.351, "MP120": 1.593, "DP210": 9.108, "DP450": 17.089, "DAOL": 1.739, "DACAB": 0.15, "DMAR": 0.009},
    2020: {"MGTe": 17.953, "D3P": 79.398, "DIPP": -0.856, "DPE365": 0.711, "DPE450": 0.856, "DPN": 0.592, "DSTAY": 77.098, "DSTAY54": 51.508, "MP120": 1.703, "DP210": 9.788, "DP450": 18.189, "DAOL": 1.964, "DACAB": 0.205, "DMAR": 0.019},
    2021: {"MGTe": 19.497, "D3P": 79.87, "DIPP": -0.9, "DPE365": 0.816, "DPE450": 0.966, "DPN": 0.578, "DSTAY": 78.926, "DSTAY54": 53.976, "MP120": 2.024, "DP210": 10.603, "DP450": 19.634, "DAOL": 2.249, "DACAB": 0.266, "DMAR": 0.039},
    2022: {"MGTe": 20.984, "D3P": 80.213, "DIPP": -0.927, "DPE365": 0.921, "DPE450": 1.077, "DPN": 0.603, "DSTAY": 80.196, "DSTAY54": 56.847, "MP120": 2.411, "DP210": 11.41, "DP450": 21.038, "DAOL": 2.496, "DACAB": 0.346, "DMAR": 0.044},
    2023: {"MGTe": 22.768, "D3P": 80.789, "DIPP": -0.957, "DPE365": 1.03, "DPE450": 1.195, "DPN": 0.625, "DSTAY": 81.672, "DSTAY54": 59.163, "MP120": 2.725, "DP210": 12.429, "DP450": 22.886, "DAOL": 2.903, "DACAB": 0.432, "DMAR": 0.051},
    2024: {"MGTe": 24.122, "D3P": 80.528, "DIPP": -0.985, "DPE365": 1.156, "DPE450": 1.326, "DPN": 0.641, "DSTAY": 82.302, "DSTAY54": 61.031, "MP120": 3.151, "DP210": 13.15, "DP450": 24.489, "DAOL": 3.149, "DACAB": 0.505, "DMAR": 0.059},
}

# Tabela de percentil TOP (0.1% a 100%)
# Cada entrada: {TOP: float, DEP_NAME: valor_de_corte, ...}
# Um animal com valor >= valor_de_corte está naquele TOP
ANCP_TOP_PERCENTILE_TABLE = [
    {"TOP": 0.1, "MGTe": 33.87, "D3P": 95.74, "DIPP": -1.61, "DPE365": 3.37, "DPE450": 3.39, "DPN": -1.53, "DSTAY": 97.38, "DSTAY54": 83.36, "MP120": 7.43, "DP210": 24.11, "DP450": 41.72, "DAOL": 7.09, "DACAB": 3.36, "DMAR": 3.36},
    {"TOP": 0.5, "MGTe": 31.98, "D3P": 93.24, "DIPP": -1.45, "DPE365": 2.23, "DPE450": 2.5, "DPN": -1.11, "DSTAY": 94.79, "DSTAY54": 78.67, "MP120": 6.39, "DP210": 21.71, "DP450": 38.03, "DAOL": 6.21, "DACAB": 1.43, "DMAR": 0.29},
    {"TOP": 1, "MGTe": 30.89, "D3P": 91.8, "DIPP": -1.36, "DPE365": 2.01, "DPE450": 2.27, "DPN": -0.89, "DSTAY": 93.24, "DSTAY54": 75.96, "MP120": 5.81, "DP210": 20.26, "DP450": 35.71, "DAOL": 5.67, "DACAB": 1.19, "DMAR": 0.24},
    {"TOP": 2, "MGTe": 29.79, "D3P": 90.44, "DIPP": -1.28, "DPE365": 1.83, "DPE450": 2.08, "DPN": -0.7, "DSTAY": 91.7, "DSTAY54": 73.28, "MP120": 5.24, "DP210": 18.8, "DP450": 33.4, "DAOL": 5.16, "DACAB": 1.01, "DMAR": 0.21},
    {"TOP": 3, "MGTe": 29.01, "D3P": 89.45, "DIPP": -1.22, "DPE365": 1.7, "DPE450": 1.94, "DPN": -0.58, "DSTAY": 90.5, "DSTAY54": 71.17, "MP120": 4.84, "DP210": 17.7, "DP450": 31.63, "DAOL": 4.77, "DACAB": 0.88, "DMAR": 0.18},
    {"TOP": 4, "MGTe": 28.25, "D3P": 88.68, "DIPP": -1.18, "DPE365": 1.59, "DPE450": 1.83, "DPN": -0.5, "DSTAY": 89.54, "DSTAY54": 69.51, "MP120": 4.53, "DP210": 16.83, "DP450": 30.29, "DAOL": 4.49, "DACAB": 0.79, "DMAR": 0.17},
    {"TOP": 5, "MGTe": 27.69, "D3P": 88.04, "DIPP": -1.14, "DPE365": 1.51, "DPE450": 1.74, "DPN": -0.43, "DSTAY": 88.7, "DSTAY54": 68.1, "MP120": 4.28, "DP210": 16.12, "DP450": 29.15, "DAOL": 4.24, "DACAB": 0.72, "DMAR": 0.15},
    {"TOP": 10, "MGTe": 25.1, "D3P": 85.71, "DIPP": -1.01, "DPE365": 1.22, "DPE450": 1.43, "DPN": -0.23, "DSTAY": 85.61, "DSTAY54": 62.99, "MP120": 3.51, "DP210": 13.72, "DP450": 25.21, "DAOL": 3.45, "DACAB": 0.49, "DMAR": 0.09},
    {"TOP": 15, "MGTe": 23.37, "D3P": 83.9, "DIPP": -0.91, "DPE365": 1.03, "DPE450": 1.22, "DPN": -0.11, "DSTAY": 83.42, "DSTAY54": 59.49, "MP120": 3.02, "DP210": 12.16, "DP450": 22.61, "DAOL": 2.95, "DACAB": 0.35, "DMAR": 0.06},
    {"TOP": 20, "MGTe": 21.94, "D3P": 82.31, "DIPP": -0.84, "DPE365": 0.88, "DPE450": 1.06, "DPN": -0.01, "DSTAY": 81.65, "DSTAY54": 56.72, "MP120": 2.65, "DP210": 10.94, "DP450": 20.61, "DAOL": 2.57, "DACAB": 0.24, "DMAR": 0.02},
    {"TOP": 25, "MGTe": 20.69, "D3P": 80.84, "DIPP": -0.77, "DPE365": 0.75, "DPE450": 0.91, "DPN": 0.08, "DSTAY": 80.09, "DSTAY54": 54.37, "MP120": 2.36, "DP210": 9.92, "DP450": 18.92, "DAOL": 2.25, "DACAB": 0.16, "DMAR": -0.01},
    {"TOP": 30, "MGTe": 19.57, "D3P": 79.44, "DIPP": -0.7, "DPE365": 0.63, "DPE450": 0.78, "DPN": 0.16, "DSTAY": 78.69, "DSTAY54": 52.28, "MP120": 2.12, "DP210": 9.03, "DP450": 17.45, "DAOL": 1.97, "DACAB": 0.09, "DMAR": -0.03},
    {"TOP": 35, "MGTe": 18.53, "D3P": 78.07, "DIPP": -0.64, "DPE365": 0.52, "DPE450": 0.66, "DPN": 0.23, "DSTAY": 77.39, "DSTAY54": 50.36, "MP120": 1.91, "DP210": 8.23, "DP450": 16.14, "DAOL": 1.72, "DACAB": 0.03, "DMAR": -0.06},
    {"TOP": 40, "MGTe": 17.58, "D3P": 76.73, "DIPP": -0.59, "DPE365": 0.42, "DPE450": 0.55, "DPN": 0.29, "DSTAY": 76.18, "DSTAY54": 48.56, "MP120": 1.71, "DP210": 7.49, "DP450": 14.96, "DAOL": 1.49, "DACAB": -0.02, "DMAR": -0.08},
    {"TOP": 45, "MGTe": 16.67, "D3P": 75.39, "DIPP": -0.54, "DPE365": 0.32, "DPE450": 0.43, "DPN": 0.36, "DSTAY": 75.03, "DSTAY54": 46.86, "MP120": 1.52, "DP210": 6.79, "DP450": 13.87, "DAOL": 1.26, "DACAB": -0.07, "DMAR": -0.11},
    {"TOP": 50, "MGTe": 15.8, "D3P": 74.07, "DIPP": -0.48, "DPE365": 0.22, "DPE450": 0.33, "DPN": 0.42, "DSTAY": 73.94, "DSTAY54": 45.24, "MP120": 1.34, "DP210": 6.13, "DP450": 12.84, "DAOL": 1.05, "DACAB": -0.12, "DMAR": -0.13},
    {"TOP": 55, "MGTe": 14.95, "D3P": 72.78, "DIPP": -0.43, "DPE365": 0.13, "DPE450": 0.23, "DPN": 0.49, "DSTAY": 72.9, "DSTAY54": 43.7, "MP120": 1.17, "DP210": 5.5, "DP450": 11.86, "DAOL": 0.84, "DACAB": -0.16, "DMAR": -0.16},
    {"TOP": 60, "MGTe": 14.1, "D3P": 71.52, "DIPP": -0.38, "DPE365": 0.03, "DPE450": 0.13, "DPN": 0.55, "DSTAY": 71.91, "DSTAY54": 42.23, "MP120": 1.01, "DP210": 4.89, "DP450": 10.92, "DAOL": 0.64, "DACAB": -0.2, "DMAR": -0.18},
    {"TOP": 65, "MGTe": 13.24, "D3P": 70.28, "DIPP": -0.32, "DPE365": -0.07, "DPE450": 0.03, "DPN": 0.61, "DSTAY": 70.93, "DSTAY54": 40.83, "MP120": 0.85, "DP210": 4.29, "DP450": 10.0, "DAOL": 0.44, "DACAB": -0.25, "DMAR": -0.21},
    {"TOP": 70, "MGTe": 12.36, "D3P": 69.04, "DIPP": -0.27, "DPE365": -0.17, "DPE450": -0.07, "DPN": 0.68, "DSTAY": 69.97, "DSTAY54": 39.49, "MP120": 0.69, "DP210": 3.71, "DP450": 9.1, "DAOL": 0.25, "DACAB": -0.29, "DMAR": -0.23},
    {"TOP": 75, "MGTe": 11.46, "D3P": 67.8, "DIPP": -0.21, "DPE365": -0.27, "DPE450": -0.17, "DPN": 0.74, "DSTAY": 69.02, "DSTAY54": 38.18, "MP120": 0.53, "DP210": 3.13, "DP450": 8.21, "DAOL": 0.06, "DACAB": -0.34, "DMAR": -0.26},
    {"TOP": 80, "MGTe": 10.5, "D3P": 66.57, "DIPP": -0.16, "DPE365": -0.37, "DPE450": -0.27, "DPN": 0.8, "DSTAY": 68.08, "DSTAY54": 36.91, "MP120": 0.37, "DP210": 2.57, "DP450": 7.33, "DAOL": -0.13, "DACAB": -0.39, "DMAR": -0.28},
    {"TOP": 85, "MGTe": 9.47, "D3P": 65.34, "DIPP": -0.11, "DPE365": -0.47, "DPE450": -0.37, "DPN": 0.86, "DSTAY": 67.14, "DSTAY54": 35.65, "MP120": 0.2, "DP210": 1.99, "DP450": 6.45, "DAOL": -0.33, "DACAB": -0.44, "DMAR": -0.31},
    {"TOP": 90, "MGTe": 8.34, "D3P": 64.09, "DIPP": -0.06, "DPE365": -0.57, "DPE450": -0.47, "DPN": 0.92, "DSTAY": 66.19, "DSTAY54": 34.38, "MP120": 0.03, "DP210": 1.42, "DP450": 5.56, "DAOL": -0.53, "DACAB": -0.49, "DMAR": -0.34},
    {"TOP": 95, "MGTe": 7.05, "D3P": 62.81, "DIPP": -0.01, "DPE365": -0.67, "DPE450": -0.57, "DPN": 0.99, "DSTAY": 65.23, "DSTAY54": 33.11, "MP120": -0.14, "DP210": 0.85, "DP450": 4.67, "DAOL": -0.74, "DACAB": -0.54, "DMAR": -0.37},
    {"TOP": 100, "MGTe": 0.1, "D3P": 60.3, "DIPP": 0.09, "DPE365": -0.86, "DPE450": -0.76, "DPN": 1.12, "DSTAY": 63.42, "DSTAY54": 30.71, "MP120": -0.49, "DP210": -0.23, "DP450": 2.98, "DAOL": -1.15, "DACAB": -0.66, "DMAR": -0.44},
]

# DEPs onde MAIOR valor = MELHOR (normal)
_HIGHER_IS_BETTER = {"MGTe", "D3P", "DPE365", "DPE450", "DSTAY", "DSTAY54", "MP120", "DP210", "DP450", "DAOL", "DACAB", "DMAR"}
# DEPs onde MENOR valor = MELHOR (invertido)
_LOWER_IS_BETTER = {"DIPP", "DPN", "CAR"}


def find_top_percentile(dep_name: str, value: float) -> float:
    """
    Dado o nome de uma DEP e um valor médio, retorna o TOP percentil.
    Exemplo: MGTe=29.80 -> TOP 2 (porque 29.80 >= 29.79 que é o corte do TOP 2).

    Para DEPs "higher is better": valor >= corte = está naquele TOP.
    Para DEPs "lower is better" (DIPP, DPN): valor <= corte = está naquele TOP.
    """
    if value is None:
        return None

    is_lower_better = dep_name in _LOWER_IS_BETTER

    for row in ANCP_TOP_PERCENTILE_TABLE:
        cutoff = row.get(dep_name)
        if cutoff is None:
            continue

        if is_lower_better:
            # Para DIPP/DPN: quanto menor, melhor. Valor <= corte = está nesse TOP
            if value <= cutoff:
                return row["TOP"]
        else:
            # Para maioria: quanto maior, melhor. Valor >= corte = está nesse TOP
            if value >= cutoff:
                return row["TOP"]

    # Se não atingiu nenhum corte, retorna 100 (pior percentil)
    return 100.0
