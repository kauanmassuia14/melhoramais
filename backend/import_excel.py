"""
Script de Importação Excel → PostgreSQL (genetics)
Projeto Melhora+ - Multi-Tenant
Arquivo: Avaliacao_Corte2026 (2).xls (PMGZ/ABCZ)

Layout: Excel PMGZ com cabeçalho triplo, dados a partir da linha 9 (índice 8)
Mapeamento por índice de coluna (0-110)

Uso:
    python import_excel.py <excel> <farm_id> [fonte] [safra]
    python import_excel.py "Avaliacao_Corte2026 (2).xls" <farm_id> PMGZ 2026
"""

import sys
import re
from typing import Optional
import pandas as pd
import psycopg2


def get_db_connection(db_url: str = None):
    """Retorna conexão com o banco"""
    if db_url is None:
        db_url = "postgresql://postgres:viruss@localhost:5432/melhoramais_agro?sslmode=disable"
    return psycopg2.connect(db_url)


def clean_numeric_value(value) -> Optional[float]:
    """
    Converte valor sujo para float.
    Aceita: 1,23 (BR), 1.23 (US), '1.23 kg', '1,23%', '-', 'ND', None
    """
    if value is None or pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        value = value.strip().upper()

        # Valores inválidos → NULL
        if value in ['', '-', '--', 'ND', 'N/A', 'NA', 'NR', 'NS']:
            return None

        # Remover unidades (kg, cm, %, etc)
        value = re.sub(r'[A-Za-z%°]', '', value).strip()

        if not value:
            return None

        # Converter vírgula para ponto
        value = value.replace(',', '.')

        try:
            return float(value)
        except ValueError:
            return None

    return None


def clean_int_value(value) -> Optional[int]:
    """Converte valor para inteiro"""
    num = clean_numeric_value(value)
    return int(num) if num is not None else None


def null_to_none(value):
    """Converte NaN/None do pandas para None do Python"""
    if pd.isna(value):
        return None
    return value


def format_value_for_sql(value):
    """Formata valor para SQL (None vira NULL)"""
    if value is None:
        return "NULL"
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return str(value)


def get_cell_string(df, row_idx: int, col_idx: int) -> Optional[str]:
    """Retorna valor como string, ou None se vazio/traço"""
    try:
        if col_idx >= len(df.columns):
            return None
        val = df.iloc[row_idx, col_idx]
        if pd.isna(val):
            return None
        val_str = str(val).strip()
        # Ignorar traços e valores inválidos
        if val_str in ['', '-', '--', 'ND', 'N/A']:
            return None
        return val_str
    except:
        return None


def get_cell_numeric(df, row_idx: int, col_idx: int) -> Optional[float]:
    """Retorna valor como float (conversão BR)"""
    try:
        if col_idx >= len(df.columns):
            return None
        val = df.iloc[row_idx, col_idx]
        return clean_numeric_value(val)
    except:
        return None


def get_cell_int(df, row_idx: int, col_idx: int) -> Optional[int]:
    """Retorna valor como inteiro"""
    return clean_int_value(get_cell_numeric(df, row_idx, col_idx))


def parse_metric(df, row_idx: int, start_idx: int) -> str:
    """
    Parse metric_block a partir de índices de coluna.
    Espera 4 colunas: DEP, AC, DECA, P%
    """
    try:
        dep = get_cell_numeric(df, row_idx, start_idx)
        ac = get_cell_numeric(df, row_idx, start_idx + 1)
        deca = get_cell_int(df, row_idx, start_idx + 2)
        p_percent = get_cell_numeric(df, row_idx, start_idx + 3)
    except:
        return "NULL"

    if all(v is None for v in [dep, ac, deca, p_percent]):
        return "NULL"

    return f"({format_value_for_sql(dep)}, {format_value_for_sql(ac)}, {format_value_for_sql(deca)}, {format_value_for_sql(p_percent)})"


def parse_progeny(df, row_idx: int, start_idx: int) -> str:
    """Parse progeny_info: filhos, rebanhos"""
    try:
        filhos = get_cell_int(df, row_idx, start_idx)
        rebanhos = get_cell_int(df, row_idx, start_idx + 1)
    except:
        return "NULL"

    if filhos is None and rebanhos is None:
        return "NULL"

    return f"({format_value_for_sql(filhos)}, {format_value_for_sql(rebanhos)})"


