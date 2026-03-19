import pandas as pd
import os

def create_sample_ancp():
    data = {
        'RGN': ['123', '456', '789'],
        'NOME': ['Boi 1', 'Boi 2', 'Vaca 1'],
        'SEXO': ['M', 'M', 'F'],
        'DT_NASC': ['2022-01-01', '2022-02-15', '2021-12-10'],
        'PESO_DESM': [210.5, 195.0, 180.2],
        'PESO_SOBRE': [450.0, 430.5, 410.0],
        'IRRELEVANT': ['foo', 'bar', 'baz']
    }
    df = pd.DataFrame(data)
    os.makedirs('tests/data', exist_ok=True)
    df.to_excel('tests/data/ancp_sample.xlsx', index=False)
    print("Sample ANCP file created at tests/data/ancp_sample.xlsx")

if __name__ == "__main__":
    create_sample_ancp()
