import numpy
import pandas as pd
def promedio_ciudad_ciudades(raw_data: list, fields: list) -> pd.DataFrame:
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
    transformed.rename(columns={'ciudad': 'ciudad_nombre'}, inplace=True)



    print(pd.DataFrame(raw_data).columns)
    return transformed
def promedio_ciudad_productos(raw_data: list, fields: list) -> pd.DataFrame:
    """
    Filters data to include only requested fields and converts values to strings.
    """
    #the serialize i from zeep to convert the object to a ypthon object
    transformed = pd.DataFrame(raw_data).filter(fields)
    # creating a dictionary to change the values of the cities
    ciudades_dictonario = {'BOGOTÁ, D.C.': 'Bogotá', 'SAN JOSÉ DE CÚCUTA': 'Cúcuta','CARTAGENA DE INDIAS' : 'Cartagena'}
    transformed['ciudad'] = transformed['ciudad'].replace(ciudades_dictonario)
    transformed['ciudad'] = transformed['ciudad'].str.capitalize()
 
    transformed = transformed.drop_duplicates(subset=["producto"])
#removes the columns but keeps everything as a dataframe
    transformed = transformed.drop(["enviado","fechaCaptura","fechaCreacion", "precioPromedio","ciudad","regId"],axis=1)
    transformed.rename(columns={'producto': 'producto_nombre'}, inplace=True)
    transformed.rename(columns={'codProducto': 'producto_id'}, inplace=True)
    transformed.set_index('producto_id', inplace=True)
    transformed.index = transformed.index.astype(int)

# now the index transformation we need to conver the number to integer for python
#to avoid problems with other types or data that sql has problems with
    print(pd.DataFrame(raw_data).columns)
    return transformed
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
    transformed.rename(columns={'codProducto': 'producto_id'}, inplace=True)
    transformed.rename(columns={'regId': 'precio_id'}, inplace=True)
    transformed.rename(columns={'ciudad': 'ciudad_id'},inplace=True)
    transformed.rename(columns={'precioPromedio': 'precio_kilo'}, inplace=True)
    transformed.rename(columns={'fechaCaptura': 'precio_fecha'}, inplace=True)
    transformed.rename(columns={'fechaCreacion': 'precio_fecha_creacion'}, inplace=True)
    
   

    print(pd.DataFrame(raw_data).columns)
    return transformed
#


