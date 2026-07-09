import os
import sys
from etl import etl 
from etl import soap_client
from etl import transformers
from etl import load


wsdl = 'https://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService?WSDL'
service_method = "promediosSipsaCiudad"

fields = [
    "ciudad", "codProducto", "enviado", "fechaCaptura", 
    "fechaCreacion", "precioPromedio", "producto", "regId"
]

transformation = transformers.promedio_ciudad

db_table_name = "precios"
index = False
etl.controller(wsdl, service_method, fields, transformation, db_table_name, index)
