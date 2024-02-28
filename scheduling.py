from apscheduler.schedulers.background import BackgroundScheduler

# import notice.ai
import notice.computer
import notice.ssu_catch
import fun_system.fun_system
from smart_campus.smart_campus import *
import sqlalchemy
import configuration

from sqlalchemy.orm import sessionmaker

def notice_scrapping():
    # notice.ai.ai_department_crawling()
    notice.computer.computer_department_crawling()
    notice.ssu_catch.ssu_catch_crawling()
    fun_system.fun_system.fun_system_crawling(10)

def course_refresh():
    db = sqlalchemy.engine.URL.create(
        drivername="mysql+pymysql",
        username=configuration.db_user_name,
        password=configuration.db_pw,
        host=configuration.db_host,
        database=configuration.db_name
    )

    engine = sqlalchemy.create_engine(db)
    Session = sessionmaker(bind=engine)
    session = Session()

    users = session.query(Users).all()

    for user in users:
        token = user.ssu_token
        student_id = user.student_id
        if (token is not None and student_id is not None):
            smart_campus_crawling(token, student_id)


scheduler = BackgroundScheduler(daemon=True, timezone='Asia/Seoul')

scheduler.add_job(notice_scrapping, 'cron', hour='0', minute='10')
scheduler.add_job(course_refresh, 'cron', hour='0,12', minute='10')

def start_scheduling():
    scheduler.start()