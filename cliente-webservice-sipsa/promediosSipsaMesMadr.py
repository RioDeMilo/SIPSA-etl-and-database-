from etl import etl

wsdl = 'https://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService?WSDL'
serviceMethod = "promediosSipsaMesMadr"
arg0 = None
fields = [
    'artiId',
    'artiNombre',
    'enviado',
    'fechaCreacion',
    'fechaMesIni',
    'fuenId',
    'fuenNombre',
    'futiId',
    'maximoKg',
    'minimoKg',
    'promedioKg',
    'tmpMayoMesId'
]
pathFile = str("E:/Camilo De Los Rios/1Projects/SIPSA/ETL PYTHON LIBRARY/cliente-webservice-sipsa/data/promediosSipsaMesMadr.json")
etl.controller(wsdl, serviceMethod, arg0, fields, pathFile)
