import os
import sys
import etl 
import soap_client
import transformers
import load


wsdl = 'http://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService?WSDL'
service_method = "promediosSipsaCiudad"

fields = [
    "ciudad", "codProducto", "enviado", "fechaCaptura", 
    "fechaCreacion", "precioPromedio", "producto", "regId"
]

transformation = transformers.promedio_ciudad_ciudades

db_table_name = "ciudades"
index = False
etl.controller(wsdl,service_method, fields, transformation, db_table_name, index)
