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
        
        # =============================================
        # PMGZ - NOVO FORMATO CAVAFUNDA
        # =============================================
        
        # ANIMAL - dados básicos
        ColumnMapping(source_system="PMGZ", source_column="NOME", target_column="nome_animal", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="SERIE / RGD", target_column="pmg_serie_rgd", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="RGN", target_column="rgn_animal", data_type="string", is_required=True),
        ColumnMapping(source_system="PMGZ", source_column="SEXO", target_column="sexo", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="NASC", target_column="data_nascimento", data_type="date"),
        ColumnMapping(source_system="PMGZ", source_column="iABCZg", target_column="pmg_iabc", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="DECA", target_column="pmg_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="P %", target_column="pmg_p_percent", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="F %", target_column="pmg_f_percent", data_type="float"),
        
        # Genealogia expandida
        ColumnMapping(source_system="PMGZ", source_column="PAI", target_column="pai_nome", data_type="string"),  # Nome
        ColumnMapping(source_system="PMGZ", source_column="PAI SERIE", target_column="pai_serie_rgd", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="PAI RGN", target_column="pai_rgn", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="MÃE", target_column="mae_nome", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="MÃE SERIE", target_column="mae_serie_rgd", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="MÃE RGN", target_column="mae_rgn", data_type="string"),
        
        # CARACTERÍSTICAS DE CRESCIMENTO - PN-EDg
        ColumnMapping(source_system="PMGZ", source_column="Peso ao nascimento - efeito direto (PN-EDg) - kg", target_column="pmg_pn_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Peso ao nascimento - efeito direto (PN-EDg) - kg AC%", target_column="pmg_pn_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Peso ao nascimento - efeito direto (PN-EDg) - kg DECA", target_column="pmg_pn_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Peso ao nascimento - efeito direto (PN-EDg) - kg P %", target_column="pmg_pn_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS DE CRESCIMENTO - PD-EDg
        ColumnMapping(source_system="PMGZ", source_column="Peso à desmama - efeito direto (PD-EDg) - kg", target_column="pmg_pd_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Peso à desmama - efeito direto (PD-EDg) - kg AC%", target_column="pmg_pd_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Peso à desmama - efeito direto (PD-EDg) - kg DECA", target_column="pmg_pd_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Peso à desmama - efeito direto (PD-EDg) - kg P %", target_column="pmg_pd_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS DE CRESCIMENTO - PA-EDg
        ColumnMapping(source_system="PMGZ", source_column="Peso ao ano - efeito direto (PA-EDg)", target_column="pmg_pa_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Peso ao ano - efeito direto (PA-EDg) AC%", target_column="pmg_pa_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Peso ao ano - efeito direto (PA-EDg) DECA", target_column="pmg_pa_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Peso ao ano - efeito direto (PA-EDg) P %", target_column="pmg_pa_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS DE CRESCIMENTO - PS-EDg
        ColumnMapping(source_system="PMGZ", source_column="Peso ao sobreano - efeito direto (PS-EDg) - kg", target_column="pmg_ps_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Peso ao sobreano - efeito direto (PS-EDg) - kg AC%", target_column="pmg_ps_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Peso ao sobreano - efeito direto (PS-EDg) - kg DECA", target_column="pmg_ps_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Peso ao sobreano - efeito direto (PS-EDg) - kg P %", target_column="pmg_ps_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS MATERNAS - PM-EMg
        ColumnMapping(source_system="PMGZ", source_column="Peso à fase materna - efeito materno (PM-EMg) - kg", target_column="pmg_pm_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Peso à fase materna - efeito materno (PM-EMg) - kg AC%", target_column="pmg_pm_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Peso à fase materna - efeito materno (PM-EMg) - kg DECA", target_column="pmg_pm_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Peso à fase materna - efeito materno (PM-EMg) - kg P %", target_column="pmg_pm_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS REPRODUTIVAS - IPPg
        ColumnMapping(source_system="PMGZ", source_column="Idade ao primeiro parto (IPPg) - dias", target_column="pmg_ipp_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Idade ao primeiro parto (IPPg) - dias AC%", target_column="pmg_ipp_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Idade ao primeiro parto (IPPg) - dias DECA", target_column="pmg_ipp_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Idade ao primeiro parto (IPPg) - dias P %", target_column="pmg_ipp_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS REPRODUTIVAS - STAYg
        ColumnMapping(source_system="PMGZ", source_column="Stayability (STAYg) - %", target_column="pmg_stay_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Stayability (STAYg) - % AC%", target_column="pmg_stay_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Stayability (STAYg) - % DECA", target_column="pmg_stay_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Stayability (STAYg) - % P %", target_column="pmg_stay_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS REPRODUTIVAS - PE-365g
        ColumnMapping(source_system="PMGZ", source_column="Perímetro escrotal aos 365 dias (PE-365g) - cm", target_column="pmg_pe365_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Perímetro escrotal aos 365 dias (PE-365g) - cm AC%", target_column="pmg_pe365_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Perímetro escrotal aos 365 dias (PE-365g) - cm DECA", target_column="pmg_pe365_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Perímetro escrotal aos 365 dias (PE-365g) - cm P %", target_column="pmg_pe365_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS REPRODUTIVAS - PSNg
        ColumnMapping(source_system="PMGZ", source_column="Precocidade Sexual Natural ( PSNg ) %", target_column="pmg_psn_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Precocidade Sexual Natural ( PSNg ) % AC%", target_column="pmg_psn_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Precocidade Sexual Natural ( PSNg ) % DECA", target_column="pmg_psn_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Precocidade Sexual Natural ( PSNg ) % P %", target_column="pmg_psn_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS DE CARCAÇA - AOLg
        ColumnMapping(source_system="PMGZ", source_column="Área de olho de lombo (AOLg) - cm²", target_column="pmg_aol_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Área de olho de lombo (AOLg) - cm² AC%", target_column="pmg_aol_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Área de olho de lombo (AOLg) - cm² DECA", target_column="pmg_aol_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Área de olho de lombo (AOLg) - cm² P %", target_column="pmg_aol_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS DE CARCAÇA - ACABg
        ColumnMapping(source_system="PMGZ", source_column="Acabamento de carcaça (ACABg) - mm", target_column="pmg_acab_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Acabamento de carcaça (ACABg) - mm AC%", target_column="pmg_acab_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Acabamento de carcaça (ACABg) - mm DECA", target_column="pmg_acab_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Acabamento de carcaça (ACABg) - mm P %", target_column="pmg_acab_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS DE CARCAÇA - MARg
        ColumnMapping(source_system="PMGZ", source_column="Marmoreio (MARg) %", target_column="pmg_mar_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Marmoreio (MARg) % AC%", target_column="pmg_mar_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Marmoreio (MARg) % DECA", target_column="pmg_mar_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Marmoreio (MARg) % P %", target_column="pmg_mar_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS MORFOLÓGICAS - Eg
        ColumnMapping(source_system="PMGZ", source_column="Estrutura corporal (Eg)", target_column="pmg_eg_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Estrutura corporal (Eg) AC%", target_column="pmg_eg_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Estrutura corporal (Eg) DECA", target_column="pmg_eg_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Estrutura corporal (Eg) P %", target_column="pmg_eg_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS MORFOLÓGICAS - Pg
        ColumnMapping(source_system="PMGZ", source_column="Precocidade (Pg)", target_column="pmg_p_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Precocidade (Pg) AC%", target_column="pmg_p_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Precocidade (Pg) DECA", target_column="pmg_p_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Precocidade (Pg) P %", target_column="pmg_p_p_percent", data_type="float"),
        
        # CARACTERÍSTICAS MORFOLÓGICAS - Mg
        ColumnMapping(source_system="PMGZ", source_column="Musculosidade (Mg)", target_column="pmg_m_dep", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Musculosidade (Mg) AC%", target_column="pmg_m_ac", data_type="float"),
        ColumnMapping(source_system="PMGZ", source_column="Musculosidade (Mg) DECA", target_column="pmg_m_deca", data_type="string"),
        ColumnMapping(source_system="PMGZ", source_column="Musculosidade (Mg) P %", target_column="pmg_m_p_percent", data_type="float"),
        
        # PESOS (colunas simples)
        ColumnMapping(source_system="PMGZ", source_column="Peso aos 120 dias (P120)", target_column="p120_peso_120", data_type="float"),
        
        # INFORMAÇÕES DE DESCENDENTES
        ColumnMapping(source_system="PMGZ", source_column="Peso aos 120 dias (P120) FILHOS", target_column="desc_p120_filhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Peso aos 120 dias (P120) REBANHOS", target_column="desc_p120_rebanhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Peso aos 210 dias (P210) FILHOS", target_column="desc_p210_filhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Peso aos 210 dias (P210) REBANHOS", target_column="desc_p210_rebanhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Peso aos 365 dias (P365) FILHOS", target_column="desc_p365_filhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Peso aos 365 dias (P365) REBANHOS", target_column="desc_p365_rebanhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Peso aos 450 dias (P450) FILHOS", target_column="desc_p450_filhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Peso aos 450 dias (P450) REBANHOS", target_column="desc_p450_rebanhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Peso aos 120 dias (P120) NETOS", target_column="desc_p120_netosc", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Peso aos 120 dias (P120) NETOS REBANHOS", target_column="desc_p120_netosc_rebanhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Peso aos 210 dias (P210) NETOS", target_column="desc_p210_netosc", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Peso aos 210 dias (P210) NETOS REBANHOS", target_column="desc_p210_netosc_rebanhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Perímetro Escrotal aos 365 dias (PE365) FILHOS", target_column="desc_pe365_filhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Perímetro Escrotal aos 365 dias (PE365) REBANHOS", target_column="desc_pe365_rebanhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Fenótipo Stayability (STAY) FILHOS", target_column="desc_stay_filhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Fenótipo Stayability (STAY) REBANHOS", target_column="desc_stay_rebanhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Fenótipo Idade ao Primeiro Parto (IPP) FILHOS", target_column="desc_ipp_filhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Fenótipo Idade ao Primeiro Parto (IPP) REBANHOS", target_column="desc_ipp_rebanhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Medida Área Olho de Lombo (AOL) FILHOS", target_column="desc_aol_filhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Medida Área Olho de Lombo (AOL) REBANHOS", target_column="desc_aol_rebanhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Medida Acabamento de Carcaça (ACAB) FILHOS", target_column="desc_acab_filhos", data_type="integer"),
        ColumnMapping(source_system="PMGZ", source_column="Medida Acabamento de Carcaça (ACAB) REBANHOS", target_column="desc_acab_rebanhos", data_type="integer"),
        
        # INFORMAÇÕES EXTRAS
        ColumnMapping(source_system="PMGZ", source_column="GENOTIPADO", target_column="genotipado", data_type="boolean"),
        ColumnMapping(source_system="PMGZ", source_column="CSG", target_column="csg", data_type="boolean"),
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