from pydantic import BaseModel

class UserInfo(BaseModel):
    student_id: str
    password: str

class SmartCampusReq(BaseModel):
    token: str
    student_id: str