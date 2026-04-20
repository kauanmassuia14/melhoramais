#!/usr/bin/env python3
"""
Script para importar clientes do CSV para o banco PostgreSQL.
Uso: python import_clientes.py
"""
import csv
import os
import sys
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from models import Cliente, Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kauan:viruss@localhost:5432/melhoramais_agro")
CSV_PATH = os.path.expanduser("~/Downloads/Clientes Melhora Mais 2025  - Nome e endereço.csv")


def clean_value(value):
    """Limpa e normaliza valores do CSV."""
    if value is None:
        return None
    value = str(value).strip()
    if value == '' or value == 'None':
        return None
    return value


def parse_status(observacoes):
    """Extrai status das observações."""
    if not observacoes:
        return None
    obs_lower = observacoes.lower()
    if 'desligado' in obs_lower:
        return 'desligado'
    if 'possível cliente' in obs_lower or 'possivel cliente' in obs_lower:
        return 'prospecto'
    return None


def main():
    print(f"Conectando ao banco: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Cria a tabela se não existir
    Base.metadata.create_all(engine, tables=[Cliente.__table__])
    
    Session = sessionmaker(bind=engine)
    db = Session()
    
    print(f"Lendo CSV: {CSV_PATH}")
    
    clientes_inseridos = 0
    clientes_ignorados = 0
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        # Pula as 3 linhas de cabeçalho
        next(reader)  # "CLIENTES - 2025"
        next(reader)  # Sub-cabeçalho
        next(reader)  # Cabeçalho das colunas
        
        for row_num, row in enumerate(reader, start=4):
            # Pula linhas vazias ou de cabeçalho repetido
            if not row or not row[0] or row[0].strip() == '' or row[0].strip().startswith('CLIENTES'):
                clientes_ignorados += 1
                continue
            
            proprietario = clean_value(row[0])
            if not proprietario:
                clientes_ignorados += 1
                continue
            
            # Remove duplicatas (linhas 12 e 32 são "ÁGUAS DO CAETÊ" duplicado)
            existing = db.query(Cliente).filter(Cliente.proprietario == proprietario).first()
            if existing:
                print(f"  [SKIP] Cliente já existe: {proprietario}")
                clientes_ignorados += 1
                continue
            
            observacoes = clean_value(row[23]) if len(row) > 23 else None
            status = parse_status(observacoes)
            
            cliente = Cliente(
                proprietario=proprietario,
                data_nascimento=clean_value(row[1]) if len(row) > 1 else None,
                fazenda_empresa=clean_value(row[2]) if len(row) > 2 else None,
                cnpj_cpf=clean_value(row[3]) if len(row) > 3 else None,
                contato=clean_value(row[4]) if len(row) > 4 else None,
                endereco=clean_value(row[5]) if len(row) > 5 else None,
                municipio=clean_value(row[6]) if len(row) > 6 else None,
                uf=clean_value(row[7]) if len(row) > 7 else None,
                cep=clean_value(row[8]) if len(row) > 8 else None,
                endereco_correspondencia=clean_value(row[9]) if len(row) > 9 else None,
                fones=clean_value(row[10]) if len(row) > 10 else None,
                coordenador=clean_value(row[11]) if len(row) > 11 else None,
                gado=clean_value(row[12]) if len(row) > 12 else None,
                rebanho=clean_value(row[13]) if len(row) > 13 else None,
                software=clean_value(row[14]) if len(row) > 14 else None,
                programa_melhoramento=clean_value(row[15]) if len(row) > 15 else None,
                nome_financeiro=clean_value(row[16]) if len(row) > 16 else None,
                whatsapp_financeiro=clean_value(row[17]) if len(row) > 17 else None,
                email=clean_value(row[18]) if len(row) > 18 else None,
                endereco_financeiro=clean_value(row[19]) if len(row) > 19 else None,
                contrato=clean_value(row[20]) if len(row) > 20 else None,
                nf=clean_value(row[21]) if len(row) > 21 else None,
                venc_boleto=clean_value(row[22]) if len(row) > 22 else None,
                observacoes=observacoes,
                status=status,
            )
            
            db.add(cliente)
            clientes_inseridos += 1
            print(f"  [OK] {proprietario}")
    
    db.commit()
    db.close()
    
    print(f"\n=== Importação concluída ===")
    print(f"Clientes inseridos: {clientes_inseridos}")
    print(f"Clientes ignorados: {clientes_ignorados}")


if __name__ == "__main__":
    main()
