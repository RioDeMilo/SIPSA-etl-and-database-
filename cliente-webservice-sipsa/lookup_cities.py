import os
import sys

# 1. The Import
# Since main.py is outside the folder, we import the file from the folder.
from etl import etl_lookup_tables 

wsdl = 'https://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService?WSDL'
service_method = "promediosSipsaCiudad"

fields = [
    "ciudad", "codProducto", "enviado", "fechaCaptura", 
    "fechaCreacion", "precioPromedio", "producto", "regId"
]

# 2. Path Setup
# We need to make sure the 'data' folder is created in the root (general folder)
output_dir = "data"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

path_file = os.path.join(output_dir, "lookup_cities.csv")

# 3. Execution
# Remember: do not pass 'arg0' if the method doesn't need it
etl_lookup_tables.controller(wsdl, service_method, fields, path_file)
