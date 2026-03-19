from sqlalchemy.orm import Session
from .models import ColumnMapping, Base
from .main import engine
from sqlalchemy.orm import sessionmaker

def seed():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Check if mappings already exist
    if db.query(ColumnMapping).count() > 0:
        print("Mappings already seeded.")
        return

    mappings = [
        # ANCP
        ColumnMapping(source_system='ANCP', source_column='RGN', target_column='rgn_animal', data_type='string'),
        ColumnMapping(source_system='ANCP', source_column='NOME', target_column='nome_animal', data_type='string'),
        ColumnMapping(source_system='ANCP', source_column='SEXO', target_column='sexo', data_type='string'),
        ColumnMapping(source_system='ANCP', source_column='DT_NASC', target_column='data_nascimento', data_type='date'),
        ColumnMapping(source_system='ANCP', source_column='PESO_DESM', target_column='p210_peso_desmama', data_type='float'),
        ColumnMapping(source_system='ANCP', source_column='PESO_SOBRE', target_column='p450_peso_sobreano', data_type='float'),

        # PMGZ
        ColumnMapping(source_system='PMGZ', source_column='Registro', target_column='rgn_animal', data_type='string'),
        ColumnMapping(source_system='PMGZ', source_column='Nome', target_column='nome_animal', data_type='string'),
        ColumnMapping(source_system='PMGZ', source_column='P210', target_column='p210_peso_desmama', data_type='float'),
        ColumnMapping(source_system='PMGZ', source_column='P365', target_column='p365_peso_ano', data_type='float'),
        ColumnMapping(source_system='PMGZ', source_column='P450', target_column='p450_peso_sobreano', data_type='float'),

        # Geneplus
        ColumnMapping(source_system='Geneplus', source_column='PREFIXO_RGN', target_column='rgn_animal', data_type='string'),
        ColumnMapping(source_system='Geneplus', source_column='P_DESM', target_column='p210_peso_desmama', data_type='float'),
        ColumnMapping(source_system='Geneplus', source_column='P_SOBRE', target_column='p450_peso_sobreano', data_type='float'),
    ]

    try:
        db.add_all(mappings)
        db.commit()
        print("Mappings seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding mappings: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
