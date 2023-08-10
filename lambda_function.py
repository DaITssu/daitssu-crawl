from smart_campus import smart_campus_crawling
from departments import departments_crawling
from fun_system import fus_system_crawling
from ssu_catch import ssu_catch_crawling

def lambda_handler(event, context):
    function_name = event['function']
    value = event['value']
    
    if function_name == 'smart_campus':
        result = smart_campus_crawling(value)
    elif function_name == 'departments':
        result = departments_crawling(value)
    elif function_name == 'fus_system':
        result = fus_system_crawling(value)
    elif function_name == 'ssu_catch':
        result = ssu_catch_crawling(value)
    else:
        result = "Function not found"
    
    return {
        'statusCode': 200,
        'body': result
    }