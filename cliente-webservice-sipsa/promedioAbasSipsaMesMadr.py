from etl import etl

wsdl = 'https://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService?WSDL'
serviceMethod = "promedioAbasSipsaMesMadr"
arg0 = None
fields = [
    "artiId",
    "artiNombre",
    "cantidadTon",
    "fechaMesIni",
    "fuenId",
    "fuenNombre",
    "futiId",
]
pathFile = str("E:/Camilo De Los Rios/1Projects/SIPSA/cliente-webservice-sipsa/data/promedioAbasSipsaMesMadr.json")
etl.controller(wsdl, serviceMethod, arg0, fields, pathFile)
