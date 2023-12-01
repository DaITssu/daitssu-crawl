import requests
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, CHAR, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi.responses import JSONResponse
import datetime
import configuration


Base = declarative_base()
db_url = sqlalchemy.engine.URL.create(  # db연결 url 생성
    drivername="postgresql",
    username=configuration.db_user_name,
    password=configuration.db_pw,
    host=configuration.db_host,
    database=configuration.db_name
)

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
default_date = datetime.datetime(9999, 12, 31, 23, 59, 59)
default_start_date = datetime.datetime(2023,1,1,00,00,00)
current_time = datetime.datetime.now()

class Course(Base):
    __tablename__ = 'course'
    __table_args__ = {"schema": "course"}
    course_code = Column(CHAR(32), nullable=False)
    id = Column(Integer, primary_key=True)
    name = Column(CHAR(64))
    term = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Video(Base):
    __tablename__ = 'video'
    __table_args__ = {"schema": "course"}
    id = Column(Integer, primary_key=True)
    name = Column(CHAR(256))
    course_id = Column(Integer, ForeignKey('course.course.id'))
    due_at = Column(DateTime, default=default_date)
    start_at = Column(DateTime, default=default_date)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Assignment(Base):
    __tablename__ = 'assignment'
    __table_args__ = {"schema": "course"}
    id = Column(Integer, primary_key=True)
    name = Column(CHAR(256))
    course_id = Column(Integer, ForeignKey('course.course.id'))
    due_at = Column(DateTime, default=default_date)
    start_at = Column(DateTime, default=default_date)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class UserCourseRelation(Base):
    __tablename__ = 'user_course_relation'
    __table_args__ = {"schema": "course"}
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    course_id = Column(Integer, ForeignKey('course.course.id'))
    register_status = Column(CHAR(20))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Calendar(Base):
    __tablename__ = 'calendar'
    __table_args__ = {"schema": "course"}
    id = Column(Integer, primary_key=True)
    type = Column(CHAR(32))
    course = Column(CHAR(64))
    due_at = Column(DateTime,default=default_date)
    name = Column(CHAR(256))
    is_complete = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    user_id = Column(Integer)



