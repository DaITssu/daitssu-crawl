import requests
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, CHAR, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func
import datetime
import dev_db

from fastapi.responses import JSONResponse

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


class Course(Base):
    __tablename__ = 'course'
    course_id = id = Column(Integer, nullable=False)
    id = Column(Integer, primary_key=True)
    name = Column(CHAR(32), nullable=False)
    term = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class Video(Base):
    __tablename__ = 'video'

    id = Column(Integer, primary_key=True)
    name = Column(CHAR(256), nullable=False)
    course_id = Column(Integer, ForeignKey('course.course_id'), nullable=False)
    due_at = Column(DateTime, nullable=False)
    start_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class Assignment(Base):
    __tablename__ = 'assignment'

    id = Column(Integer, primary_key=True)
    name = Column(CHAR(256), nullable=False)
    course_id = Column(Integer, ForeignKey('course.course_id'), nullable=False)
    due_at = Column(DateTime, nullable=False)
    start_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class UserCourseRelation(Base):
    __tablename__ = 'user_course_relation'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, ForeignKey('course.course_id'), nullable=False)
    register_status = Column(CHAR(20), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    color = name = Column(CHAR(32), nullable=False)


class Calendar(Base):
    __tablename__ = 'calendar'

    id = Column(Integer, primary_key=True)
    type = Column(CHAR(32), nullable=False)
    course = Column(CHAR(32), nullable=False)
    due_at = Column(DateTime, nullable=False)
    name = Column(CHAR(32), nullable=False)
    isComplete = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

class SmartCampus:
    def __init__(self, session):
        self.session = session

    color_list = ['FF8DC4', 'FF7171', 'FF9E68', 'FFD057', 'B7E532', '35CC7B', '73E4DE', '6197FF', 'B69BE3', 'A48172']
    over_color = 'BDBDBD'

    def course(self, token, user_id):  # 토큰을 보냄으로 학기에 현재 수강중인 과목의 정보를 받아옴
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
                self.save_subject_data(course_id, course_title, color_code, user_id)
                cnt += 1
            self.session.commit()

    # 받아온 과목의 코드, 과목 이름, 지정된 색상 코드를 저장함
    def save_course_data(self, course_id, course_title, color_code, user_id):
        current_time = datetime.utcnow()
        existing_course = self.session.query(Course).filter_by(course_id=course_id).first()
        existing_course_of_user = self.session.query(UserCourseRelation).filter_by(user_id= user_id,course_id=course_id).first()
        if existing_course_of_user is None:
            put_course = UserCourseRelation(user_id=user_id, course_id=course_id, register_status="수강중",
                                            created_at=current_time, updated_ap=current_time)
            self.session.add(put_course)
        if existing_course is None:
            # 존재하지 않는 경우에만 추가s
            new_subject = Course(course_id=course_id, term=2, name=course_title, created_at=current_time,
                                 updated_at=current_time)
            self.session.add(new_subject)

    # 과목 코드와 토큰을 받음으로 해당 과목의 출결 상태를 저장함
    def get_calander_data(self, token, subject_num):
        current_time = datetime.utcnow()
        subject = subject_num
        url = f"https://canvas.ssu.ac.kr/learningx/api/v1/courses/{subject}/attendance_items?include_detail=true"
        headers = {"Authorization": "Bearer " + token}

        summary_url = "https://canvas.ssu.ac.kr/learningx/api/v1/courses/24920/attendance_items/summary?only_use_attendance=true"
        response_summary = requests.get(summary_url, headers=headers)
        if response_summary.status_code == 200:
            summary_data = response_summary.json().get("attendance_summaries", {})

        # API 요청 보내고 데이터 파싱
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            attendance_items = data.get("attendance_items", [])
            for item in attendance_items:
                item_content_data = item.get("item_content_data", {})
                placement = item_content_data.get("placement")
                schedule_time = item_content_data.get("schedule_time")
                item_id_data = item.get("item_id")
                status = False
                if placement:
                    # 중복된 "due_at" 값이 있는지 확인하고 중복된 경우 스킵
                    if not self.session.query(Calendar).filter_by(due_at=schedule_time).first():
                        for item_id, attendance_summary in summary_data.items():
                            if item_id==item_id_data:
                                if attendance_summary["attendance_status"]=="attendance":
                                    status=True
                                    break
                        course_name = self.session.query(Course).filter_by(course_id=subject_num).first()
                        new_calendar_item = Calendar(type="대면수업",
                            course=course_name.name,
                            due_at=schedule_time,
                            is_completed=status,
                            name=item.get("title"),
                            created_at=current_time,
                            updated_at=current_time
                        )
                        course = self.session.query(Course).filter_by(course_id=subject_num).first()
                        course.updated_at = current_time
                        self.session.add(new_calendar_item)

            self.session.commit()
            self.session.close()
        else:
            print("API 요청에 실패했습니다. 응답 코드:", response.status_code)


    # 토큰과 과목 코드를 받음으로 해당 과목의 강의의 출결 인정 기간 및 과목의 제출 인정 기간 등의 정보를 받아옴
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
                        unlock_at = datetime.strptime(item["content_data"]["unlock_at"], "%Y-%m-%dT%H:%M:%SZ") if \
                            item["content_data"]["unlock_at"] else None
                        due_at = datetime.strptime(item["content_data"]["due_at"], "%Y-%m-%dT%H:%M:%SZ") if \
                            item["content_data"]["due_at"] else None
                        create_at = datetime.strptime(item["content_data"]["created_at"], "%Y-%m-%dT%H:%M:%SZ") if \
                            item["content_data"]["late_at"] else None
                        updated_at = datetime.strptime(item["content_data"]["updated_at"], "%Y-%m-%dT%H:%M:%SZ") if \
                            item["content_data"]["late_at"] else None
                        video_url = item["content_data"]["item_content_data"]["view_url"]
                        self.save_video_data(subject_num, title, create_at, unlock_at, due_at, updated_at, video_url)
                    elif item["content_type"] == "assignment":
                        unlock_at = datetime.strptime(item["content_data"]["unlock_at"], "%Y-%m-%dT%H:%M:%SZ") if \
                            item["content_data"]["unlock_at"] else None
                        due_at = datetime.strptime(item["content_data"]["due_at"], "%Y-%m-%dT%H:%M:%SZ") if \
                            item["content_data"]["due_at"] else None
                        self.save_assignment_data(subject_num, title, unlock_at, due_at)
                    elif item["content_type"] == "quiz":
                        due_at = datetime.strptime(item["content_data"]["due_at"], "%Y-%m-%dT%H:%M:%SZ") if \
                            item["content_data"]["due_at"] else None
                        self.save_quiz_data(subject_num, title, due_at)


            self.session.commit()

    def save_video_data(self, course_id, title, unlock_at, due_at):
        current_time = datetime.utcnow()
        existing_data = self.session.query(Video).filter_by(course_id=course_id, name=title).first()

        if existing_data is None:
            new_date = Video(course_id=course_id, name=title,
                             start_at=unlock_at, due_at=due_at, updated_at=current_time, created_at=current_time)
            self.session.add(new_date)
            course = self.session.query(Course).filter_by(course_id=course_id).first()
            course.updated_at = current_time
        else:
            if (
                    existing_data.start_at != unlock_at
                    or existing_data.due_at != due_at
            ):
                existing_data.start_at = unlock_at
                existing_data.due_at = due_at
                existing_data.updated_at = current_time
                course = self.session.query(Course).filter_by(course_id=course_id).first()
                course.updated_at = current_time

    def save_assignment_data(self, course_id, title, unlock_at, due_at):
        current_time = datetime.utcnow()
        existing_data = self.session.query(Assignment).filter_by(course_id=course_id, name=title).first()

        if existing_data is None:
            new_date = Assignment(course_id=course_id, name=title,
                                  start_at=unlock_at, due_at=due_at, created_at=current_time, updated_at=current_time)
            self.session.add(new_date)
            course = self.session.query(Course).filter_by(course_id=course_id).first()
            course.updated_at = current_time
        else:
            if (
                    existing_data.start_at != unlock_at
                    or existing_data.due_at != due_at
            ):
                existing_data.start_at = unlock_at
                existing_data.due_at = due_at
                existing_data.updated_at = current_time
                course = self.session.query(Course).filter_by(course_id=course_id).first()
                course.updated_at = current_time

    def save_quiz_data(self, course_id, title, due_at):
        current_time = datetime.utcnow()
        course_name = self.session.query(Course).filter_by(course_id=course_id).first()
        existing_data = self.session.query(Calendar).filter_by(course=course_name, type="퀴즈", due_at=due_at).first()

        if existing_data is None:
            new_calendar_item = Calendar(type="퀴즈",
                                         course=course_name.name,
                                         due_at=due_at,
                                         name=title,
                                         created_at=current_time,
                                         updated_at=current_time
                                         )
            self.session.add(new_calendar_item)
            course = self.session.query(Course).filter_by(course_id=course_id).first()
            course.updated_at = current_time
        else:
            if (
                existing_data.due_at != due_at
            ):
                existing_data.due_at = due_at
                existing_data.updated_at = current_time
                course = self.session.query(Course).filter_by(course_id=course_id).first()
                course.updated_at = current_time






def smart_campus_crawling(token, user_id):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        smart_campus = SmartCampus(session)

        # Get subjects and save them to the database
        smart_campus.course(token, user_id)

        # Loop through the subjects and get attendance data for each
        subjects = session.query(UserCourseRelation).all()
        for subject in subjects:
            subject_num = subject.course_id
            smart_campus.get_calander_data(token, subject_num)  # 수정: get_calander_data 호출
            smart_campus.get_date(token, subject_num)

    except:
        return JSONResponse(content="Internal Server Error", status_code=500)

    return JSONResponse(content="OK", status_code=200)


if __name__ == "__main__":
    token = "테스트시 토큰 값을 넣어주세요."
    smart_campus_crawling(token)
