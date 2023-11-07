import botocore.exceptions
import requests
from bs4 import BeautifulSoup
from datetime import date
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker, declarative_base
import sqlalchemy
import configuration
from fastapi.responses import JSONResponse
import boto3

from control_s3 import update_notification
from notification import Notification

URL = "https://scatch.ssu.ac.kr/%ea%b3%b5%ec%a7%80%ec%82%ac%ed%95%ad"

metadata_obj = MetaData()
Base = declarative_base()

db_url = sqlalchemy.engine.URL.create(  # db연결 url 생성
    drivername="postgresql",
    username=configuration.db_user_name,
    password=configuration.db_pw,
    host=configuration.db_host,
    database=configuration.db_name
)
engine = create_engine(db_url)  # db 연결
session_maker = sessionmaker()
session_maker.configure(bind=engine)

s3 = boto3.client("s3",
                  aws_access_key_id=configuration.aws_access_key_id,
                  aws_secret_access_key=configuration.aws_secret_access_key)


class Content(Notification):  # Crawling 결과를 담는 객체

    def __init__(self, content):
        lists = list(content.children)
        columns = iter([1, 3, 5, 7, 9])

        current_column = next(columns)
        self.__init_date(lists[current_column])

        next(columns)
        current_column = next(columns)
        self.__init_contents(lists[current_column])
        self.__init_category(lists[current_column])
        self.__init_title(lists[current_column])

        self.__init_department()
        next(columns)

        current_column = next(columns)
        self.__init_views(lists[current_column])

    def __init_date(self, column):  # 생성 시각 크롤링
        target = column.find('div')
        date_arr = [int(item) for item in target.text.strip().split(".")]
        self.created_at = date(date_arr[0], date_arr[1], date_arr[2])
        self.updated_at = date(date_arr[0], date_arr[1], date_arr[2])

    def __init_contents(self, column):  # 본문 내용 크롤링
        self.image_url = []
        self.content = ""
        real_content = ""
        self.file_url = []

        target = column.find('a')
        post_url = target['href']
        req = requests.get(post_url)
        soup = BeautifulSoup(req.text, 'lxml')
        contents = soup.find("div", class_="clearfix").find_next_sibling('div')
        for tag in contents.findAll('p'):
            img = tag.find("img", class_=lambda css_class: css_class != "emoji")
            if img:
                self.image_url.append(img['src'])
            else:
                real_content += BeautifulSoup(tag.text, "lxml").text
        file_urls = contents.find("ul")

        if file_urls:
            links = file_urls.findAll("a")
            for item in links:
                self.file_url.append(item['href'])

        self.content = real_content

    def __init_category(self, column):  # 카테고리 크롤링
        category_dict = {
            "학사": "ACADEMICS",
            "장학": "SCHOLARSHIP",
            "국제교류": "INTERNATIONAL_EXCHANGE",
            "외국인유학생": "INTERNATIONAL_STUDENT",
            "채용": "RECRUITMENT",
            "비교과·행사": "EXTRACURRICULAR",
            "교원채용": "FACULTY_RECRUITMENT",
            "봉사": "VOLUNTEERING",
            "교직": "TEACHING",
            "기타": "OTHER",
            "코로나19관련소식": "COVID_19"
        }
        target = column.find('span', class_='label')
        self.category = category_dict.get(target.text.strip())

    def __init_title(self, column):  # 제목 크롤링
        target = column.findAll("span")[2]
        self.title = target.text.strip()

    def __init_department(self):  # 등록 부서 크롤링
        with engine.connect() as connect:
            department_table = Table("department", metadata_obj, schema="main", autoload_with=engine)
            query = department_table.select().where(department_table.c.name == "슈케치")
            results = connect.execute(query)
            for result in results:
                self.department_id = result.id

    def __init_views(self, column):
        self.views = int(column.text.strip())

    def __str__(self) -> str:
        return "title: {0}\n" \
               "category: {1}\n" \
               "date: {2}\n" \
               "link: {3}\n" \
               "department_id: {4}\n" \
               "content: {5}\n" \
               "img: {6}\n" \
            .format(self.title,
                    self.category,
                    self.created_at,
                    self.file_url,
                    self.department_id,
                    self.content[:200],
                    self.image_url
                    )


def ssu_catch_crawling():
    try:
        page = 1  # 1~
        base_url = URL + "/page/{0}".format(page)
        req = requests.get(base_url)

        soup = BeautifulSoup(req.text, 'lxml')
        content = soup.find(class_='notice-lists').children

        content_iterator = iter(content)
        for i in range(3):
            next(content_iterator)

        content_list = []
        for (idx, item) in enumerate(content_iterator):  # 핵심 크롤링 부분
            if idx % 2 == 0:
                content_list.append(Content(item.find('div')))
        notification_table = Table("notice", metadata_obj, schema="notice", autoload_with=engine)

        with session_maker() as session:
            for result in content_list:
                update_notification("SsuCatch", result, session, s3, notification_table)
            session.commit()

    except botocore.exceptions.NoCredentialsError as e:
        return JSONResponse(content=e.args, status_code=403)
    except Exception as e:
        return JSONResponse(content=e.args, status_code=500)

    return JSONResponse(content="OK", status_code=200)


if __name__ == "__main__":
    ssu_catch_crawling()
