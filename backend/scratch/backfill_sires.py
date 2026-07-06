import os
import sys
import uuid
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append("/home/kauanmassuia/projeto-melhoramais")
load_dotenv("/home/kauanmassuia/projeto-melhoramais/.env")

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

file_path = "/home/kauanmassuia/projeto-melhoramais/Relatorio_ag (1).xls"
if not os.path.exists(file_path):
    print(f"Error: file not found at {file_path}")
    sys.exit(1)

print(f"Loading Excel file {file_path}...")
try:
    df = pd.read_excel(file_path, engine="xlrd")
    print(f"Loaded {len(df)} rows.")
except Exception as e:
    print(f"Failed to load Excel: {e}")
    sys.exit(1)

def get_val(r, col_name):
    import unicodedata
    if not col_name: return None
    if col_name in r: return r[col_name]
    
    def norm(text):
        if not text: return ""
        return "".join(
            c for c in unicodedata.normalize('NFD', str(text))
            if unicodedata.category(c) != 'Mn'
        ).lower().replace(" ", "").replace("_", "").replace("-", "")

    c_norm = norm(col_name)
    for k in r.keys():
        if norm(k) == c_norm:
            return r[k]
    return None

def safe_str(val):
    if val is None or pd.isna(val): return None
    s = str(val).strip()
    return s if s else None

# 1. Resolve farm_id and upload_id from database
farm_id = "485a060b-80df-41c6-a675-d14cfce5b66d"  # Default fallback (Camaragibe)
upload_id = None

with engine.connect() as conn:
    row = conn.execute(text("""
        SELECT upload_id, id_farm 
        FROM genetics.uploads 
        WHERE arquivo_nome_original LIKE '%Relatorio_ag (1)%' 
        LIMIT 1
    """)).fetchone()
    if row:
        upload_id = row[0]
        farm_id = row[1]
        print(f"Found upload record: upload_id={upload_id}, farm_id={farm_id}")
    else:
        print(f"No upload record found. Using default farm_id={farm_id}")

# 2. Extract parents
print("Extracting unique parents and children from file...")
parents_to_resolve = []
seen_parents = set()
children_keys = {}

for _, row in df.iterrows():
    # Child
    r_rgn = get_val(row, 'rgn_animal') or get_val(row, 'rgn') or get_val(row, 'registro')
    if r_rgn and str(r_rgn).strip().lower() not in ['nan', 'none', '', 'nat']:
        r_rgn_str = str(r_rgn).strip().upper()
        r_serie_str = str(get_val(row, 'serie_animal') or get_val(row, 'serie') or get_val(row, 'série') or "").strip().upper()
        children_keys[(r_rgn_str, r_serie_str)] = None

    # Sire
    sire_rgn = get_val(row, 'pai_rgn')
    if sire_rgn and str(sire_rgn).strip().lower() not in ['nan', 'none', '']:
        s_rgn_str = str(sire_rgn).strip().upper()
        s_serie_str = str(get_val(row, 'pai_serie') or get_val(row, 'pai_serie_rgd') or "").strip().upper()
        s_nome_str = safe_str(get_val(row, 'pai_nome'))
        key = ('sire', s_rgn_str, s_serie_str)
        if key not in seen_parents:
            seen_parents.add(key)
            parents_to_resolve.append({
                'type': 'sire',
                'rgn': s_rgn_str,
                'serie': s_serie_str,
                'nome': s_nome_str or f"PAI: {s_rgn_str}",
                'raca': safe_str(get_val(row, 'raca') or get_val(row, 'raça'))
            })

    # Dam
    dam_rgn = get_val(row, 'mae_rgn')
    if dam_rgn and str(dam_rgn).strip().lower() not in ['nan', 'none', '']:
        d_rgn_str = str(dam_rgn).strip().upper()
        d_serie_str = str(get_val(row, 'mae_serie') or get_val(row, 'mae_serie_rgd') or "").strip().upper()
        d_nome_str = safe_str(get_val(row, 'mae_nome'))
        key = ('dam', d_rgn_str, d_serie_str)
        if key not in seen_parents:
            seen_parents.add(key)
            parents_to_resolve.append({
                'type': 'dam',
                'rgn': d_rgn_str,
                'serie': d_serie_str,
                'nome': d_nome_str or f"MÃE: {d_rgn_str}",
                'raca': safe_str(get_val(row, 'raca') or get_val(row, 'raça'))
            })

print(f"Unique parents to check/resolve: {len(parents_to_resolve)}")

