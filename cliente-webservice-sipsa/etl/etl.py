from etl import soap_client
from etl import transformers
from etl import load

# for the transformers I need to create a string 
#to call specific functions depending on the 

def controller(wsdl: str, service_method: str, fields: list, **kwargs):
    print(f">>> Connecting to: {service_method}")
    
    

    # 1. Extract
    
    raw_data = soap_client.extract_soap(wsdl, service_method, **kwargs)
    
    if not raw_data:
        print(">>> No data returned from service.")
        return

    print(f">>> Retrieved {len(raw_data)} records.")

    # 2. Transform
    clean_data = transformers.promedio_ciudad(raw_data, fields)
    # using pandas to upload to the sqlite3 database
    load.update_database(clean_data)

    print(f">>> Done! database uploaded")



