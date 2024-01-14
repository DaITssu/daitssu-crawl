from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, CHAR, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()
default_date = datetime.datetime(9999, 12, 31, 23, 59, 59)

default_start_date = datetime.datetime(2023, 1, 1, 00, 00, 00)
current_time = datetime.datetime.now()
class Course(Base):
    __tablename__ = 'course'
    __table_args__ = {"schema": "daitssu"}
    id = Column(Integer, primary_key=True)
    course_code = Column(CHAR(32), nullable=False)
    name = Column(CHAR(64))
    term = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    videos = relationship("Video", back_populates="course")
    assignments = relationship("Assignment", back_populates="course")
    user_course_relations = relationship("UserCourseRelation", back_populates="course")
    calendars = relationship("Calendar", back_populates="course")

class Video(Base):
    __tablename__ = 'video'
    __table_args__ = {"schema": "daitssu"}
    id = Column(Integer, primary_key=True)
    name = Column(CHAR(256))
    course_id = Column(Integer, ForeignKey('daitssu.course.id'))
    due_at = Column(DateTime, default=default_date)
    start_at = Column(DateTime, default=default_date)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    course = relationship("Course", back_populates="videos")

class Assignment(Base):
    __tablename__ = 'assignment'
    __table_args__ = {"schema": "daitssu"}
    id = Column(Integer, primary_key=True)
    name = Column(CHAR(256))
    course_id = Column(Integer, ForeignKey('daitssu.course.id'))
    due_at = Column(DateTime, default=default_date)
    start_at = Column(DateTime, default=default_date)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    course = relationship("Course", back_populates="assignments")

class UserCourseRelation(Base):
    __tablename__ = 'user_course_relation'
    __table_args__ = {"schema": "daitssu"}
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    course_id = Column(Integer, ForeignKey('daitssu.course.id'))
    register_status = Column(CHAR(20))
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    course = relationship("Course", back_populates="user_course_relations")

class Calendar(Base):
    __tablename__ = 'calendar'
    __table_args__ = {"schema": "daitssu"}
    id = Column(Integer, primary_key=True)
    type = Column(CHAR(32))
    course_id = Column(Integer, ForeignKey('daitssu.course.id'))
    due_at = Column(DateTime, default=default_date)
    name = Column(CHAR(256))
    is_completed = Column(Boolean)
    user_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    course = relationship("Course", back_populates="calendars")