# 3. Query existing animals to map RGN+Serie to IDs
parent_ids_map = {}
with engine.connect() as conn:
    # Query all children IDs
    child_rgns = list(set([k[0] for k in children_keys.keys()]))
    if child_rgns:
        res = conn.execute(text("""
            SELECT rgn, COALESCE(serie, ''), id 
            FROM genetics.animals 
            WHERE rgn = ANY(:rgns) AND farm_id = :fid
        """), {"rgns": child_rgns, "fid": farm_id}).fetchall()
        for row_rgn, row_serie, uid in res:
            children_keys[(row_rgn, row_serie)] = str(uid)

    # Query parent IDs
    if parents_to_resolve:
        parent_rgns = list(set([p['rgn'] for p in parents_to_resolve]))
        res = conn.execute(text("""
            SELECT rgn, COALESCE(serie, ''), id 
            FROM genetics.animals 
            WHERE rgn = ANY(:rgns) AND farm_id = :fid
        """), {"rgns": parent_rgns, "fid": farm_id}).fetchall()
        for row_rgn, row_serie, uid in res:
            parent_ids_map[(row_rgn, row_serie)] = str(uid)

# 4. Filter missing parents and insert placeholders
parents_to_insert = []
for p in parents_to_resolve:
    key = (p['rgn'], p['serie'])
    if key in parent_ids_map:
        continue
    # If the parent is actually one of the children in the DB
    if key in children_keys and children_keys[key] is not None:
        parent_ids_map[key] = children_keys[key]
        continue
    
    p_uuid = str(uuid.uuid4())
    parent_ids_map[key] = p_uuid
    parents_to_insert.append({
        'id': p_uuid,
        'farm_id': farm_id,
        'rgn': p['rgn'],
        'nome': p['nome'],
        'serie': p['serie'],
        'sexo': 'M' if p['type'] == 'sire' else 'F',
        'raca': p['raca'],
        'upload_id': upload_id
    })

print(f"Parents to insert as placeholders: {len(parents_to_insert)}")

# Perform DB operations in transaction
with engine.begin() as conn:
    # Insert missing parents
    if parents_to_insert:
        print("Inserting placeholder parents...")
        for p in parents_to_insert:
            conn.execute(text("""
                INSERT INTO genetics.animals (id, farm_id, rgn, nome, serie, sexo, raca, nascimento, genotipado, csg, upload_id)
                VALUES (:id, :farm_id, :rgn, :nome, :serie, :sexo, :raca, NULL, 'NÃO'::genetics.boolean_status, 'NÃO'::genetics.boolean_status, :upload_id)
                ON CONFLICT (farm_id, rgn, serie) DO NOTHING
            """), p)

    # Perform backfill updates for child animals
    print("Updating animal records with sire_id and dam_id...")
    update_count = 0
    for _, row in df.iterrows():
        rgn = get_val(row, 'rgn_animal') or get_val(row, 'rgn') or get_val(row, 'registro')
        if not rgn or str(rgn).strip().lower() in ['nan', 'none', '', 'nat']:
            continue
        
        rgn_str = str(rgn).strip().upper()
        serie_str = str(get_val(row, 'serie_animal') or get_val(row, 'serie') or get_val(row, 'série') or "").strip().upper()
        
        child_id = children_keys.get((rgn_str, serie_str))
        if not child_id:
            # Query child ID in case it wasn't mapped earlier
            res = conn.execute(text("""
                SELECT id FROM genetics.animals WHERE farm_id = :fid AND rgn = :rgn AND COALESCE(serie, '') = :serie
            """), {"fid": farm_id, "rgn": rgn_str, "serie": serie_str}).fetchone()
            if res:
                child_id = str(res[0])
                children_keys[(rgn_str, serie_str)] = child_id
        
        if not child_id:
            continue

        # Sire
        sire_rgn = get_val(row, 'pai_rgn')
        sire_id = None
        if sire_rgn and str(sire_rgn).strip().lower() not in ['nan', 'none', '']:
            s_rgn_str = str(sire_rgn).strip().upper()
            s_serie_str = str(get_val(row, 'pai_serie') or get_val(row, 'pai_serie_rgd') or "").strip().upper()
            sire_id = parent_ids_map.get((s_rgn_str, s_serie_str))

        # Dam
        dam_rgn = get_val(row, 'mae_rgn')
        dam_id = None
        if dam_rgn and str(dam_rgn).strip().lower() not in ['nan', 'none', '']:
            d_rgn_str = str(dam_rgn).strip().upper()
            d_serie_str = str(get_val(row, 'mae_serie') or get_val(row, 'mae_serie_rgd') or "").strip().upper()
            dam_id = parent_ids_map.get((d_rgn_str, d_serie_str))

        if sire_id or dam_id:
            conn.execute(text("""
                UPDATE genetics.animals 
                SET sire_id = COALESCE(sire_id, :sire_id),
                    dam_id = COALESCE(dam_id, :dam_id)
                WHERE id = :id
            """), {"id": child_id, "sire_id": sire_id, "dam_id": dam_id})
            update_count += 1

print(f"Backfill successfully completed! Updated {update_count} animal records.")
