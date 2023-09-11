import requests
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import dev_db

db_url = sqlalchemy.engine.URL.create(  # db연결 url 생성
        drivername="postgresql",
        username=dev_db.dev_user_name,
        password=dev_db.dev_db_pw,
        host=dev_db.dev_host,
        database=dev_db.dev_db_name
    )

engine = create_engine(db_url)  # db 연결
session_maker = sessionmaker()
session_maker.configure(bind=engine)


Base = declarative_base()

class SmartCampusData(Base): #과목별 과목 코드와 과목의 이름, 색상 코드를 저장할 부분
    __tablename__ = 'smart_campus_data'

    course_id = Column(Integer, primary_key=True)
    course_title = Column(String(255))
    color_code = Column(String(10))

class AttendanceRecord(Base): #과목별 과목 출결상태를 저장할 부분으로 과목 코드에 맞는 과목에 종속됨
    __tablename__ = 'attendance_record'

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('smart_campus_data.course_id'))
    attendance_id = Column(Integer)
    attendance_status = Column(String(50))

    course = relationship('SmartCampusData', back_populates='attendance_records')

class DateRecord(Base): #과목별 강의 기한 및 과제 기한을 저장할 부분으로 과목 코드에 맞는 과목에 종속됨
    __tablename__ = 'date_record'

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('smart_campus_data.course_id'))
    module_item_id = Column(Integer, unique=True)
    module_item_title = Column(String(255))
    unlock_at = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True)
    late_at = Column(DateTime, nullable=True)
    video_url = Column(String)

    course = relationship('SmartCampusData', back_populates='date_records')



class SmartCampus:
    def __init__(self, session):
        self.session = session

    def get_subject(self, token): #토큰을 보냄으로 학기에 현재 수강중인 과목의 정보를 받아옴
        url = "https://canvas.ssu.ac.kr/learningx/api/v1/learn_activities/courses?term_ids[]=31"
        headers = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)
        cnt = 1
        if response.status_code == 200:
            data = response.json()
            for module in data:
                course_title = module["name"]
                course_id = module["id"]
                color_code = self.color_list[cnt - 1] if cnt < 11 else self.over_color
                self.save_subject_data(course_id, course_title, color_code)
                cnt += 1

    #받아온 과목의 코드, 과목 이름, 지정된 색상 코드를 저장함
    def save_subject_data(self, course_id, course_title, color_code):
        new_subject = SmartCampusData(course_id=course_id, course_title=course_title, color_code=color_code)
        self.session.add(new_subject)
        self.session.commit()
    
    #과목 코드와 토큰을 받음으로 해당 과목의 출결 상태를 저장함
    def get_attendance_data(self, token, subject_num):
        subject = subject_num
        url = f"https://canvas.ssu.ac.kr/learningx/api/v1/courses/{subject}/attendance_items/summary?only_use_attendance=true"
        headers = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            attendance_statuses = data['attendance_summaries']
            for item_id, attendance in attendance_statuses.items():
                attendance_status = attendance['attendance_status']
                existing_data = self.session.query(AttendanceRecord).filter_by(course_id=subject_num, attendance_status=attendance_status, attendance_id=item_id).first()
                #이미 동일한 item_id로 입력된 출결 상태가 존재하면 넘어가고 아니라면 새로이 추가된 출결 상태라 판단하여 저장함
                if not existing_data:
                    self.save_attendance_data(subject_num, item_id, attendance_status)
        else:
            print("요청에 실패했습니다. 응답 코드:", response.status_code)

    #출결상태 저장
    def save_attendance_data(self, course_id, item_id, attendance_status):
        course = self.session.query(SmartCampusData).filter_by(course_id=course_id).first()
        if course is not None:
            new_attendance = AttendanceRecord(course=course, attendance_id=item_id, attendance_status=attendance_status)
            self.session.add(new_attendance)
            self.session.commit()
        else:
             print("오류가 발생했습니다.")

    #토큰과 과목 코드를 받음으로 해당 과목의 강의의 출결 인정 기간 및 과목의 제출 인정 기간 등의 정보를 받아옴
    def get_date(self, token, subject_num):

        subject = subject_num
        url = f"https://canvas.ssu.ac.kr/learningx/api/v1/courses/{subject}/modules?include_detail=true"
        headers = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for module in data:
                module_items = module["module_items"]
                for item in module_items:
                    module_item_id = item["module_item_id"]
                    title = item["title"]
                    if item["content_type"] == "attendance_item":
                        #받아온 데이터의 종류가 강의일 경우 강의를 시청할 수 있는 url과 함께 시작 및 종료 시간을 입력 받아 저장함
                        unlock_at = datetime.strptime(item["content_data"]["unlock_at"], "%Y-%m-%dT%H:%M:%SZ") if item["content_data"]["unlock_at"] else None
                        due_at = datetime.strptime(item["content_data"]["due_at"], "%Y-%m-%dT%H:%M:%SZ") if item["content_data"]["due_at"] else None
                        late_at = datetime.strptime(item["content_data"]["late_at"], "%Y-%m-%dT%H:%M:%SZ") if item["content_data"]["late_at"] else None
                        video_url = item["content_data"]["item_content_data"]["view_url"]
                        self.save_date_data(subject_num, title, module_item_id, unlock_at, due_at, late_at, video_url)
                    elif item["content_type"] == "assignment":
                        #데이터의 형식이 과제일 경우 시작일 및 제출 마감일만 저장함
                        unlock_at = datetime.strptime(item["content_data"]["unlock_at"], "%Y-%m-%dT%H:%M:%SZ") if item["content_data"]["unlock_at"] else None
                        due_at = datetime.strptime(item["content_data"]["due_at"], "%Y-%m-%dT%H:%M:%SZ") if item["content_data"]["due_at"] else None
                        self.save_date_data(subject_num, title, module_item_id, unlock_at, due_at, None, None)

    #받아온 강의 및 과제의 정보를 저장하는 함수
    def save_date_data(self, course_id, title, module_item_id, unlock_at, due_at, late_at, video_url):
        course = self.session.query(SmartCampusData).filter_by(course_id=course_id).first()
        if course is not None:
            new_date = DateRecord(course=course, module_item_title=title, module_item_id=module_item_id,
                                  unlock_at=unlock_at, due_at=due_at, late_at=late_at, video_url=video_url)
            self.session.add(new_date)
            self.session.commit()
        else:
             print("오류가 발생했습니다.")

