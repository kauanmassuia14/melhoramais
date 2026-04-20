from sqlalchemy.orm import sessionmaker
from .models import ColumnMapping, Farm, Base
from .main import engine


def seed():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Set search path to include silver schema
    from sqlalchemy import text
    db.execute(text("SET search_path TO silver, public"))

    # Seed default farm
    if db.query(Farm).count() == 0:
        farm = Farm(nome_farm="Fazenda Desenvolvimento", responsavel="Admin")
        db.add(farm)
        db.commit()
        print("Default farm seeded.")

    # Wipe all mappings and re-seed clean
    db.query(ColumnMapping).delete()
    db.commit()

    mappings = [
        # =============================================
        # ANCP
        # =============================================
        ColumnMapping(source_system="ANCP", source_column="RGN", target_column="rgn_animal", data_type="string", is_required=True),
        ColumnMapping(source_system="ANCP", source_column="NOME", target_column="nome_animal", data_type="string"),
        ColumnMapping(source_system="ANCP", source_column="SEXO", target_column="sexo", data_type="string"),
        ColumnMapping(source_system="ANCP", source_column="DT_NASC", target_column="data_nascimento", data_type="date"),
        ColumnMapping(source_system="ANCP", source_column="RACA", target_column="raca", data_type="string"),
        ColumnMapping(source_system="ANCP", source_column="MAE_RGN", target_column="mae_rgn", data_type="string"),
        ColumnMapping(source_system="ANCP", source_column="PAI_RGN", target_column="pai_rgn", data_type="string"),
        ColumnMapping(source_system="ANCP", source_column="PESO_DESM", target_column="p210_peso_desmama", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="PESO_SOBRE", target_column="p450_peso_sobreano", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="P365", target_column="p365_peso_ano", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="PE", target_column="pe_perimetro_escrotal", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="AOL", target_column="a_area_olho_lombo", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="EGP", target_column="eg_espessura_gordura", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="IPP", target_column="im_idade_primeiro_parto", data_type="float"),
        # Benchmarking characteristics - ANCP
        ColumnMapping(source_system="ANCP", source_column="MG", target_column="anc_mg", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="Te", target_column="anc_te", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="M", target_column="anc_m", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="P", target_column="anc_p", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="DP", target_column="anc_dp", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="SP", target_column="anc_sp", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="E", target_column="anc_e", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="SAO", target_column="anc_sao", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="LEG", target_column="anc_leg", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="SH", target_column="anc_sh", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="PP30", target_column="anc_pp30", data_type="float"),

        # =============================================
        # GENEPLUS
        # =============================================
        ColumnMapping(source_system="GENEPLUS", source_column="RGN", target_column="rgn_animal", data_type="string", is_required=True),
        ColumnMapping(source_system="GENEPLUS", source_column="NOME", target_column="nome_animal", data_type="string"),
        ColumnMapping(source_system="GENEPLUS", source_column="SEXO", target_column="sexo", data_type="string"),
        ColumnMapping(source_system="GENEPLUS", source_column="DT_NASC", target_column="data_nascimento", data_type="date"),
        ColumnMapping(source_system="GENEPLUS", source_column="RACA", target_column="raca", data_type="string"),
        ColumnMapping(source_system="GENEPLUS", source_column="MAE_RGN", target_column="mae_rgn", data_type="string"),
        ColumnMapping(source_system="GENEPLUS", source_column="PAI_RGN", target_column="pai_rgn", data_type="string"),
        ColumnMapping(source_system="GENEPLUS", source_column="PESO_DESM", target_column="p210_peso_desmama", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="PESO_SOBRE", target_column="p450_peso_sobreano", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="P365", target_column="p365_peso_ano", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="PE", target_column="pe_perimetro_escrotal", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="AOL", target_column="a_area_olho_lombo", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="EGP", target_column="eg_espessura_gordura", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="IPP", target_column="im_idade_primeiro_parto", data_type="float"),
        # Benchmarking characteristics - GENEPLUS
        ColumnMapping(source_system="GENEPLUS", source_column="IQG", target_column="gen_iqg", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="PMm", target_column="gen_pmm", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="P", target_column="gen_p", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="DP", target_column="gen_dp", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="SP", target_column="gen_sp", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="E", target_column="gen_e", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="SAO", target_column="gen_sao", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="LEG", target_column="gen_leg", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="SH", target_column="gen_sh", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="PP30", target_column="gen_pp30", data_type="float"),

        # =============================================
        # PMGZ — Mapeamento REAL baseado no arquivo do usuário
        # Arquivo tem: NOME, SERIE/RGD, RGN, SEXO, NASC, iABCZg, DECA, P %, F %,
        #              depois blocos repetidos de NOME/SERIE/RGN (PAI, AVÓS, MÃE)
        #              e colunas de DEP/AC/DECA/P% para características genéticas
        # =============================================

        # Dados do animal (colunas únicas)
        ColumnMapping(source_system="PMGZ", source_column="RGN", target_column="rgn_animal", data_type="string", is_required=True),
        ColumnMapping(source_system="PMGZ", source_column="NOME", target_column="nome_animal", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="SEXO", target_column="sexo", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="NASC", target_column="data_nascimento", data_type="date"),
        ColumnMapping(source_system="PMGZ", source_column="SERIE / RGD", target_column="raca", data_type="string"),

        # Índice genético geral
        ColumnMapping(source_system="PMGZ", source_column="iABCZg", target_column="pmg_iabc", data_type="float"),

        # PAI (pandas renomeia para RGN.1 por ser duplicata)
        ColumnMapping(source_system="PMGZ", source_column="RGN.1", target_column="pai_rgn", data_type="string"),

        # MÃE (pandas renomeia para RGN.4 — 5ª ocorrência de RGN)
        ColumnMapping(source_system="PMGZ", source_column="RGN.4", target_column="mae_rgn", data_type="string"),

        # Características genéticas — blocos DEP/AC %/DECA/P %
        # Cada bloco = 4 colunas. Primeiro bloco = Peso ao nascimento (PN-EDg)
        # Segundo bloco = Peso à desmama (PD-EDg), etc.
        # Estes serão ignorados por enquanto se não mapearem a colunas da tabela animais
        # O iABCZg já mapeia para pmg_iabc como índice geral
        
        # Benchmarking characteristics - PMGZ
        ColumnMapping(source_system="PMGZ", source_column="ZPMm", target_column="pmg_zpmm", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="P", target_column="pmg_p", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="DP", target_column="pmg_dp", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="SP", target_column="pmg_sp", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="E", target_column="pmg_e", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="SAO", target_column="pmg_sao", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="LEG", target_column="pmg_leg", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="SH", target_column="pmg_sh", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="PP30", target_column="pmg_pp30", data_type="float"),
    ]

    try:
        db.add_all(mappings)
        db.commit()
        print(f"Seeded {len(mappings)} column mappings.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding mappings: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