class SmartCampus:
    def __init__(self, session):
        self.session = session

    color_list = ['FF8DC4', 'FF7171', 'FF9E68', 'FFD057', 'B7E532', '35CC7B', '73E4DE', '6197FF', 'B69BE3', 'A48172']
    over_color = 'BDBDBD'

    def course(self, token, user_id):
        url = "https://canvas.ssu.ac.kr/learningx/api/v1/learn_activities/courses?term_ids[]=31"
        headers = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)
        cnt = 1
        if response.status_code == 200:
            data = response.json()
            for module in data:
                course_title = module["name"]
                course_title = course_title
                course_id = module["id"]
                color_code = self.color_list[cnt - 1] if cnt < 11 else self.over_color
                self.save_course_data(course_id, course_title, color_code)
                self.save_user_course_data(user_id, course_id)
                cnt += 1
            self.session.commit()

    def save_course_data(self, course_id, course_title, color_code):
        existing_course = self.session.query(Course).filter_by(name=course_title).first()
        if existing_course is None:
            new_subject = Course(course_code=str(course_id), term=2, name=course_title, created_at=current_time,
                                 updated_at=current_time)
            self.session.add(new_subject)
            self.session.commit()

    def save_user_course_data(self, user_id, course_id):
        existing_course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
        if existing_course is not None:
            course_id_temp = existing_course.id
            existing_course_of_user = self.session.query(UserCourseRelation).filter_by(user_id=user_id,
                                                                                       course_id=course_id_temp).first()
            if existing_course_of_user is None:
                put_course = UserCourseRelation(user_id=user_id, course_id=course_id_temp, register_status="ACTIVE",
                                                created_at=current_time, updated_at=current_time)
                self.session.add(put_course)
                self.session.commit()
        else:
            print(f"Course with code {course_id} not found.")

    def get_calander_data(self, token, subject_num, user_id):
        subject = subject_num
        url = f"https://canvas.ssu.ac.kr/learningx/api/v1/courses/{subject}/attendance_items?include_detail=true"
        headers = {"Authorization": "Bearer " + token}

        summary_url = f"https://canvas.ssu.ac.kr/learningx/api/v1/courses/{subject}/attendance_items/summary?only_use_attendance=true"
        response_summary = requests.get(summary_url, headers=headers)
        if response_summary.status_code == 200:
            summary_data = response_summary.json().get("attendance_summaries", {})

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
                    if not self.session.query(Calendar).filter_by(due_at=schedule_time).first():
                        for item_id, attendance_summary in summary_data.items():
                            if item_id == item_id_data:
                                if attendance_summary["attendance_status"] == "attendance":
                                    status = True
                                    break
                        course_name = self.session.query(Course).filter_by(course_code=str(subject_num)).first()
                        new_calendar_item = Calendar(type="OFFLINE_LECTURE",
                                                     course=course_name.name,
                                                     due_at=schedule_time,
                                                     is_complete=status,
                                                     name=item.get("title"),
                                                     created_at=current_time,
                                                     updated_at=current_time,
                                                     user_id = user_id
                                                     )
                        course = self.session.query(Course).filter_by(course_code=str(subject_num)).first()
                        course.updated_at = current_time
                        self.session.add(new_calendar_item)

            self.session.commit()
        else:
            print("API 요청에 실패했습니다. 응답 코드:", response.status_code)

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


                    title = item["title"]
                    if len(title) > 32:
                        title = title
                    content_data = item.get("content_data", {})  # content_data 키가 없을 경우 빈 딕셔너리 반환
                    if content_data is not None:
                        item_content_data = content_data.get("item_content_data",
                                                             {})  # item_content_data 키가 없을 경우 빈 딕셔너리 반환
                        content_type = item_content_data.get("content_type")  # content_type 키가 없을 경우 None 반환

                        if content_type and content_type in ["movie", "mp4", "zoom"]:
                            # 조건이 만족할 때 실행할 코드
                            unlock_at = datetime.datetime.strptime(content_data.get("unlock_at", ""),
                                                                   "%Y-%m-%dT%H:%M:%SZ") if \
                                content_data.get("unlock_at") else None
                            due_at = datetime.datetime.strptime(content_data.get("due_at", ""), "%Y-%m-%dT%H:%M:%SZ") if \
                                content_data.get("due_at") else None
                            self.save_video_data(subject_num, title, unlock_at, due_at)
                        elif item["content_type"] == "assignment":
                            unlock_at = datetime.datetime.strptime(item["content_data"]["unlock_at"],
                                                                   "%Y-%m-%dT%H:%M:%SZ") if \
                                item["content_data"]["unlock_at"] else None
                            due_at = datetime.datetime.strptime(item["content_data"]["due_at"], "%Y-%m-%dT%H:%M:%SZ") if \
                                item["content_data"]["due_at"] else None
                            self.save_assignment_data(subject_num, title, unlock_at, due_at)

            self.session.commit()

    def save_video_data(self, course_id, title, unlock_at, due_at):
        existing_course = self.session.query(Course).filter_by(course_code=str(course_id)).first()

        course_id_temp = existing_course.id
        existing_data = self.session.query(Video).filter_by(course_id=course_id_temp, name=title).first()
        if due_at is None:
            due_at = default_date
        if unlock_at is None:
            unlock_at = default_start_date
        if existing_data is None:
            new_date = Video(course_id=course_id_temp, name=title,
                             start_at=unlock_at, due_at=due_at, updated_at=current_time, created_at=current_time)
            self.session.add(new_date)
            existing_course.updated_at = current_time
            self.session.commit()
        else:
            if (
                existing_data.start_at != unlock_at
                or existing_data.due_at != due_at
            ):
                existing_data.start_at = unlock_at
                existing_data.due_at = due_at
                existing_data.updated_at = current_time
                existing_course.updated_at = current_time
                self.session.commit()


        self.session.commit()

    def save_assignment_data(self, course_id, title, unlock_at, due_at):
        existing_course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
        course_id_temp = existing_course.id
        existing_data = self.session.query(Assignment).filter_by(course_id=course_id_temp, name=title).first()
        if due_at is None:
            due_at = default_date
        if unlock_at is None:
            unlock_at = default_start_date
        if existing_data is None:
            new_date = Assignment(course_id=course_id_temp, name=title,
                                  start_at=unlock_at, due_at=due_at, created_at=current_time, updated_at=current_time)
            self.session.add(new_date)
            existing_course.updated_at = current_time
            self.session.commit()
        else:
            if (
                existing_data.start_at != unlock_at
                or existing_data.due_at != due_at
            ):
                existing_data.start_at = unlock_at
                existing_data.due_at = due_at
                existing_data.updated_at = current_time
                existing_course.updated_at = current_time
                self.session.commit()

        self.session.commit()

    def save_to_do_to_calendar(self, token, user_id):
        url = "https://canvas.ssu.ac.kr/learningx/api/v1/learn_activities/to_dos?term_ids[]=31"
        headers = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data_dict = response.json()  # JSON 응답을 파이썬의 딕셔너리로 변환

            for module in data_dict.get("to_dos", []):
                course_id = module.get("course_id")

                assignment = defaultdict(list)
                video = defaultdict(list)
                quiz = defaultdict(list)

                session = Session()
                course = self.session.query(Course).filter_by(course_code=str(course_id)).first()

                # 필요한 데이터 가져오기
                query = session.query(Calendar).filter_by(course=course.name)
                calendars = query.all()

                # 데이터를 HashMap에 저장
                for calendar in calendars:
                    if calendar.type == 'ASSIGNMENT':
                        assignment[calendar.name].append(calendar.due_at)
                    elif calendar.type == 'VIDEO':
                        video[calendar.name].append(calendar.due_at)
                    elif calendar.type == 'QUIZ':
                        quiz[calendar.name].append(calendar.due_at)

                if course_id:
                    activities = module.get("activities", {})
                    last_assignment = activities.get("total_unsubmitted_assignments")
                    last_video = activities.get("total_incompleted_movies")

                    if last_assignment != 0 or last_video != 0:
                        todo_list = module.get("todo_list", [])

                        for todo in todo_list:
                            if todo.get("component_type") == "assignment" and not todo.get(
                                    "generated_from_lecture_content"):
                                title = todo.get('title')
                                due_at = todo.get('due_date')
                                existing_data = self.session.query(Calendar).filter_by(name=title,
                                                                                       due_at=due_at).first()

                                if existing_data is None:
                                    course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
                                    new_calendar_item = Calendar(
                                        type="ASSIGNMENT",
                                        course=course.name,
                                        due_at=due_at,
                                        is_complete=False,
                                        name=title,
                                        created_at=current_time,
                                        updated_at=current_time,
                                        user_id=user_id
                                    )
                                    course.updated_at = current_time
                                    self.session.add(new_calendar_item)
                                elif title in assignment:
                                    if existing_data.due_at != due_at:
                                        change_data = self.session.query(Calendar).filter_by(name=title).first()
                                        change_data.due_at = due_at
                                        course = self.session.query(Course).filter_by(
                                            course_code=str(course_id)).first()
                                        course.updated_at = current_time
                                    assignment.pop(title)  # 해당 assignment를 처리했으므로 pop

                            elif todo.get("component_type") == "commons":
                                title = todo.get('title')
                                due_at = todo.get('due_date')
                                existing_data = self.session.query(Calendar).filter_by(name=title,
                                                                                       due_at=due_at).first()

                                if existing_data is None:
                                    course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
                                    new_calendar_item = Calendar(
                                        type="VIDEO",
                                        course=course.name,
                                        due_at=due_at,
                                        is_complete=False,
                                        name=title,
                                        created_at=current_time,
                                        updated_at=current_time,
                                        user_id=user_id
                                    )
                                    course.updated_at = current_time
                                    self.session.add(new_calendar_item)
                                elif title in video:
                                    if existing_data.due_at != due_at:
                                        change_data = self.session.query(Calendar).filter_by(name=title).first()
                                        change_data.due_at = due_at
                                        course = self.session.query(Course).filter_by(
                                            course_code=str(course_id)).first()
                                        course.updated_at = current_time
                                    video.pop(title)  # 해당 video를 처리했으므로 pop

                            elif todo.get("component_type") == "quiz":
                                title = todo.get('title')
                                due_at = todo.get('due_date')
                                existing_data = self.session.query(Calendar).filter_by(name=title,
                                                                                       due_at=due_at).first()

                                if existing_data is None:
                                    course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
                                    new_calendar_item = Calendar(
                                        type="QUIZ",
                                        course=course.name,
                                        due_at=due_at,
                                        is_complete=False,
                                        name=title,
                                        created_at=current_time,
                                        updated_at=current_time,
                                        user_id=user_id
                                    )
                                    course.updated_at = current_time
                                    self.session.add(new_calendar_item)
                                elif title in quiz:
                                    if existing_data.due_at != due_at:
                                        change_data = self.session.query(Calendar).filter_by(name=title).first()
                                        change_data.due_at = due_at
                                        course = self.session.query(Course).filter_by(
                                            course_code=str(course_id)).first()
                                        course.updated_at = current_time
                                    quiz.pop(title)  # 해당 quiz를 처리했으므로 pop

                        # 남은 데이터 처리
                        for assign in assignment.keys():
                            change_data = self.session.query(Calendar).filter_by(name=assign).first()
                            if change_data.is_complete == False:
                                change_data.is_complete = True
                            course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
                            course.updated_at = current_time

                        for video in video.keys():
                            change_data = self.session.query(Calendar).filter_by(name=video).first()
                            if change_data.is_complete == False:
                                change_data.is_complete = True
                            course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
                            course.updated_at = current_time

                        for quiz in quiz.keys():
                            change_data = self.session.query(Calendar).filter_by(name=quiz).first()
                            if change_data.is_complete == False:
                                change_data.is_complete = True
                            course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
                            course.updated_at = current_time

                    else:
                        print("이 모듈에서는 Course ID를 찾을 수 없습니다.")


def smart_campus_crawling(token, user_id):
        Session = sessionmaker(bind=engine)
        session = Session()
        smart_campus = SmartCampus(session)
        # Get subjects and save them to the database
        smart_campus.course(token, user_id)
        courses = session.query(UserCourseRelation).all()

        for course in courses:

            real_id = session.query(Course).filter_by(id=course.course_id).first()
            subject_num = int(real_id.course_code)
            smart_campus.get_date(token, subject_num)
        for course in courses:

            real_id = session.query(Course).filter_by(id=course.course_id).first()
            subject_num = int(real_id.course_code)

            smart_campus.get_calander_data(token, subject_num, user_id)
        smart_campus.save_user_course_data(token, user_id)
        smart_campus.save_to_do_to_calendar(token, user_id)

        # 모든 작업이 정상적으로 완료되면 commit 수행
        session.commit()



if __name__ == "__main__":
    token = "테스트 토큰 입력"
    user_id = "유저 아이디 입력"
    smart_campus_crawling(token, user_id)



