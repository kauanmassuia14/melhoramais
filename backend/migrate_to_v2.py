"""
SCRIPT DE MIGRAÇÃO: Animais.old → Modelos.v2

Este script:
1. Cria as novas tabelas (animal_base, animal_platform_data, animal_snapshot, animal_audit)
2. Migra dados da tabela 'animais' antiga para as novas tabelas normalizadas
3. Preserva histórico de snapshots

Execute com:
    python -m backend.migrate_to_v2
"""

import logging
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_migration(db: Session):
    """
    Executa migração completa.
    """
    logger.info("=" * 60)
    logger.info("INICIANDO MIGRAÇÃO PARA v2")
    logger.info("=" * 60)
    
    # 1. Criar novas tabelas
    _create_new_tables(db)
    
    # 2. Migrar dados
    _migrate_animals(db)
    
    # 3. Criar índices
    _create_indexes(db)
    
    logger.info("=" * 60)
    logger.info("MIGRAÇÃO CONCLUÍDA COM SUCESSO")
    logger.info("=" * 60)


def _create_new_tables(db: Session):
    """Cria as novas tabelas."""
    logger.info("Criando novas tabelas...")
    
    if not _is_sqlite(db):
        # PostgreSQL: criar schemas
        db.execute(text("CREATE SCHEMA IF NOT EXISTS silver"))
        db.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))
        db.commit()
    
    # Tabela: animal_base
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS animal_base (
            id SERIAL PRIMARY KEY,
            id_farm INTEGER NOT NULL,
            upload_id VARCHAR(36),
            rgn_animal VARCHAR(50) NOT NULL,
            nome_animal VARCHAR(255),
            raca VARCHAR(50),
            sexo VARCHAR(1),
            data_nascimento DATE,
            mae_rgn VARCHAR(50),
            pai_rgn VARCHAR(50),
            avo_paterno_rgn VARCHAR(50),
            avo_paterno_mae_rgn VARCHAR(50),
            avo_materno_rgn VARCHAR(50),
            avo_materno_mae_rgn VARCHAR(50),
            bisavo_paterno_pai_rgn VARCHAR(50),
            bisavo_paterno_mae_pai_rgn VARCHAR(50),
            bisavo_materno_pai_rgn VARCHAR(50),
            bisavo_materno_mae_pai_rgn VARCHAR(50),
            bisavo_paterno_mae_rgn VARCHAR(50),
            bisavo_paterno_mae_mae_rgn VARCHAR(50),
            bisavo_materno_mae_rgn VARCHAR(50),
            bisavo_materno_mae_mae_rgn VARCHAR(50),
            trisavo_paterno_pai_rgn VARCHAR(50),
            trisavo_paterno_mae_pai_rgn VARCHAR(50),
            trisavo_materno_pai_rgn VARCHAR(50),
            trisavo_materno_mae_pai_rgn VARCHAR(50),
            trisavo_paterno_mae_rgn VARCHAR(50),
            trisavo_paterno_mae_mae_rgn VARCHAR(50),
            trisavo_materno_mae_rgn VARCHAR(50),
            trisavo_materno_mae_mae_rgn VARCHAR(50),
            peso_nascimento DOUBLE PRECISION,
            peso_final DOUBLE PRECISION,
            altura DOUBLE PRECISION,
            circumference DOUBLE PRECISION,
            im_idade_primeiro_parto DOUBLE PRECISION,
            intervalo_partos DOUBLE PRECISION,
            dias_gestacao DOUBLE PRECISION,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    # FK para animal_base (simplificado)
    if not _is_sqlite(db):
        db.execute(text("ALTER TABLE animal_base ADD CONSTRAINT fk_animal_base_farm FOREIGN KEY (id_farm) REFERENCES silver.fazendas(id_farm)"))
    
    db.commit()
    logger.info("  - Tabela 'animal_base' criada")
    
    # Tabela: animal_platform_data
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS animal_platform_data (
            id SERIAL PRIMARY KEY,
            animal_base_id INTEGER NOT NULL,
            platform VARCHAR(20) NOT NULL,
            fonte_origem VARCHAR(50),
            data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            idx_principal DOUBLE PRECISION,
            idx_principal_ac DOUBLE PRECISION,
            idx_maternal DOUBLE PRECISION,
            idx_maternal_ac DOUBLE PRECISION,
            idx_peso DOUBLE PRECISION,
            idx_peso_ac DOUBLE PRECISION,
            idx_sobreano DOUBLE PRECISION,
            idx_sobreano_ac DOUBLE PRECISION,
            idx_eficiencia DOUBLE PRECISION,
            idx_aol DOUBLE PRECISION,
            idx_gordura DOUBLE PRECISION,
            idx_sexo_hack DOUBLE PRECISION,
            idx_pp30 DOUBLE PRECISION,
            dep_pn DOUBLE PRECISION,
            dep_pn_ac DOUBLE PRECISION,
            dep_p210 DOUBLE PRECISION,
            dep_p210_ac DOUBLE PRECISION,
            dep_p365 DOUBLE PRECISION,
            dep_p365_ac DOUBLE PRECISION,
            dep_p450 DOUBLE PRECISION,
            dep_p450_ac DOUBLE PRECISION,
            dep_tm DOUBLE PRECISION,
            dep_tm_ac DOUBLE PRECISION,
            dep_stay DOUBLE PRECISION,
            dep_stay_ac DOUBLE PRECISION,
            dep_pe DOUBLE PRECISION,
            dep_pe_ac DOUBLE PRECISION,
            dep_aol DOUBLE PRECISION,
            dep_aol_ac DOUBLE PRECISION,
            dep_acab DOUBLE PRECISION,
            dep_acab_ac DOUBLE PRECISION,
            dep_ipp DOUBLE PRECISION,
            dep_ipp_ac DOUBLE PRECISION,
            dep_3p DOUBLE PRECISION,
            dep_ppp DOUBLE PRECISION,
            pmg_deca VARCHAR(10),
            pmg_deca_pn VARCHAR(10),
            pmg_deca_p12 VARCHAR(10),
            pmg_deca_ps VARCHAR(10),
            pmg_deca_stay VARCHAR(10),
            pmg_deca_pe VARCHAR(10),
            pmg_deca_aol VARCHAR(10),
            pmg_meta_p DOUBLE PRECISION,
            pmg_meta_m DOUBLE PRECISION,
            pmg_meta_t DOUBLE PRECISION,
            raw_data JSONB,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(animal_base_id, platform)
        )
    """))
    
    db.commit()
    logger.info("  - Tabela 'animal_platform_data' criada")
    
    # Tabela: animal_snapshot
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS animal_snapshot (
            id SERIAL PRIMARY KEY,
            animal_base_id INTEGER NOT NULL,
            platform VARCHAR(20),
            version INTEGER NOT NULL,
            snapshot_data JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            upload_id VARCHAR(36),
            motivo VARCHAR(255),
            UNIQUE(animal_base_id, version)
        )
    """))
    
    db.commit()
    logger.info("  - Tabela 'animal_snapshot' criada")
    
    # Tabela: animal_audit
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS animal_audit (
            id SERIAL PRIMARY KEY,
            animal_base_id INTEGER NOT NULL,
            platform VARCHAR(20),
            campo VARCHAR(100) NOT NULL,
            valor_anterior JSONB,
            valor_novo JSONB,
            user_id INTEGER,
            upload_id VARCHAR(36),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    db.commit()
    logger.info("  - Tabela 'animal_audit' criada")
    
    logger.info("Todas as tabelas criadas com sucesso!")


def _migrate_animals(db: Session):
    """Migra dados da tabela antiga 'animais' para as novas tabelas."""
    logger.info("Migrando dados...")
    
    # Buscar todos os animais da tabela antiga
    result = db.execute(text("SELECT * FROM animais"))
    rows = result.fetchall()
    
    if not rows:
        logger.warning("  - Nenhum animal encontrado na tabela antiga")
        return
    
    logger.info(f"  - Encontrados {len(rows)} animais para migrar")
    
    # Obter nomes das colunas da tabela antiga
    columns = result.keys()
    
    # Mapas de colunas por plataforma (do modelo antigo)
    anc_cols = [c for c in columns if c.startswith('anc_')]
    gen_cols = [c for c in columns if c.startswith('gen_')]
    pmg_cols = [c for c in columns if c.startswith('pmg_')]
    
    migrated_count = 0
    
    for row in rows:
        row_dict = dict(zip(columns, row))
        
        # 1. Criar animal_base
        animal_base_id = _insert_animal_base(db, row_dict)
        
        if animal_base_id:
            # 2. Criar platform data para cada plataforma
            # ANCP
            if any(row_dict.get(c) is not None for c in anc_cols):
                _insert_platform_data(db, animal_base_id, "ANCP", row_dict, anc_cols)
            
            # GENEPLUS
            if any(row_dict.get(c) is not None for c in gen_cols):
                _insert_platform_data(db, animal_base_id, "GENEPLUS", row_dict, gen_cols)
            
            # PMGZ
            if any(row_dict.get(c) is not None for c in pmg_cols):
                _insert_platform_data(db, animal_base_id, "PMGZ", row_dict, pmg_cols)
            
            # 3. Criar snapshot inicial
            _insert_snapshot(db, animal_base_id, row_dict, "import", row_dict.get('fonte_origem'))
            
            migrated_count += 1
    
    db.commit()
    logger.info(f"  - Migrados {migrated_count} animais com sucesso!")


def _insert_animal_base(db: Session, data: dict) -> int:
    """Insere registro em animal_base e retorna o ID."""
    base_fields = {
        'id_farm': data.get('id_farm'),
        'upload_id': data.get('upload_id'),
        'rgn_animal': data.get('rgn_animal'),
        'nome_animal': data.get('nome_animal'),
        'raca': data.get('raca'),
        'sexo': data.get('sexo'),
        'data_nascimento': data.get('data_nascimento'),
        'mae_rgn': data.get('mae_rgn'),
        'pai_rgn': data.get('pai_rgn'),
        'avo_paterno_rgn': data.get('avo_paterno_rgn'),
        'avo_paterno_mae_rgn': data.get('avo_paterno_mae_rgn'),
        'avo_materno_rgn': data.get('avo_materno_rgn'),
        'avo_materno_mae_rgn': data.get('avo_materno_mae_rgn'),
        'bisavo_paterno_pai_rgn': data.get('bisavo_paterno_pai_rgn'),
        'bisavo_paterno_mae_pai_rgn': data.get('bisavo_paterno_mae_pai_rgn'),
        'bisavo_materno_pai_rgn': data.get('bisavo_materno_pai_rgn'),
        'bisavo_materno_mae_pai_rgn': data.get('bisavo_materno_mae_pai_rgn'),
        'bisavo_paterno_mae_rgn': data.get('bisavo_paterno_mae_rgn'),
        'bisavo_paterno_mae_mae_rgn': data.get('bisavo_paterno_mae_mae_rgn'),
        'bisavo_materno_mae_rgn': data.get('bisavo_materno_mae_rgn'),
        'bisavo_materno_mae_mae_rgn': data.get('bisavo_materno_mae_mae_rgn'),
        'trisavo_paterno_pai_rgn': data.get('trisavo_paterno_pai_rgn'),
        'trisavo_paterno_mae_pai_rgn': data.get('trisavo_paterno_mae_pai_rgn'),
        'trisavo_materno_pai_rgn': data.get('trisavo_materno_pai_rgn'),
        'trisavo_materno_mae_pai_rgn': data.get('trisavo_materno_mae_pai_rgn'),
        'trisavo_paterno_mae_rgn': data.get('trisavo_paterno_mae_rgn'),
        'trisavo_paterno_mae_mae_rgn': data.get('trisavo_paterno_mae_mae_rgn'),
        'trisavo_materno_mae_rgn': data.get('trisavo_materno_mae_rgn'),
        'trisavo_materno_mae_mae_rgn': data.get('trisavo_materno_mae_mae_rgn'),
        'peso_nascimento': data.get('peso_nascimento'),
        'peso_final': data.get('peso_final'),
        'altura': data.get('altura'),
        'circumference': data.get('circumference'),
        'im_idade_primeiro_parto': data.get('im_idade_primeiro_parto'),
        'intervalo_partos': data.get('intervalo_partos'),
        'dias_gestacao': data.get('dias_gestacao'),
    }
    
    # Filtrar valores None
    base_fields = {k: v for k, v in base_fields.items() if v is not None}
    
    if not base_fields.get('rgn_animal') or not base_fields.get('id_farm'):
        logger.warning(f"  - Animal ignorado: dados insuficientes")
        return None
    
    cols = ', '.join(base_fields.keys())
    placeholders = ', '.join([f':{k}' for k in base_fields.keys()])
    
    sql = text(f"INSERT INTO animal_base ({cols}) VALUES ({placeholders}) RETURNING id")
    result = db.execute(sql, base_fields)
    db.commit()
    
    return result.scalar()


def _insert_platform_data(db: Session, animal_base_id: int, platform: str, data: dict, platform_cols: list):
    """Insere dados de uma plataforma específica."""
    # Mapear colunas do modelo antigo para o novo
    col_mapping = _get_platform_mapping(platform)
    
    fields = {
        'animal_base_id': animal_base_id,
        'platform': platform,
        'fonte_origem': data.get('fonte_origem'),
    }
    
    # Mapear colunas
    for old_col in platform_cols:
        new_col = col_mapping.get(old_col)
        if new_col and data.get(old_col) is not None:
            fields[new_col] = data.get(old_col)
    
    cols = ', '.join(fields.keys())
    placeholders = ', '.join([f':{k}' for k in fields.keys()])
    
    sql = text(f"INSERT INTO animal_platform_data ({cols}) VALUES ({placeholders})")
    
    try:
        db.execute(sql, fields)
    except Exception as e:
        logger.warning(f"  - Erro ao inserir platform data ({platform}): {e}")
    
    db.commit()


def _get_platform_mapping(platform: str) -> dict:
    """Retorna mapeamento de colunas Velhas → Novas por plataforma."""
    mappings = {
        'ANCP': {
            'anc_mg': 'idx_principal',
            'anc_te': 'idx_principal_ac',  # accuracy
            'anc_m': 'idx_maternal',
            'anc_m': 'idx_maternal_ac',
            'anc_p': 'idx_peso',
            'anc_dp': 'idx_peso_ac',
            'anc_sp': 'idx_sobreano',
            'anc_e': 'idx_eficiencia',
            'anc_sao': 'idx_aol',
            'anc_leg': 'idx_gordura',
            'anc_sh': 'idx_sexo_hack',
            'anc_pp30': 'idx_pp30',
            'anc_dipp': 'dep_ppp',
            'anc_d3p': 'dep_3p',
            'anc_dstay': 'dep_stay',
            'anc_dpn': 'dep_pn',
            'anc_dp12': 'dep_p210',
            'anc_dpe': 'dep_pe',
            'anc_daol': 'dep_aol',
            'anc_dacab': 'dep_acab',
            'anc_ac_mg': 'idx_principal_ac',
            'anc_ac_te': 'idx_principal_ac',
            'anc_ac_m': 'idx_maternal_ac',
            'anc_ac_p': 'idx_peso_ac',
        },
        'GENEPLUS': {
            'gen_iqg': 'idx_principal',
            'gen_pmm': 'idx_maternal',
            'gen_p': 'idx_peso',
            'gen_dp': 'idx_peso_ac',
            'gen_sp': 'idx_sobreano',
            'gen_e': 'idx_eficiencia',
            'gen_sao': 'idx_aol',
            'gen_leg': 'idx_gordura',
            'gen_sh': 'idx_sexo_hack',
            'gen_pp30': 'idx_pp30',
            'gen_pn': 'dep_pn',
            'gen_p120': 'dep_p210',
            'gen_tmd': 'dep_tm',
            'gen_pd': 'dep_p210',
            'gen_tm120': 'dep_tm',
            'gen_ps': 'dep_p450',
            'gen_gpd': 'dep_p450',
            'gen_cfd': 'dep_acab',
            'gen_cfs': 'dep_acab',
            'gen_hp_stay': 'dep_stay',
            'gen_rd': 'dep_pn',
            'gen_egs': 'dep_pn',
            'gen_acab': 'dep_acab',
            'gen_mar': 'dep_acab',
            'gen_ac_iqg': 'idx_principal_ac',
            'gen_ac_pmm': 'idx_maternal_ac',
            'gen_ac_p': 'idx_peso_ac',
        },
        'PMGZ': {
            'pmg_iabc': 'idx_principal',
            'pmg_zpmm': 'idx_maternal',
            'pmg_p': 'idx_peso',
            'pmg_dp': 'idx_peso_ac',
            'pmg_sp': 'idx_sobreano',
            'pmg_e': 'idx_eficiencia',
            'pmg_sao': 'idx_aol',
            'pmg_leg': 'idx_gordura',
            'pmg_sh': 'idx_sexo_hack',
            'pmg_pp30': 'idx_pp30',
            'pmg_pn': 'dep_pn',
            'pmg_pa': 'dep_pn',
            'pmg_ps': 'dep_p450',
            'pmg_pm': 'dep_tm',
            'pmg_ipp': 'dep_ipp',
            'pmg_stay': 'dep_stay',
            'pmg_pe': 'dep_pe',
            'pmg_aol': 'dep_aol',
            'pmg_acab': 'dep_acab',
            'pmg_mar': 'dep_acab',
            'pmg_deca': 'pmg_deca',
            'pmg_deca_pn': 'pmg_deca_pn',
            'pmg_deca_p12': 'pmg_deca_p12',
            'pmg_deca_ps': 'pmg_deca_ps',
            'pmg_deca_stay': 'pmg_deca_stay',
            'pmg_deca_pe': 'pmg_deca_pe',
            'pmg_deca_aol': 'pmg_deca_aol',
            'pmg_meta_p': 'pmg_meta_p',
            'pmg_meta_m': 'pmg_meta_m',
            'pmg_meta_t': 'pmg_meta_t',
            'pmg_ac_iabc': 'idx_principal_ac',
            'pmg_ac_p': 'idx_peso_ac',
            'pmg_ac_m': 'idx_maternal_ac',
        }
    }
    
    return mappings.get(platform, {})


def _insert_snapshot(db: Session, animal_base_id: int, data: dict, motivo: str, platform: str = None):
    """Cria snapshot inicial."""
    # Obter versão atual
    result = db.execute(
        text("SELECT COALESCE(MAX(version), 0) FROM animal_snapshot WHERE animal_base_id = :id"),
        {"id": animal_base_id}
    )
    current_version = result.scalar() or 0
    new_version = current_version + 1
    
    sql = text("""
        INSERT INTO animal_snapshot (animal_base_id, platform, version, snapshot_data, motivo)
        VALUES (:id, :platform, :version, :data, :motivo)
    """)
    
    db.execute(sql, {
        "id": animal_base_id,
        "platform": platform,
        "version": new_version,
        "data": str(data),  # JSON dump
        "motivo": motivo,
    })
    db.commit()


def _create_indexes(db: Session):
    """Cria índices para performance."""
    logger.info("Criando índices...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_animal_base_farm ON animal_base(id_farm)",
        "CREATE INDEX IF NOT EXISTS idx_animal_base_rgn ON animal_base(rgn_animal)",
        "CREATE INDEX IF NOT EXISTS idx_animal_base_upload ON animal_base(upload_id)",
        "CREATE INDEX IF NOT EXISTS idx_platform_data_animal ON animal_platform_data(animal_base_id)",
        "CREATE INDEX IF NOT EXISTS idx_platform_data_platform ON animal_platform_data(platform)",
        "CREATE INDEX IF NOT EXISTS idx_animal_audit_base ON animal_audit(animal_base_id)",
        "CREATE INDEX IF NOT EXISTS idx_animal_audit_created ON animal_audit(created_at)",
    ]
    
    for idx_sql in indexes:
        try:
            db.execute(text(idx_sql))
        except Exception as e:
            logger.warning(f"  - Erro ao criar índice: {e}")
    
    db.commit()
    logger.info("  - Índices criados!")


def _is_sqlite(db: Session) -> bool:
    """Verifica se é SQLite."""
    return 'sqlite' in str(db.bind.url)


if __name__ == "__main__":
    from backend.database import SessionLocal, engine
    from backend.models import Base
    
    # Criar sessão
    db = SessionLocal()
    
    try:
        run_migration(db)
    except Exception as e:
        logger.error(f"Erro durante migração: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()