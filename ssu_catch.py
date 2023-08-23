import json
import requests
from bs4 import BeautifulSoup
from enum import Enum, auto
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, CHAR, ARRAY, DateTime, TEXT
from sqlalchemy.orm import sessionmaker, declarative_base
import sqlalchemy
import dev_db

URL = "https://scatch.ssu.ac.kr/%ea%b3%b5%ec%a7%80%ec%82%ac%ed%95%ad"
department_id_dict = {"교수학습혁신센터": 1, "총무감사팀": 2, "국제팀": 3, "기획팀": 4, "사회공헌팀": 5, "장학팀": 6, "학생서비스팀": 7, "정보화팀": 8,
                      "교무팀": 9, "총무·인사팀": 10, "산학협력진흥팀": 11, "웹마스터": 12, "혁신공유대학 사업추진단": 13, "학사팀": 14, "창업지원단": 15,
                      "공대 교학팀": 16, "진로취업센터": 17, "현장실습지원센터": 18, "교양교육연구센터": 19}
# department id 어떻게 할지 생각해야함.
Base = declarative_base()


class NoticeDB(Base):
    __tablename__ = "notice"
    __table_args__ = {"schema": "notice"}
    id = Column(Integer, primary_key=True)
    title = Column(TEXT)
    department_id = Column(Integer)
    content = Column(TEXT)
    category = Column(CHAR(32))  # 카테고리 Enum방식이면 db에 어떻게 저장할지 생각
    image_url = Column(ARRAY(TEXT))
    file_url = Column(ARRAY(TEXT))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Category(Enum):
    # Category 용 Enum
    school = auto()  # 학사
    scholarship = auto()  # 장학
    international = auto()  # 국제 교류
    foreigner = auto()  # 외국인 유학생
    employment = auto()  # 채용
    event = auto()  # 비교과, 행사
    faculty_recruitment = auto()  # 교원 채용
    teaching_profession = auto()  # 교직
    volunteer = auto()  # 봉사
    etc = auto()  # 기타
    covid19 = auto()  # 코로나 19 관련 소식


class Content:  # Crawling 결과를 담는 객체

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

        current_column = next(columns)
        self.__init_department(lists[current_column])

        current_column = next(columns)
        self.__init_views(lists[current_column])

    def __init_date(self, column):  # 생성 시각 크롤링
        target = column.find('div')
        date_arr = [int(item) for item in target.text.strip().split(".")]
        self.create_date = date(date_arr[0], date_arr[1], date_arr[2])
        self.updated_date = date(date_arr[0], date_arr[1], date_arr[2])

    def __init_contents(self, column):  # 본문 내용 크롤링
        self.img_link = []
        self.contents = ""
        self.file_link = []

        target = column.find('a')
        post_url = target['href']
        req = requests.get(post_url)
        soup = BeautifulSoup(req.text, 'lxml')
        contents = soup.find("div", class_="clearfix").find_next_sibling('div')
        for tag in contents.findAll('p'):
            img = tag.find("img", class_=lambda css_class: css_class != "emoji")
            if img:
                self.img_link.append(img['src'])
            else:
                self.contents += BeautifulSoup(tag.text, "lxml").text
        file_urls = contents.find("ul")
        if file_urls:
            links = file_urls.findAll("a")
            for item in links:
                self.file_link.append(item['href'])

    def __init_category(self, column):  # 카테고리 크롤링
        category_dict = {
            "학사": 1,
            "장학": 2,
            "국제교류": 3,
            "외국인유학생": 4,
            "채용": 5,
            "비교과·행사": 6,
            "교원채용": 7,
            "봉사": 8,
            "교직": 9,
            "기타": 10,
            "코로나19관련소식": 11
        }
        target = column.find('span', class_='label')
        self.category = category_dict.get(target.text.strip())

    def __init_title(self, column):  # 제목 크롤링
        target = column.findAll("span")[2]
        self.title = target.text.strip()

    def __init_department(self, column):  # 등록 부서 크롤링
        self.department = department_id_dict.get(column.text.strip())

    def __init_views(self, column):  # 조회수 크롤링
        self.views = int(column.text.strip())

    def __str__(self) -> str:
        return "title: {0}\n" \
               "category: {1}\n" \
               "view: {2}\n" \
               "date: {3}\n" \
               "link: {4}\n" \
               "department: {5}\n" \
               "content: {6}\n" \
               "img: {7}\n" \
            .format(self.title,
                    self.category,
                    self.views,
                    self.create_date,
                    self.file_link,
                    self.department,
                    self.contents[:200],
                    self.img_link
                    )

    def to_dict(self):
        return {
            "title": self.title,
            "category": self.category.name if self.category else None,
            "views": self.views,
            "created_date": self.create_date.isoformat(),
            "file_link": self.file_link,
            "department": self.department,
            "contents": self.contents,
            "img_link": self.img_link
        }

    def to_json(self):
        return json.dumps(self.to_dict())


def ssu_catch_crawling(value):
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

    db_url = sqlalchemy.engine.URL.create(  # db연결 url 생성
        drivername="postgresql+psycopg2",
        username=dev_db.dev_user_name,
        password=dev_db.dev_db_pw,
        host=dev_db.dev_host,
        database=dev_db.dev_db_name
    )

    engine = create_engine(db_url)  # db 연결
    session_maker = sessionmaker()
    session_maker.configure(bind=engine)

    with session_maker() as session:

        for content in content_list:
            if len(content.contents) >= 2048:
                print("ERROR!!!!")  # content의 길이가 2048보다 클 경우가 있음.
                print(len(content.contents))
                print(content.contents)
                break
            session.add(NoticeDB(title=content.title,  # orm 객체 저장.
                                 department_id=content.department,
                                 content=content.contents,
                                 image_url=content.img_link,
                                 file_url=content.file_link,
                                 created_at=content.create_date,
                                 category=content.category,
                                 updated_at=content.updated_date))
        session.commit()


ssu_catch_crawling(1)
