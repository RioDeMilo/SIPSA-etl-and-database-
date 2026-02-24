import csv
import json
import zeep
import xmltodict
import os
import numpy
import pandas as pd
from zeep.helpers import serialize_object
import sqlite3
from pathlib import Path
# This serialize_object helps pass the xzeep objcets to dictionary like objects in ptho 
#nso pandas can work with them

def extract_data(wsdl: str, service_method: str, **kwargs) -> list:
    """
    Dynamically calls the SOAP service method.
    """
    try:
        client = zeep.Client(wsdl=wsdl)
        # getattr finds the method by name (e.g., 'promediosSipsaCiudad')
        method = getattr(client.service, service_method, None)
        
        if not method:
            raise ValueError(f"Method '{service_method}' not found in WSDL.")

        # Pass any extra arguments (like arg0) directly to the service
        response = method(**kwargs)
        
        # Ensure we always return a list
        if response is None:
            return []
        return list(response) if isinstance(response, list) else [response]

    except zeep.exceptions.Fault as e:
        print(f"SOAP Fault: {e}")
        return []

def transform_data(raw_data: list, fields: list) -> pd.DataFrame:
    """
    Filters data to include only requested fields and converts values to strings.
    """
    raw_data = serialize_object(raw_data)
    #the serialize i from zeep to convert the object to a ypthon object
    transformed = pd.DataFrame(raw_data).filter(fields)
    # creating a dictionary to change the values of the cities
    ciudades_dictonario = {'BOGOTÁ, D.C.': 'Bogotá', 'SAN JOSÉ DE CÚCUTA': 'Cúcuta','CARTAGENA DE INDIAS' : 'Cartagena'}
    transformed['ciudad'] = transformed['ciudad'].replace(ciudades_dictonario)
    transformed['ciudad'] = transformed['ciudad'].str.capitalize()
 
    transformed = transformed.drop_duplicates(subset=["ciudad"])
#removes the columns but keeps everything as a dataframe
    transformed = transformed.drop(["codProducto","enviado","fechaCaptura","fechaCreacion", "precioPromedio","producto","regId"],axis=1)
    transformed.rename(columns={'ciudad': 'city_name'}, inplace=True)



    print(pd.DataFrame(raw_data).columns)
    return transformed
#def save_json(path_file: str, data: list):
#    with open(path_file, "w", encoding='utf-8') as f:
#        json.dump(data, f, indent=4, ensure_ascii=False)

def save_csv(path_file : str, clean_data : pd.DataFrame):
    # DictWriter automatically handles header mapping and commas in data
    clean_data.to_csv(path_file,index=False,mode='a',header=False)  
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

    except Exception as e:
        print(f"Error al guardar: {e}")


# mode is to append and header to avoid pasting the header everytime
#def save_xml(path_file: str, data: list):
    # Wraps data in a root element to ensure valid XML
#    wrapped_data = {"Root": {"Item": data}}
#    with open(path_file, "w", encoding='utf-8') as f:
#        xmltodict.unparse(wrapped_data, output=f, pretty=True)

def controller(wsdl: str, service_method: str, fields: list, path_file: str, **kwargs):
    print(f">>> Connecting to: {service_method}")
    
    # 1. Extract
    raw_data = extract_data(wsdl, service_method, **kwargs)
    
    if not raw_data:
        print(">>> No data returned from service.")
        return

    print(f">>> Retrieved {len(raw_data)} records.")
    
    # 2. Transform
    clean_data = transform_data(raw_data, fields)
    
    # 3. Load (Save)
    ext = os.path.splitext(path_file)[1].lower()
    
    print(f">>> Saving to {ext}...")
    #if ext == '.json':
    #    save_json(path_file, clean_data)
    if ext == '.csv':
        save_csv(path_file,clean_data)
    #elif ext == '.xml': 
    #    save_xml(path_file, clean_data)
    #else:
    #    print(f"Error: Unsupported file extension '{ext}'")
        
    print(f">>> Done! File saved at: {path_file}")
