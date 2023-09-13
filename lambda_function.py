import json

def lambda_handler(event, context):
    body = json.loads(event['body'])
    function_name = body['function']
    value = body['value']

    match function_name:
        case "smart_campus":
            # 스마트 캠퍼스 크롤링 모듈 import 문을 작성해주세요.
            # 스마트 캠퍼스 크롤링 로직 함수를 호출해주세요.
            pass
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
