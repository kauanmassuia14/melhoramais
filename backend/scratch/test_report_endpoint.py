import os
import sys
import uuid as _uuid
import json
import statistics

# Add the parent folder to the path so we can import backend packages
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import SessionLocal
from models import GeneticsFarm, GeneticsAnimal, GeneticsGeneticEvaluation, ProcessingLog
from sqlalchemy import func
from report_generator_v2 import ReportGeneratorV2

def test_report_logic():
    print("Initializing test...")
    db = SessionLocal()
    try:
        # 1. Fetch a valid farm
        farm = db.query(GeneticsFarm).first()
        if not farm:
            print("ERROR: No farms found in database!")
            return
        
        farm_uuid = farm.id
        farm_name = farm.nome
        print(f"Testing for Farm: {farm_name} ({farm_uuid})")

        # 2. Get animal count
        animal_query = db.query(GeneticsAnimal).filter(GeneticsAnimal.farm_id == farm_uuid)
        total_animals = animal_query.count()
        print(f"Total Animals: {total_animals}")

        # 3. Sex Breakdown
        sex_counts_query = (
            db.query(GeneticsAnimal.sexo, func.count(GeneticsAnimal.id))
            .filter(GeneticsAnimal.farm_id == farm_uuid)
            .group_by(GeneticsAnimal.sexo)
            .all()
        )
        animals_by_sex = {s or "unknown": c for s, c in sex_counts_query}
        print(f"Sex Breakdown: {animals_by_sex}")

        # 4. Source Platform Breakdown
        eval_query = db.query(GeneticsGeneticEvaluation).filter(GeneticsGeneticEvaluation.farm_id == farm_uuid)
        source_counts_query = (
            db.query(GeneticsGeneticEvaluation.fonte_origem, func.count(GeneticsGeneticEvaluation.id))
            .filter(GeneticsGeneticEvaluation.farm_id == farm_uuid)
            .group_by(GeneticsGeneticEvaluation.fonte_origem)
            .all()
        )
        animals_by_source = {s or "unknown": c for s, c in source_counts_query}
        print(f"Source Breakdown: {animals_by_source}")

        # 5. Weight Statistics
        all_evals = eval_query.all()
        p210_list = []
        p365_list = []
        p450_list = []

        for ev in all_evals:
            metrics = ev.metrics if isinstance(ev.metrics, dict) else {}
            if isinstance(ev.metrics, str):
                try:
                    metrics = json.loads(ev.metrics)
                except:
                    metrics = {}

            pd_m = metrics.get("PD-EDg") or metrics.get("DP210") or metrics.get("DP120")
            if pd_m and pd_m.get("dep") is not None:
                p210_list.append(float(pd_m["dep"]))

            pa_m = metrics.get("PA-EDg") or metrics.get("DP365")
            if pa_m and pa_m.get("dep") is not None:
                p365_list.append(float(pa_m["dep"]))

            ps_m = metrics.get("PS-EDg") or metrics.get("DP450")
            if ps_m and ps_m.get("dep") is not None:
                p450_list.append(float(ps_m["dep"]))

        avg_p210 = statistics.mean(p210_list) if p210_list else None
        avg_p365 = statistics.mean(p365_list) if p365_list else None
        avg_p450 = statistics.mean(p450_list) if p450_list else None
        print(f"Weight Averages: P210={avg_p210}, P365={avg_p365}, P450={avg_p450}")

        # 6. Recent Uploads
        recent_uploads = (
            db.query(ProcessingLog)
            .filter(ProcessingLog.id_farm == str(farm_uuid))
            .count()
        )
        print(f"Recent Uploads: {recent_uploads}")

        stats = {
            "total_animals": total_animals,
            "total_farms": 1,
            "animals_by_source": animals_by_source,
            "animals_by_sex": animals_by_sex,
            "recent_uploads": recent_uploads,
            "avg_p210": avg_p210,
            "avg_p365": avg_p365,
            "avg_p450": avg_p450,
        }

        # 7. Fetch animals
        animals_list = animal_query.limit(200).all()
        animals_data = []
        for a in animals_list:
            latest_eval = (
                db.query(GeneticsGeneticEvaluation)
                .filter(GeneticsGeneticEvaluation.animal_id == a.id)
                .order_by(GeneticsGeneticEvaluation.safra.desc())
                .first()
            )

            p210_val = None
            p365_val = None
            p450_val = None
            metrics = {}
            if latest_eval:
                metrics = latest_eval.metrics if isinstance(latest_eval.metrics, dict) else {}
                if isinstance(latest_eval.metrics, str):
                    try:
                        metrics = json.loads(latest_eval.metrics)
                    except:
                        metrics = {}

                pd_m = metrics.get("PD-EDg") or metrics.get("DP210") or metrics.get("DP120")
                if pd_m and pd_m.get("dep") is not None:
                    p210_val = float(pd_m["dep"])
                pa_m = metrics.get("PA-EDg") or metrics.get("DP365")
                if pa_m and pa_m.get("dep") is not None:
                    p365_val = float(pa_m["dep"])
                ps_m = metrics.get("PS-EDg") or metrics.get("DP450")
                if ps_m and ps_m.get("dep") is not None:
                    p450_val = float(ps_m["dep"])

            animals_data.append({
                "rgn_animal": a.rgn,
                "nome_animal": a.nome or "—",
                "sexo": a.sexo or "—",
                "raca": a.serie or "—",
                "p210_peso_desmama": p210_val,
                "p365_peso_ano": p365_val,
                "p450_peso_sobreano": p450_val,
                "fonte_origem": latest_eval.fonte_origem if latest_eval else "—",
                "metrics": metrics,
            })

        print(f"Animals Compiled: {len(animals_data)} records ready")

        # 8. Run PDF Generator
        print("Generating PDF report...")
        generator = ReportGeneratorV2()
        pdf_bytes = generator.generate_dashboard_report(
            stats=stats,
            animals=animals_data,
            farm_name=farm_name,
        )
        print(f"PDF Successfully Generated! Size: {len(pdf_bytes)} bytes")
        
        # Save output for inspection
        with open("test_report_output.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("PDF saved to test_report_output.pdf")

    except Exception as e:
        print("RUNTIME ERROR OCCURRED:")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_report_logic()
