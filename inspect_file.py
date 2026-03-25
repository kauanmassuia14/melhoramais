"""Script para inspecionar colunas de qualquer arquivo genético.
Uso: poetry run python inspect_file.py <caminho_do_arquivo>
"""
import sys
import pandas as pd
import io

if len(sys.argv) < 2:
    print("Uso: poetry run python inspect_file.py <arquivo>")
    sys.exit(1)

filepath = sys.argv[1]
filename = filepath.split("/")[-1]

print(f"=== Inspecionando: {filename} ===\n")

if filename.endswith((".xlsx", ".xls")):
    df = pd.read_excel(filepath)
elif filename.endswith(".csv"):
    df = pd.read_csv(filepath)
else:
    print(f"Formato não suportado: {filename}")
    sys.exit(1)

print("COLUNAS ENCONTRADAS:")
for i, col in enumerate(df.columns, 1):
    dtype = df[col].dtype
    sample = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else "(vazio)"
    print(f"  {i:2d}. '{col}' (tipo: {dtype}, exemplo: {sample})")

print(f"\nTOTAL: {len(df)} linhas, {len(df.columns)} colunas")
print(f"\nPRIMEIRAS 3 LINHAS:")
print(df.head(3).to_string())
