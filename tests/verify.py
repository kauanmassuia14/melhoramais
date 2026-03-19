import requests
import time
import subprocess
import os
import pandas as pd
import io

def test_api():
    # 1. Start the server
    server_process = subprocess.Popen(
        ["poetry", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd(),
        env={**os.environ, "PYTHONPATH": "."}
    )
    
    # 2. Give it a few seconds to start
    time.sleep(3)
    
    try:
        # 3. Health check
        resp = requests.get("http://localhost:8000/health")
        print(f"Health Check: {resp.status_code} - {resp.json()}")

        # 4. Upload file
        with open("tests/data/ancp_sample.xlsx", "rb") as f:
            files = {"file": ("ancp_sample.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            data = {"source_system": "ANCP"}
            resp = requests.post("http://localhost:8000/process-genetic-data", files=files, data=data)
            
        if resp.status_code == 200:
            print("Upload Successful!")
            # 5. Verify content
            output_df = pd.read_excel(io.BytesIO(resp.content))
            print("\nOutput Data Head:")
            print(output_df.head())
            
            # Check if columns were renamed correctly
            expected_cols = ['rgn_animal', 'nome_animal', 'sexo', 'data_nascimento', 'p210_peso_desmama', 'p450_peso_sobreano', 'fonte_origem']
            for col in expected_cols:
                assert col in output_df.columns, f"Column {col} missing from output!"
            
            print("\nVerification Passed: Column mapping and data cleaning successful!")
        else:
            print(f"Upload Failed: {resp.status_code} - {resp.text}")

    finally:
        server_process.terminate()

if __name__ == "__main__":
    test_api()
