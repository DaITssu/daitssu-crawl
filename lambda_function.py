import json
from model.req_models import *

def lambda_handler(event, context):
    body = json.loads(event['body'])
    function_name = body['function']

    match function_name:
        case "smart-campus_auth":
            user_info = body['value']
            result = auth_controller(user_info)
        case "smart_campus":
            smart_campus_req = body['value']
            result = smart_campus_controller(smart_campus_req)
        case "fun_system":
            result = fun_system_controller()
        case "ssu_catch":
            result = ssu_catch_controller()
        case "notice_computer":
            result = computer_department_controller()
        case _:
            result = "Function not found"

    return {
        'statusCode': 200,
        'body': result
    }

def auth_controller(user_info: UserInfo):
    """
    현재 정상 이용 가능합니다.
    """
    from smart_campus.auth_token import get_auth_token
    result = get_auth_token(user_info)
    return result

def smart_campus_controller(smart_campus_req: SmartCampusReq):
    """
    현재 정상 이용 가능합니다.
    """
    from smart_campus.smart_campus import smart_campus_crawling
    result = smart_campus_crawling(smart_campus_req.token, smart_campus_req.student_id)
    return result

def fun_system_controller():
    """
    현재 정상 이용 가능합니다.
    """
    from fun_system.fun_system import fun_system_crawling
    result = fun_system_crawling()
    return result

def ssu_catch_controller():
    """
    현재 정상 이용 가능합니다.
    """
    from notice.ssu_catch import ssu_catch_crawling
    result = ssu_catch_crawling()
    return result

def computer_department_controller():
    """
    현재 정상 이용 가능합니다.
    """
    from notice.computer import computer_department_crawling
    result = computer_department_crawling()
    return result
