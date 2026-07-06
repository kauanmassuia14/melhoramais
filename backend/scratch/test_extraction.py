import pandas as pd

file_path = "/home/kauanmassuia/projeto-melhoramais/Relatorio_ag (1).xls"
df = pd.read_excel(file_path, engine="xlrd")

def get_val(r, col_name):
    if not col_name: return None
    if col_name in r: return r[col_name]
    c_norm = str(col_name).lower().replace(" ", "").replace("_", "").replace("-", "")
    for k in r.keys():
        if str(k).lower().replace(" ", "").replace("_", "").replace("-", "") == c_norm:
            return r[k]
    return None

print("Sample rows:")
for idx, row in df.head(5).iterrows():
    rgn = get_val(row, 'rgn_animal') or get_val(row, 'rgn')
    serie = get_val(row, 'serie_animal') or get_val(row, 'serie') or get_val(row, 'série')
    nome = get_val(row, 'nome') or get_val(row, 'nome_animal')
    
    sire_rgn = get_val(row, 'pai_rgn')
    sire_serie = get_val(row, 'pai_serie')
    sire_nome = get_val(row, 'pai_nome')
    
    print(f"Child: RGN={rgn}, Serie={repr(serie)}, Nome={nome}")
    print(f"  Pai: RGN={sire_rgn}, Serie={repr(sire_serie)}, Nome={sire_nome}")
