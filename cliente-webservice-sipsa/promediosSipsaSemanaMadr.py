from etl import etl

wsdl = 'https://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService?WSDL'
serviceMethod = "promediosSipsaSemanaMadr"
arg0 = None
fields = [
    'artiId',
    'artiNombre',
    'fechaIni',
    'fuenId',
    'fuenNombre',
    'futiId',
    'maximoKg',
    'minimoKg',
    'promedioKg',
]
pathFile = str("E:/Camilo De Los Rios/1Projects/SIPSA/cliente-webservice-sipsa/data/promediosSipsaSemanaMadr.json")
etl.controller(wsdl, serviceMethod, arg0, fields, pathFile)
