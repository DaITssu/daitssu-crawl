import bs4.element
import requests
from bs4 import BeautifulSoup
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, CHAR, ARRAY, DateTime
import sqlalchemy
import dev_db

URL = "http://cse.ssu.ac.kr/03_sub/01_sub.htm"

Base = declarative_base()


class ComputerNotification(Base):
    __tablename__ = "notice"
    __table_args__ = {"schema": "notice"}
    id = Column(Integer, primary_key=True)
    title = Column(CHAR(1024))
    department_id = Column(Integer)
    content = Column(CHAR(2048))
    category = Column(CHAR(32))
    image_url = Column(ARRAY(CHAR(2048)))
    file_url = Column(ARRAY(CHAR(2048)))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __init__(self, row: bs4.element.Tag):
        children = row.findAll("td")
        number = children[0].text.strip()
        if number == "공지":
            self.__is_notice = True
            self.__link = URL + children[1].contents[0].contents[0]['href']
        else:
            self.__id = int(number)
            self.__is_notice = False
            self.__link = URL + children[1].contents[0]['href']

        req = requests.get(self.__link)
        soup = BeautifulSoup(req.text, 'lxml')
        content = soup.find(summary='글보기').findAll("td")
        self.content = content[2].text.strip()  # content

        file_container = content[3].find(class_='file')
        files = None
        file_link = []
        if file_container is not None:
            files = file_container.findAll('a')
        if files is not None:
            for file in files:
                file_link.append("http://cse.ssu.ac.kr" + file['href'])
        self.file_url = file_link
        self.title = children[1].text.strip()

        date_splits = list(map(int, children[3].text.strip().split('.')))
        self.__create_date = date(date_splits[0], date_splits[1], date_splits[2])


def computer_department_crawling(value):
    page = 1  # 1 ~
    base_url = URL + "?page={0}".format(page)
    req = requests.get(base_url)
    soup = BeautifulSoup(req.text, 'lxml')
    content = soup.find('table', summary='글목록').find('tbody')
    rows = content.findChildren("tr")
    result = []
    for row in rows:
        result.append(ComputerNotification(row))
        print(result[len(result) - 1], '\n')

    db_url = sqlalchemy.engine.URL.create(
        drivername="postgresql+psycopg2",
        username=dev_db.dev_user_name,
        password=dev_db.dev_db_pw,
        host=dev_db.dev_host,
        database=dev_db.dev_db_name
    )

    engine = create_engine(db_url)
    session_maker = sessionmaker()
    session_maker.configure(bind=engine)

    with session_maker() as session:
        for content in result:
            session.add(content)


def departments_crawling(value):
    computer_department_crawling(value)
