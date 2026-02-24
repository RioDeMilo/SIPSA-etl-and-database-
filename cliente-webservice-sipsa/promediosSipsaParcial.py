from etl import etl

wsdl = 'https://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService?WSDL'
serviceMethod = "promediosSipsaParcial"
arg0 = None
fields = [
    'artiNombre',
    'deptNombre',
    'enmaFecha',
    'fuenId',
    'fuenNombre',
    'futiId',
    'grupNombre',
    'idArtiSemana',
    'maximoKg',
    'minimoKg',
    'muniId',
    'muniNombre',
    'promedioKg'
]
pathFile = str("E:/Camilo De Los Rios/1Projects/cliente-webservice-sipsa/data/promediosSipsaParcial.json")
etl.controller(wsdl, serviceMethod, arg0, fields, pathFile)
