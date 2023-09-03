import json

from smart_campus import smart_campus
from departments import departments_crawling
from fun_system import fus_system_crawling
from ssu_catch import ssu_catch_crawling
from auth_token import get_auth_token

def lambda_handler(event, context):
    body = json.loads(event['body'])
    function_name = body['function']
    value = body['value']
    
    if function_name == 'smart_campus':
        result = smart_campus(value)
    elif function_name == 'departments':
        result = departments_crawling(value)
    elif function_name == 'fus_system':
        result = fus_system_crawling(value)
    elif function_name == 'ssu_catch':
        result = ssu_catch_crawling(value)
    elif function_name == 'auth_token':
        result = get_auth_token(value)
    else:
        result = "Function not found"
    
    return {
        'statusCode': 200,
        'body': result
    }
