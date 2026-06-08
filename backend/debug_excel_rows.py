import os
import sys
import pandas as pd
import io

filepath = "/home/kauanmassuia/Downloads/Relatorio_ag (22) jacamim.xls"

if not os.path.exists(filepath):
    print(f"File not found: {filepath}")
    sys.exit(1)

print(f"=== Inspecting file: {filepath} ===")

df = None
with open(filepath, "rb") as f:
    file_content = f.read()

content_io = io.BytesIO(file_content)

try:
    df = pd.read_excel(content_io, engine="openpyxl")
    print("Loaded with openpyxl")
except Exception as e:
    print(f"openpyxl failed: {e}")
    try:
        content_io.seek(0)
        df = pd.read_excel(content_io, engine="xlrd")
        print("Loaded with xlrd")
    except Exception as e2:
        print(f"xlrd failed: {e2}")
        try:
            content_io.seek(0)
            dfs = pd.read_html(content_io)
            if dfs:
                df = dfs[0]
                print("Loaded as HTML table")
        except Exception as e3:
            print(f"HTML read failed: {e3}")

if df is None:
    print("Could not load DataFrame")
    sys.exit(1)

print(f"Loaded successfully. Total rows: {len(df)}")
print(f"Columns: {list(df.columns)}")

# Normalized column finder
def get_val_col(columns, target):
    t_norm = str(target).lower().replace(" ", "").replace("_", "").replace("-", "")
    for col in columns:
        if str(col).lower().replace(" ", "").replace("_", "").replace("-", "") == t_norm:
            return col
    return None

rgn_col = get_val_col(df.columns, 'rgn_animal') or get_val_col(df.columns, 'rgn') or get_val_col(df.columns, 'registro')
print(f"Identified RGN column: {rgn_col}")

if rgn_col:
    # Clean up empty rows
    initial_len = len(df)
    df_non_empty = df.dropna(how='all')
    print(f"Rows after dropping completely empty rows (dropna(how='all')): {len(df_non_empty)}")
    
    series = df_non_empty[rgn_col].astype(str).str.strip().str.upper()
    series_cleaned = series.replace(['NAN', 'NONE', '', 'NAT', 'NOT A TIME'], None).dropna()
    print(f"Rows with non-null/cleaned RGN: {len(series_cleaned)}")
    print(f"Rows with null/empty/NaN RGN: {len(df_non_empty) - len(series_cleaned)}")
    
    # Check duplicates in clean series
    unique_count = series_cleaned.nunique()
    print(f"Unique RGN count: {unique_count}")
    print(f"Duplicate RGN rows: {len(series_cleaned) - unique_count}")
    
    serie_col = get_val_col(df.columns, 'serie_animal') or get_val_col(df.columns, 'serie') or get_val_col(df.columns, 'série')
    print(f"Identified Serie column: {serie_col}")
    
    if serie_col:
        df_non_empty['serie_cleaned'] = df_non_empty[serie_col].astype(str).str.strip().str.upper().replace(['NAN', 'NONE', '', 'NAT', 'NOT A TIME'], None)
        unique_combo = df_non_empty.drop_duplicates(subset=[rgn_col, serie_col])
        print(f"Unique (RGN, Serie) combination count: {len(unique_combo)}")
        print(f"Duplicate (RGN, Serie) combination rows: {len(df_non_empty) - len(unique_combo)}")
    
    # Let's see if duplicates are identical rows or different evaluations
    dups_list = series_cleaned[series_cleaned.duplicated()].unique()
    if len(dups_list) > 0:
        print(f"Total unique RGNs that have duplicate rows: {len(dups_list)}")
        print(f"Example duplicate RGN: {dups_list[0]}")
        example_rows = df_non_empty[df_non_empty[rgn_col].astype(str).str.strip().str.upper() == dups_list[0]]
        print("Example rows for this RGN:")
        print(example_rows.to_string())
else:
    print("No RGN column found in the file!")