def upsert_animal(conn, farm_id: str, rgn: str, nome: str = None, serie: str = None,
                  sexo: str = None, sire_id: str = None, dam_id: str = None) -> Optional[str]:
    """
    Upsert de animal na tabela genetics.animals
    Retorna o ID (UUID) do animal inserido/atualizado
    """
    if not rgn:
        return None

    nome_val = null_to_none(nome)
    serie_val = null_to_none(serie)
    sexo_val = f"'{sexo}'" if sexo in ['M', 'F'] else "NULL"
    sire_val = f"'{sire_id}'" if sire_id else "NULL"
    dam_val = f"'{dam_id}'" if dam_id else "NULL"

    rgn_sql = format_value_for_sql(rgn)

    sql = f"""
    INSERT INTO genetics.animals (
        farm_id, rgn, nome, serie, sexo, sire_id, dam_id
    ) VALUES (
        '{farm_id}', {rgn_sql}, {format_value_for_sql(nome_val)}, {format_value_for_sql(serie_val)}, {sexo_val}, {sire_val}, {dam_val}
    )
    ON CONFLICT (farm_id, rgn) DO UPDATE SET
        nome = COALESCE(EXCLUDED.nome, genetics.animals.nome),
        serie = COALESCE(EXCLUDED.serie, genetics.animals.serie),
        sexo = COALESCE(EXCLUDED.sexo, genetics.animals.sexo),
        sire_id = COALESCE(EXCLUDED.sire_id, genetics.animals.sire_id),
        dam_id = COALESCE(EXCLUDED.dam_id, genetics.animals.dam_id)
    RETURNING id;
    """

    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        result = cursor.fetchone()
        conn.commit()
        return result[0] if result else None
    except Exception as e:
        conn.rollback()
        print(f"  [ERRO] upsert animal {rgn}: {e}")
        return None
    finally:
        cursor.close()


def upsert_evaluation(conn, farm_id: str, animal_id: str, safra: int, fonte: str, df, row_idx: int) -> bool:
    """
    Upsert de avaliação genética na tabela genetics.genetic_evaluations
    """
    # Campos globais
    iabczg = get_cell_numeric(df, row_idx, 5)
    deca_index = get_cell_int(df, row_idx, 6)

    # Crescimento (metric_block)
    pn_ed = parse_metric(df, row_idx, 27)
    pd_ed = parse_metric(df, row_idx, 31)
    pa_ed = parse_metric(df, row_idx, 35)
    ps_ed = parse_metric(df, row_idx, 39)
    pm_em = parse_metric(df, row_idx, 43)

    # Reprodutivas/Maternas (metric_block)
    ipp = parse_metric(df, row_idx, 47)
    stay = parse_metric(df, row_idx, 51)
    pe_365 = parse_metric(df, row_idx, 55)
    psn = parse_metric(df, row_idx, 59)

    # Carcaça (metric_block)
    aol = parse_metric(df, row_idx, 63)
    acab = parse_metric(df, row_idx, 67)
    marmoreio = parse_metric(df, row_idx, 71)

    # Morfológicas (metric_block)
    eg = parse_metric(df, row_idx, 75)
    pg = parse_metric(df, row_idx, 79)
    mg = parse_metric(df, row_idx, 83)

    # Descendentes (progeny_info)
    p120_info = parse_progeny(df, row_idx, 87)
    p210_info = parse_progeny(df, row_idx, 89)
    p365_info = parse_progeny(df, row_idx, 91)
    p450_info = parse_progeny(df, row_idx, 93)

    # Extras (genotipado, csg)
    genotipado_val = get_cell_string(df, row_idx, 109)
    csg_val = get_cell_string(df, row_idx, 110)

    genotipado = f"'{genotipado_val}'" if genotipado_val in ['SIM', 'NÃO'] else "NULL"
    csg = f"'{csg_val}'" if csg_val in ['SIM', 'NÃO'] else "NULL"

    sql = f"""
    INSERT INTO genetics.genetic_evaluations (
        animal_id, farm_id, safra, fonte_origem,
        iabczg, deca_index,
        pn_ed, pd_ed, pa_ed, ps_ed, pm_em,
        ipp, stay, pe_365, psn,
        aol, acab, marmoreio,
        eg, pg, mg,
        p120_info, p210_info, p365_info, p450_info
    ) VALUES (
        '{animal_id}', '{farm_id}', {safra}, '{fonte}',
        {format_value_for_sql(iabczg)}, {format_value_for_sql(deca_index)},
        {pn_ed}, {pd_ed}, {pa_ed}, {ps_ed}, {pm_em},
        {ipp}, {stay}, {pe_365}, {psn},
        {aol}, {acab}, {marmoreio},
        {eg}, {pg}, {mg},
        {p120_info}, {p210_info}, {p365_info}, {p450_info}
    )
    ON CONFLICT (farm_id, animal_id, safra) DO UPDATE SET
        iabczg = EXCLUDED.iabczg,
        deca_index = EXCLUDED.deca_index,
        pn_ed = EXCLUDED.pn_ed,
        pd_ed = EXCLUDED.pd_ed,
        pa_ed = EXCLUDED.pa_ed,
        ps_ed = EXCLUDED.ps_ed,
        pm_em = EXCLUDED.pm_em,
        ipp = EXCLUDED.ipp,
        stay = EXCLUDED.stay,
        pe_365 = EXCLUDED.pe_365,
        psn = EXCLUDED.psn,
        aol = EXCLUDED.aol,
        acab = EXCLUDED.acab,
        marmoreio = EXCLUDED.marmoreio,
        eg = EXCLUDED.eg,
        pg = EXCLUDED.pg,
        mg = EXCLUDED.mg;
    """

    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"  [ERRO] upsert avaliação: {e}")
        return False
    finally:
        cursor.close()


