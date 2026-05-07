import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.models import ColumnMapping

def seed_mappings():
    db = SessionLocal()
    try:
        mappings = [
            # ANCP Standard Mappings
            {"source_system": "ANCP", "source_column": "RGN", "target_column": "rgn_animal", "is_required": True},
            {"source_system": "ANCP", "source_column": "Nome", "target_column": "nome_animal", "is_required": False},
            {"source_system": "ANCP", "source_column": "Sexo", "target_column": "sexo", "is_required": False},
            {"source_system": "ANCP", "source_column": "Nasc", "target_column": "data_nascimento", "is_required": False},
            {"source_system": "ANCP", "source_column": "Raça", "target_column": "raca", "is_required": False},
            {"source_system": "ANCP", "source_column": "MGTe", "target_column": "MGTe", "is_required": False},
            {"source_system": "ANCP", "source_column": "TOP_MGTe", "target_column": "TOP_MGTe", "is_required": False},
            {"source_system": "ANCP", "source_column": "DPN", "target_column": "DPN", "is_required": False},
            {"source_system": "ANCP", "source_column": "ACC_DPN", "target_column": "ACC_DPN", "is_required": False},
            {"source_system": "ANCP", "source_column": "TOP_DPN", "target_column": "TOP_DPN", "is_required": False},
        ]
        
        for m in mappings:
            # Check if exists
            exists = db.query(ColumnMapping).filter_by(
                source_system=m["source_system"], 
                source_column=m["source_column"]
            ).first()
            
            if not exists:
                db.add(ColumnMapping(**m))
        
        db.commit()
        print("Mappings seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding mappings: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_mappings()
