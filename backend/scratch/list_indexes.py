import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== TODOS OS ÍNDICES DE genetic_evaluations ===")
    res = conn.execute(text("""
        SELECT
            t.relname as table_name,
            i.relname as index_name,
            a.attname as column_name,
            ix.indisunique as is_unique
        FROM
            pg_class t,
            pg_class i,
            pg_index ix,
            pg_attribute a,
            pg_namespace n
        WHERE
            t.oid = ix.indrelid
            AND i.oid = ix.indexrelid
            AND a.attrelid = t.oid
            AND a.attnum = ANY(ix.indkey)
            AND t.relkind = 'r'
            AND n.oid = t.relnamespace
            AND n.nspname = 'genetics'
            AND t.relname = 'genetic_evaluations'
        ORDER BY
            t.relname,
            i.relname;
    """)).fetchall()
    
    current_index = ""
    cols = []
    for row in res:
        if row[1] != current_index:
            if current_index:
                print(f"Index: {current_index} | Columns: {', '.join(cols)}")
            current_index = row[1]
            cols = [row[2]]
        else:
            cols.append(row[2])
    if current_index:
        print(f"Index: {current_index} | Columns: {', '.join(cols)}")
