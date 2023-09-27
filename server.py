from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
# start command
# uvicorn server:app --reload
# Swagger: {Base URL}/docs

class UserInfo(BaseModel):
    student_id: str
    password: str

class SmartCampusToken(BaseModel):
    token: str


@app.post("/smart-campus/crawling")
async def smart_campus_controller(smart_campus_token: SmartCampusToken):
    from smart_campus import smart_campus_crawling
    result = smart_campus_crawling(smart_campus_token.token)
    return result

@app.post("/smart-campus/auth")
async def auth_controller(user_info: UserInfo):
    from auth_token import get_auth_token
    result = get_auth_token(user_info)
    return result
    
@app.get("/fun-system")
async def fun_system_controller():
    from fun_system import fun_system_crawling
    result = fun_system_crawling()
    return result

@app.get("/notice/ssu-catch")
async def ssu_catch_controller():
    from ssu_catch import ssu_catch_crawling
    result = ssu_catch_crawling()
    return result

@app.get("/notice/computer")
async def computer_department_controller():
    from computer import computer_department_crawling
    result = computer_department_crawling()
    return result

