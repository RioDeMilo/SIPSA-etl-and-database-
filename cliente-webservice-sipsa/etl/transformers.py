import numpy
import pandas as pd
def promedio_ciudad(raw_data: list, fields: list) -> pd.DataFrame:
    """
    Filters data to include only requested fields and converts values to strings.
    """
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


