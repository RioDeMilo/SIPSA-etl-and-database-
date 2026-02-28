import zeep
from zeep.helpers import serialize_object

def extract_soap(wsdl: str, service_method: str, **kwargs) -> list:
    """
    Dynamically calls the SOAP service method.
    """
    
# wsdl is the vbariable that we get from the controller call
    try:
        client = zeep.Client(wsdl=wsdl)
        # getattr finds the method by name (e.g., 'promediosSipsaCiudad')
        method = getattr(client.service, service_method, None)
        
        if not method:
            raise ValueError(f"Method '{service_method}' not found in WSDL.")

        # Pass any extra arguments (like arg0) directly to the service
        response = method(**kwargs)
        # the serialize object is a zeep component to transform froma 
        # zeep object to a normal python list
        raw_data = serialize_object(response)

        # Ensure always list
        if isinstance(raw_data, list):
            return raw_data

        return [raw_data]

    except zeep.exceptions.Fault as e:
        print(f"SOAP Fault: {e}")
        return []

#if I don't add the return in every function it will noet
# give any value after finisihng the function call

