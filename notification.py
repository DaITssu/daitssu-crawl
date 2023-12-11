from sqlalchemy import Column, Integer, CHAR, ARRAY, DateTime, JSON
from sqlalchemy.orm import declarative_base


# unit class for notice.notice
class Notification(declarative_base()):
    __tablename__ = "notice"
    __table_args__ = {"schema": "daitssu"}
    id = Column(Integer, primary_key=True)
    title = Column(CHAR(1024))
    department_id = Column(Integer)
    content = Column(CHAR(2048))
    category = Column(CHAR(32))
    image_url = Column(JSON)
    file_url = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    views = Column(Integer)
