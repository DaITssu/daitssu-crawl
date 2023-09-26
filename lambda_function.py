import json

def lambda_handler(event, context):
    body = json.loads(event['body'])
    function_name = body['function']
    value = body['value']

    match function_name:
        case "smart_campus":
            from smart_campus import smart_campus_crawling
            result = smart_campus_crawling(value)
        case "fun_system":
            from fun_system import fun_system_crawling
            result = fun_system_crawling(value)
        case "ssu_catch":
            from ssu_catch import ssu_catch_crawling
            result = ssu_catch_crawling(value)
        case "auth_token":
            from auth_token import get_auth_token
            result = get_auth_token(value)
        case _:
            result = "Function not found"

    return {
        'statusCode': 200,
        'body': result
    }
