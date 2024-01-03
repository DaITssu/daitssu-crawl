from fastapi import FastAPI, HTTPException
import uvicorn
from model.req_models import *

app = FastAPI (
    title="Daitssu Crawl Server",
    description="다잇슈 크롤링 서버 api 문서입니다.",
    version="1.0.0"
    )

@app.post("/smart-campus/crawling")
async def smart_campus_controller(smart_campus_req: SmartCampusReq):
    """
    현재 정상 이용 가능합니다.
    """
    from smart_campus.smart_campus import smart_campus_crawling
    try:
        result = smart_campus_crawling(smart_campus_req.token, smart_campus_req.student_id)
    except:
        raise HTTPException(status_code=400, detail="에러가 발생 했습니다.")
    return result

@app.post("/smart-campus/auth")
async def auth_controller(user_info: UserInfo):
    """
    현재 정상 이용 가능합니다.
    """
    from smart_campus.auth_token import get_auth_token
    result = get_auth_token(user_info)
    return result
    
@app.get("/fun-system")
async def fun_system_controller():
    """
    현재 정상 이용 가능합니다.
    """
    from fun_system.fun_system import fun_system_crawling
    result = fun_system_crawling()
    return result

@app.get("/notice/ssu-catch")
async def ssu_catch_controller():
    """
    현재 정상 이용 가능합니다.
    """
    from notice.ssu_catch import ssu_catch_crawling
    result = ssu_catch_crawling()
    return result

@app.get("/notice/computer")
async def computer_department_controller():
    """
    현재 정상 이용 가능합니다.
    """
    from notice.computer import computer_department_crawling
    result = computer_department_crawling()
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)