def process_row(df, row_idx: int, farm_id: str, conn) -> Optional[str]:
    """
    Processa uma linha do Excel na ordem hierárquica:
    1. Avós (apenas se tiverem RGN)
    2. Pais (apenas se tiverem RGN)
    3. Animal Principal

    Valida ciclos: se animal_rgn == sire_rgn → WARNING + pular
    """
    # === ANIMAL PRINCIPAL ===
    animal_rgn = get_cell_string(df, row_idx, 2)
    if not animal_rgn:
        return None

    # Validação: ciclo (animal = sire) → WARNING
    sire_rgn_check = get_cell_string(df, row_idx, 11)
    if sire_rgn_check and sire_rgn_check == animal_rgn:
        print(f"  [WARNING] Linha {row_idx}: animal_rgn == sire_rgn ({animal_rgn}). Pulando relação de pai.")
        sire_rgn_check = None  # Ignorar pai

    # === PASSO 1: Avós ===
    avopat_id = None
    avapat_id = None
    avomat_id = None
    avamat_id = None

    # Avô Paterno (col 14)
    avopat_rgn = get_cell_string(df, row_idx, 14)
    if avopat_rgn:
        avopat_id = upsert_animal(conn, farm_id, avopat_rgn,
                                   get_cell_string(df, row_idx, 12))

    # Avó Paterna (col 17)
    avapat_rgn = get_cell_string(df, row_idx, 17)
    if avapat_rgn:
        avapat_id = upsert_animal(conn, farm_id, avapat_rgn,
                                   get_cell_string(df, row_idx, 15))

    # Avô Materno (col 23)
    avomat_rgn = get_cell_string(df, row_idx, 23)
    if avomat_rgn:
        avomat_id = upsert_animal(conn, farm_id, avomat_rgn,
                                   get_cell_string(df, row_idx, 21))

    # Avó Materna (col 26)
    avamat_rgn = get_cell_string(df, row_idx, 26)
    if avamat_rgn:
        avamat_id = upsert_animal(conn, farm_id, avamat_rgn,
                                   get_cell_string(df, row_idx, 24))

    # === PASSO 2: Pais ===
    # Pai (col 11)
    pai_id = None
    if sire_rgn_check:
        pai_id = upsert_animal(conn, farm_id, sire_rgn_check,
                               get_cell_string(df, row_idx, 9),
                               sire_id=avopat_id, dam_id=avapat_id)

    # Mãe (col 20)
    mae_id = None
    mae_rgn = get_cell_string(df, row_idx, 20)
    if mae_rgn:
        mae_id = upsert_animal(conn, farm_id, mae_rgn,
                               get_cell_string(df, row_idx, 18),
                               sire_id=avomat_id, dam_id=avamat_id)

    # === PASSO 3: Animal Principal ===
    animal_id = upsert_animal(conn, farm_id, animal_rgn,
                               get_cell_string(df, row_idx, 0),   # Nome
                               get_cell_string(df, row_idx, 1),   # Serie
                               get_cell_string(df, row_idx, 3),   # Sexo
                               sire_id=pai_id, dam_id=mae_id)

    return animal_id


