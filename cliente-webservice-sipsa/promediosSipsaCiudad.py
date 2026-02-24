import os
from etl import etl

wsdl = 'https://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService?WSDL'
serviceMethod = "promediosSipsaCiudad"
arg0 = None
fields = [
    "ciudad",
    "codProducto",
    "enviado",
    "fechaCaptura",
    "fechaCreacion",
    "precioPromedio",
    "producto",
    "regId",
]
# --- MODIFIED LINE ---
# Changed the Windows path to a relative, cross-platform friendly path
pathFile = os.path.join("data", "promediosSipsaCiudad.csv")
# You could also use the simple string: pathFile = "data/promediosSipsaCiudad.json"
# But os.path.join is best practice.
# ---------------------pathFile = str("E:/Camilo De Los Rios/1Projects/SIPSA/cliente-webservice-sipsa/data/promediosSipsaCiudad.json")
etl.controller(wsdl, serviceMethod, arg0, fields, pathFile)
