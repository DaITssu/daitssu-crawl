from fastapi import FastAPI
from model.req_models import *

app = FastAPI (
    title="Daitssu Crawl Server",
    description="다잇슈 크롤링 서버 api 문서입니다.",
    version="1.0.0"
    )


@app.post("/smart-campus/crawling")
async def smart_campus_controller(smart_campus_token: SmartCampusToken):
    """
    현재 디버깅이 필요합니다.
    """
    from smart_campus import smart_campus_crawling
    result = smart_campus_crawling(smart_campus_token.token)
    return result

@app.post("/smart-campus/auth")
async def auth_controller(user_info: UserInfo):
    """
    현재 정상 이용 가능합니다.
    """
    from auth_token import get_auth_token
    result = get_auth_token(user_info)
    return result
    
@app.get("/fun-system")
async def fun_system_controller():
    """
    S3 설정을 마친 뒤 정상 이용 가능합니다.
    """
    from fun_system import fun_system_crawling
    result = fun_system_crawling()
    return result

@app.get("/notice/ssu-catch")
async def ssu_catch_controller():
    """
    S3 설정을 마친 뒤 정상 이용 가능합니다.
    """
    from ssu_catch import ssu_catch_crawling
    result = ssu_catch_crawling()
    return result

@app.get("/notice/computer")
async def computer_department_controller():
    """
    현재 정상 이용 가능합니다.
    """
    from computer import computer_department_crawling
    result = computer_department_crawling()
    return result

