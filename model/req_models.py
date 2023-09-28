from pydantic import BaseModel

class UserInfo(BaseModel):
    student_id: str
    password: str

class SmartCampusToken(BaseModel):
    token: str