def import_excel(excel_path: str, farm_id: str, db_url: str = None,
                 fonte: str = 'PMGZ', safra: int = 2026):
    """
    Função principal de importação
    Lê Excel com skiprows=8 (dados a partir da linha 9)
    """
    print(f"\n{'='*60}")
    print(f"IMPORTANDO: {excel_path}")
    print(f"FARM ID: {farm_id}")
    print(f"FONTE: {fonte} | SAFRA: {safra}")
    print(f"{'='*60}\n")

    # Ler Excel: header=None, dados a partir da linha 9 (índice 8)
    df = pd.read_excel(excel_path, header=None, skiprows=8)

    print(f"Total de linhas no arquivo: {len(df)}")
    print(f"Total de colunas: {len(df.columns)}")

    # Validação de layout
    if len(df.columns) < 110:
        raise Exception(f"Layout de colunas inválido! Esperado: 110, Encontrado: {len(df.columns)}")

    # Remover linhas onde RGN está vazio
    df_valid = df[df.iloc[:, 2].notna()].copy()
    print(f"Registros com RGN válido: {len(df_valid)}\n")

    conn = get_db_connection(db_url)

    stats = {'sucesso': 0, 'erros': 0, 'skip': 0}

    try:
        for idx in range(len(df_valid)):
            try:
                # Processar animal hierárquico
                animal_id = process_row(df_valid, idx, farm_id, conn)

                if not animal_id:
                    stats['skip'] += 1
                    continue

                # Processar avaliação
                ok = upsert_evaluation(conn, farm_id, animal_id, safra, fonte, df_valid, idx)

                rgn = get_cell_string(df_valid, idx, 2)
                if ok:
                    stats['sucesso'] += 1
                    print(f"  [SUCESSO] RGN {rgn} inserido/atualizado")
                else:
                    stats['erros'] += 1
                    print(f"  [ERRO] RGN {rgn}: falha na avaliação")

                # Progresso a cada 20 registros
                if (stats['sucesso'] + stats['erros']) % 20 == 0:
                    print(f"    → Progresso: {stats['sucesso'] + stats['erros']}/{len(df_valid)}\n")

            except Exception as e:
                stats['erros'] += 1
                rgn = get_cell_string(df_valid, idx, 2) or "?"
                print(f"  [ERRO] Linha {idx} (RGN {rgn}): {e}")

    except Exception as e:
        print(f"\n[ERRO FATAL] {e}")
        raise
    finally:
        conn.close()

    print(f"\n{'='*60}")
    print(f"IMPORTAÇÃO CONCLUÍDA")
    print(f"  ✅ Sucesso: {stats['sucesso']}")
    print(f"  ❌ Erros: {stats['erros']}")
    print(f"  ⏭️  Pulados: {stats['skip']}")
    print(f"{'='*60}\n")

    return stats


# ========== ENTRY POINT ==========
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python import_excel.py <caminho_excel> <farm_id> [db_url] [fonte] [safra]")
        print("\nExemplo:")
        print("  python import_excel.py 'Avaliacao_Corte2026 (2).xls' <farm_id> PMGZ 2026")
        print("  python import_excel.py 'Avaliacao_Corte2026 (2).xls' <farm_id> '<url>' PMGZ 2026")
        sys.exit(1)

    excel_path = sys.argv[1]
    farm_id = sys.argv[2]
    db_url = sys.argv[3] if len(sys.argv) > 3 else None
    fonte = sys.argv[4] if len(sys.argv) > 4 else 'PMGZ'
    safra = int(sys.argv[5]) if len(sys.argv) > 5 else 2026

    import_excel(excel_path, farm_id, db_url, fonte, safra)