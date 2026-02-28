from pathlib import Path
import sqlite3
import numpy
import pandas as pd

def update_database(clean_data : pd.DataFrame):
    # DictWriter automatically handles header mapping and commas in data
    #clean_data.to_csv(path_file,index=False,mode='a',header=False)  
    # now we also insert here the SQL database upload

    # 1. Corregir la ruta: Subir un nivel desde la carpeta del script para encontrar 'database'
    # Esto asegura que busque en /home/milo/sipsa/database/sipsa.db
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    correct_path = BASE_DIR / "database" / "sipsa.db"

    try:
        # 2. Definir 'conn' ANTES de usarla
        conn = sqlite3.connect(str(correct_path))
        
        print(f"Intentando guardar en: {correct_path}")
        
        # 3. Ejecutar el guardado
        clean_data.to_sql("cities", conn, if_exists="delete_rows", index=False)
        conn.close()
        print(">>> Guardado exitoso en base de datos.")
# the to_sql is a pandas function
#
    except Exception as e:
        print(f"Error al guardar: {e}")


