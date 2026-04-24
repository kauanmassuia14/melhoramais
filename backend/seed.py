from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from backend.models import ColumnMapping, Farm, Base
from backend.database import engine


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

    mappings = []

    # =============================================
    # ANCP - Todas as colunas
    # =============================================
    mappings.extend([
        # Identificação
        ColumnMapping(source_system="ANCP", source_column="RGN", target_column="rgn_animal", data_type="string", is_required=True),
        ColumnMapping(source_system="ANCP", source_column="NOME", target_column="nome_animal", data_type="string"),
        ColumnMapping(source_system="ANCP", source_column="SEXO", target_column="sexo", data_type="string"),
        ColumnMapping(source_system="ANCP", source_column="DT_NASC", target_column="data_nascimento", data_type="date"),
        ColumnMapping(source_system="ANCP", source_column="RACA", target_column="raca", data_type="string"),
        
        # Genealogia - 1ª geração
        ColumnMapping(source_system="ANCP", source_column="MAE_RGN", target_column="mae_rgn", data_type="string"),
        ColumnMapping(source_system="ANCP", source_column="PAI_RGN", target_column="pai_rgn", data_type="string"),
        
        # Genealogia - 2ª geração
        ColumnMapping(source_system="ANCP", source_column="AVO_PAT_RGN", target_column="avo_paterno_rgn", data_type="string"),
        ColumnMapping(source_system="ANCP", source_column="AVO_PAT_MAE_RGN", target_column="avo_paterno_mae_rgn", data_type="string"),
        ColumnMapping(source_system="ANCP", source_column="AVO_MAT_RGN", target_column="avo_materno_rgn", data_type="string"),
        ColumnMapping(source_system="ANCP", source_column="AVO_MAT_MAE_RGN", target_column="avo_materno_mae_rgn", data_type="string"),
        
        # Pesos
        ColumnMapping(source_system="ANCP", source_column="PESO_NASC", target_column="peso_nascimento", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="PESO_DESM", target_column="p210_peso_desmama", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="P365", target_column="p365_peso_ano", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="PESO_SOBRE", target_column="p450_peso_sobreano", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="PESO_FINAL", target_column="peso_final", data_type="float"),
        
        # Medidas
        ColumnMapping(source_system="ANCP", source_column="PE", target_column="pe_perimetro_escrotal", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="AOL", target_column="a_area_olho_lombo", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="EGP", target_column="eg_espessura_gordura", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="ALTURA", target_column="altura", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="CIRCUNFERENCIA", target_column="circumference", data_type="float"),
        
        # Reprodução
        ColumnMapping(source_system="ANCP", source_column="IPP", target_column="im_idade_primeiro_parto", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="INTERV_PARTOS", target_column="intervalo_partos", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="DIAS_GEST", target_column="dias_gestacao", data_type="float"),
        
        # ANCP - DEP (Direct Predicted)
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
        
        # ANCP - DEP Individuais
        ColumnMapping(source_system="ANCP", source_column="DIPP", target_column="anc_dipp", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="D3P", target_column="anc_d3p", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="DSTAY", target_column="anc_dstay", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="DPN", target_column="anc_dpn", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="DP12", target_column="anc_dp12", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="DPE", target_column="anc_dpe", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="DAOL", target_column="anc_daol", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="DACAB", target_column="anc_dacab", data_type="float"),
        
        # ANCP - AC (Accuracy)
        ColumnMapping(source_system="ANCP", source_column="AC_MG", target_column="anc_ac_mg", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="AC_Te", target_column="anc_ac_te", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="AC_M", target_column="anc_ac_m", data_type="float"),
        ColumnMapping(source_system="ANCP", source_column="AC_P", target_column="anc_ac_p", data_type="float"),
    ])

    # =============================================
    # GENEPLUS - Todas as colunas
    # =============================================
    mappings.extend([
        # Identificação
        ColumnMapping(source_system="GENEPLUS", source_column="RGN", target_column="rgn_animal", data_type="string", is_required=True),
        ColumnMapping(source_system="GENEPLUS", source_column="NOME", target_column="nome_animal", data_type="string"),
        ColumnMapping(source_system="GENEPLUS", source_column="SEXO", target_column="sexo", data_type="string"),
        ColumnMapping(source_system="GENEPLUS", source_column="DT_NASC", target_column="data_nascimento", data_type="date"),
        ColumnMapping(source_system="GENEPLUS", source_column="RACA", target_column="raca", data_type="string"),
        
        # Genealogia - 1ª geração
        ColumnMapping(source_system="GENEPLUS", source_column="MAE_RGN", target_column="mae_rgn", data_type="string"),
        ColumnMapping(source_system="GENEPLUS", source_column="PAI_RGN", target_column="pai_rgn", data_type="string"),
        
        # Genealogia - 2ª geração
        ColumnMapping(source_system="GENEPLUS", source_column="AVO_PAT_RGN", target_column="avo_paterno_rgn", data_type="string"),
        ColumnMapping(source_system="GENEPLUS", source_column="AVO_PAT_MAE_RGN", target_column="avo_paterno_mae_rgn", data_type="string"),
        ColumnMapping(source_system="GENEPLUS", source_column="AVO_MAT_RGN", target_column="avo_materno_rgn", data_type="string"),
        ColumnMapping(source_system="GENEPLUS", source_column="AVO_MAT_MAE_RGN", target_column="avo_materno_mae_rgn", data_type="string"),
        
        # Pesos
        ColumnMapping(source_system="GENEPLUS", source_column="PESO_NASC", target_column="peso_nascimento", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="PESO_DESM", target_column="p210_peso_desmama", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="P365", target_column="p365_peso_ano", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="PESO_SOBRE", target_column="p450_peso_sobreano", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="PESO_FINAL", target_column="peso_final", data_type="float"),
        
        # Medidas
        ColumnMapping(source_system="GENEPLUS", source_column="PE", target_column="pe_perimetro_escrotal", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="AOL", target_column="a_area_olho_lombo", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="EGP", target_column="eg_espessura_gordura", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="ALTURA", target_column="altura", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="CIRCUNFERENCIA", target_column="circumference", data_type="float"),
        
        # Reprodução
        ColumnMapping(source_system="GENEPLUS", source_column="IPP", target_column="im_idade_primeiro_parto", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="INTERV_PARTOS", target_column="intervalo_partos", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="DIAS_GEST", target_column="dias_gestacao", data_type="float"),
        
        # GENEPLUS - Benchmarking
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
        
        # GENEPLUS - DEP Individuais
        ColumnMapping(source_system="GENEPLUS", source_column="PN", target_column="gen_pn", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="P120", target_column="gen_p120", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="TMD", target_column="gen_tmd", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="PD", target_column="gen_pd", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="TM120", target_column="gen_tm120", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="PS", target_column="gen_ps", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="GPD", target_column="gen_gpd", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="CFD", target_column="gen_cfd", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="CFS", target_column="gen_cfs", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="HP_STAY", target_column="gen_hp_stay", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="RD", target_column="gen_rd", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="EGS", target_column="gen_egs", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="ACAB", target_column="gen_acab", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="MAR", target_column="gen_mar", data_type="float"),
        
        # GENEPLUS - AC
        ColumnMapping(source_system="GENEPLUS", source_column="AC_IQG", target_column="gen_ac_iqg", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="AC_PMm", target_column="gen_ac_pmm", data_type="float"),
        ColumnMapping(source_system="GENEPLUS", source_column="AC_P", target_column="gen_ac_p", data_type="float"),
    ])

    # =============================================
    # PMGZ - Todas as colunas
    # =============================================
    mappings.extend([
        # Identificação
        ColumnMapping(source_system="PMGZ", source_column="RGN", target_column="rgn_animal", data_type="string", is_required=True),
        ColumnMapping(source_system="PMGZ", source_column="NOME", target_column="nome_animal", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="SEXO", target_column="sexo", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="NASC", target_column="data_nascimento", data_type="date"),
        ColumnMapping(source_system="PMGZ", source_column="SERIE / RGD", target_column="raca", data_type="string"),
        
        # Genealogia - 1ª geração (pandas renomeia duplicatas)
        ColumnMapping(source_system="PMGZ", source_column="RGN.1", target_column="pai_rgn", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="RGN.4", target_column="mae_rgn", data_type="string"),
        
        # Genealogia - 2ª geração
        ColumnMapping(source_system="PMGZ", source_column="AVO_PAT_RGN", target_column="avo_paterno_rgn", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="AVO_PAT_MAE_RGN", target_column="avo_paterno_mae_rgn", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="AVO_MAT_RGN", target_column="avo_materno_rgn", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="AVO_MAT_MAE_RGN", target_column="avo_materno_mae_rgn", data_type="string"),
        
        # Pesos
        ColumnMapping(source_system="PMGZ", source_column="PESO_NASC", target_column="peso_nascimento", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="P210", target_column="p210_peso_desmama", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="P365", target_column="p365_peso_ano", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="P450", target_column="p450_peso_sobreano", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="PESO_FINAL", target_column="peso_final", data_type="float"),
        
        # Medidas
        ColumnMapping(source_system="PMGZ", source_column="PE", target_column="pe_perimetro_escrotal", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="AOL", target_column="a_area_olho_lombo", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="EGP", target_column="eg_espessura_gordura", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="ALTURA", target_column="altura", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="CIRCUNFERENCIA", target_column="circumference", data_type="float"),
        
        # Reprodução
        ColumnMapping(source_system="PMGZ", source_column="IPP", target_column="im_idade_primeiro_parto", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="INTERV_PARTOS", target_column="intervalo_partos", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="DIAS_GEST", target_column="dias_gestacao", data_type="float"),
        
        # PMGZ - Índice Geral
        ColumnMapping(source_system="PMGZ", source_column="iABCZg", target_column="pmg_iabc", data_type="float"),
        
        # PMGZ - Benchmarking
        ColumnMapping(source_system="PMGZ", source_column="ZPMm", target_column="pmg_zpmm", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="P", target_column="pmg_p", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="DP", target_column="pmg_dp", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="SP", target_column="pmg_sp", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="E", target_column="pmg_e", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="SAO", target_column="pmg_sao", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="LEG", target_column="pmg_leg", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="SH", target_column="pmg_sh", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="PP30", target_column="pmg_pp30", data_type="float"),
        
        # PMGZ - DEP Individuais
        ColumnMapping(source_system="PMGZ", source_column="PN-EDg", target_column="pmg_pn", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="PA-EDg", target_column="pmg_pa", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="PS-EDg", target_column="pmg_ps", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="PM-EMg", target_column="pmg_pm", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="IPPg", target_column="pmg_ipp", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="STAY", target_column="pmg_stay", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="PE-365g", target_column="pmg_pe", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="AOLg", target_column="pmg_aol", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="ACABg", target_column="pmg_acab", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="MARg", target_column="pmg_mar", data_type="float"),
        
        # PMGZ - DECA
        ColumnMapping(source_system="PMGZ", source_column="DECA", target_column="pmg_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="DECA_PN", target_column="pmg_deca_pn", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="DECA_P12", target_column="pmg_deca_p12", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="DECA_PS", target_column="pmg_deca_ps", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="DECA_STAY", target_column="pmg_deca_stay", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="DECA_PE", target_column="pmg_deca_pe", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="DECA_AOL", target_column="pmg_deca_aol", data_type="string"),
        
        # PMGZ - Metas
        ColumnMapping(source_system="PMGZ", source_column="META_P", target_column="pmg_meta_p", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="META_M", target_column="pmg_meta_m", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="META_T", target_column="pmg_meta_t", data_type="float"),
        
        # PMGZ - AC
        ColumnMapping(source_system="PMGZ", source_column="AC_iABCZ", target_column="pmg_ac_iabc", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="AC_P", target_column="pmg_ac_p", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="AC_M", target_column="pmg_ac_m", data_type="float"),
    ])

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