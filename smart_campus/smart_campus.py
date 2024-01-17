from collections import defaultdict

import requests
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, CHAR, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime
import configuration

from db_table import Base
from db_table import Course, UserCourseRelation, Video, Assignment, Calendar

db_url = sqlalchemy.engine.URL.create(
    drivername="mysql+pymysql",
    username=configuration.db_user_name,
    password=configuration.db_pw,
    host=configuration.db_host,
    database=configuration.db_name
)
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)

def create_tables():
    Base.metadata.create_all(engine)

def drop_tables():
    Base.metadata.drop_all(engine)
default_date = datetime.datetime(9999, 12, 31, 23, 59, 59)
default_start_date = datetime.datetime(2023, 1, 1, 00, 00, 00)
current_time = datetime.datetime.now()
term_num = 31
class SmartCampus:
    def __init__(self, session):
        self.session = session

    color_list = ['FF8DC4', 'FF7171', 'FF9E68', 'FFD057', 'B7E532', '35CC7B', '73E4DE', '6197FF', 'B69BE3', 'A48172']
    over_color = 'BDBDBD'

    def course(self, token, user_id):
        url = f"https://canvas.ssu.ac.kr/learningx/api/v1/learn_activities/courses?term_ids[]={term_num}"
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



    def get_date(self, token, subject_num):
        subject = subject_num
        url, headers = f"https://canvas.ssu.ac.kr/learningx/api/v1/courses/{subject}/modules?include_detail=true", {
            "Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            for module in data:
                for item in module.get("module_items", []):
                    title = item["title"][:32] if len(item["title"]) > 32 else item["title"]
                    content_data = item.get("content_data")
                    if content_data is not None:
                        content_data = content_data.get("item_content_data", {})
                    else:
                        content_data = {}
                    content_type = content_data.get("content_type")

                    if content_type and content_type in ["movie", "mp4", "zoom"]:
                        unlock_at, due_at = self.parse_datetime(content_data.get("unlock_at")), self.parse_datetime(
                            content_data.get("due_at"))
                        self.save_video_data(subject_num, title, unlock_at, due_at)
                    elif content_type == "assignment":
                        unlock_at, due_at = self.parse_datetime(
                            item["content_data"].get("unlock_at")), self.parse_datetime(
                            item["content_data"].get("due_at"))
                        self.save_assignment_data(subject_num, title, unlock_at, due_at)

            self.session.commit()

    def parse_datetime(self, datetime_str):
        return datetime.datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ") if datetime_str else None

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

    def create_calendar_item(self, course, item_type, status, due_at, name, user_id, assignment, video, quiz):
        existing_data = self.session.query(Calendar).filter_by(name=name, due_at=due_at).first()

        if existing_data is None:
            new_calendar_item = Calendar(
                type=item_type,
                course_id=course.id,
                due_at=due_at,
                is_completed=status,
                name=name,
                created_at=current_time,
                updated_at=current_time,
                user_id=user_id
            )
            # 여기서 course가 None인지 확인
            if course:
                course_updated_at = getattr(course, 'updated_at', None)
                if course_updated_at is not None:
                    course_updated_at = current_time
            self.session.add(new_calendar_item)
        else:
            if existing_data.due_at != due_at:
                change_data = self.session.query(Calendar).filter_by(name=name).first()
                change_data.due_at = due_at
                # 여기서 course가 None인지 확인
                if course:
                    course_updated_at = getattr(course, 'updated_at', None)
                    if course_updated_at is not None:
                        course_updated_at = current_time

            if name in assignment:
                assignment.pop(name)  # 해당 assignment를 처리했으므로 pop
            elif name in video:
                video.pop(name)
            elif name in quiz:
                quiz.pop(name)

        self.session.commit()

    def save_to_do_to_calendar(self, token, user_id):
        url = f"https://canvas.ssu.ac.kr/learningx/api/v1/learn_activities/to_dos?term_ids[]={term_num}"
        headers = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data_dict = response.json()

            for module in data_dict.get("to_dos", []):

                course_id = module.get("course_id")

                assignment = defaultdict(list)
                video = defaultdict(list)
                quiz = defaultdict(list)

                # 여기서 session을 self.session으로 수정
                course = self.session.query(Course).filter_by(course_code=str(course_id)).first()

                # 필요한 데이터 가져오기
                query = self.session.query(Calendar).filter_by(course_id=course.id)
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
                            title = todo.get('title')
                            due_at = todo.get('due_date')
                            if todo.get("component_type") == "assignment" and not todo.get(
                                    "generated_from_lecture_content"):

                                # 여기서 session을 self.session으로 수정
                                course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
                                self.create_calendar_item(course, "ASSIGNMENT", False, due_at, title, user_id, assignment, video, quiz)

                            elif todo.get("component_type") == "commons":

                                # 여기서 session을 self.session으로 수정
                                course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
                                self.create_calendar_item(course, "VIDEO", False, due_at, title, user_id, assignment, video, quiz)

                            elif todo.get("component_type") == "quiz":

                                # 여기서 session을 self.session으로 수정
                                course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
                                self.create_calendar_item(course, "QUIZ", False, due_at, title, user_id, assignment, video, quiz)

                        # 남은 데이터 처리
                        for assign in assignment.keys():
                            change_data = self.session.query(Calendar).filter_by(name=assign).first()
                            if change_data.is_completed == False:
                                change_data.is_completed = True
                            course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
                            course.updated_at = current_time

                        for video in video.keys():
                            change_data = self.session.query(Calendar).filter_by(name=video).first()
                            if change_data.is_completed == False:
                                change_data.is_completed = True
                            course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
                            course.updated_at = current_time

                        for quiz in quiz.keys():
                            change_data = self.session.query(Calendar).filter_by(name=quiz).first()
                            if change_data.is_completed == False:
                                change_data.is_completed = True
                            course = self.session.query(Course).filter_by(course_code=str(course_id)).first()
                            course.updated_at = current_time

                    else:
                        print("이 모듈에서는 Course ID를 찾을 수 없습니다.")


    def get_calendar_data(self, token, subject_num, user_id):
        subject = subject_num
        attendance_url = f"https://canvas.ssu.ac.kr/learningx/api/v1/courses/{subject}/attendance_items?include_detail=true"
        summary_url = f"https://canvas.ssu.ac.kr/learningx/api/v1/courses/{subject}/attendance_items/summary?only_use_attendance=true"

        headers = {"Authorization": "Bearer " + token}

        summary_data = requests.get(summary_url, headers=headers).json().get("attendance_summaries", {})
        attendance_items = requests.get(attendance_url, headers=headers).json().get("attendance_items", [])

        for item in attendance_items:
            item_content_data = item.get("item_content_data", {})
            placement, schedule_time, item_id_data = item_content_data.get("placement"), item_content_data.get(
                "schedule_time"), item.get("item_id")
            status = any(item_id_data == item_id and attendance_summary["attendance_status"] == "attendance"
                         for item_id, attendance_summary in summary_data.items())

            if placement and not self.session.query(Calendar).filter_by(due_at=schedule_time).first():
                course = self.session.query(Course).filter_by(course_code=str(subject_num)).first()
                self.create_calendar_item(self.session, course, "OFFLINE_LECTURE", status, schedule_time, item.get("title"),
                                          user_id)

        self.session.commit()



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

        smart_campus.get_calendar_data(token, subject_num, user_id)
    smart_campus.save_user_course_data(token, user_id)
    smart_campus.save_to_do_to_calendar(token, user_id)

    # 모든 작업이 정상적으로 완료되면 commit 수행
    session.commit()

    return "Success"


if __name__ == "__main__":
    token = "토큰 입력"
    user_id = "유저 아이디 입력"
    smart_campus_crawling(token, user_id)

