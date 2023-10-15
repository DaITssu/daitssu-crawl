import datetime

import bs4.element
import requests
from bs4 import BeautifulSoup
from datetime import date
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, CHAR, ARRAY, DateTime
import sqlalchemy
import configuration
import boto3

from fastapi.responses import JSONResponse

URL = "http://cse.ssu.ac.kr/03_sub/01_sub.htm"

Base = declarative_base()

db_url = sqlalchemy.engine.URL.create(
    drivername="postgresql",
    username=configuration.db_user_name,
    password=configuration.db_pw,
    host=configuration.db_host,
    database=configuration.db_name
)

engine = create_engine(db_url)
session_maker = sessionmaker(autoflush=False, autocommit=False, bind=engine)
metadata_obj = MetaData()

s3 = boto3.client("s3")


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
    views = Column(Integer)

    def __init__(self, row: bs4.element.Tag):
        children = row.findAll("td")
        number = children[0].text.strip()
        if number == "공지":
            self.__is_notice = True
            self.__link = URL + children[1].contents[0].contents[0]['href']
        else:
            self.__is_notice = False
            self.__link = URL + children[1].contents[0]['href']

        req = requests.get(self.__link)
        soup = BeautifulSoup(req.text, 'lxml')
        content = soup.find(summary='글보기').findAll("td")
        self.views = int(content[1].findAll('dd')[1].text.split()[0])
        real_content = content[2].text.strip()[:2048]  # content
        self.content = ("https://{0}.s3.amazonaws.com/{1}notice/CSE"
                        .format(configuration.bucket_name, configuration.file_path)
                        + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f") + ".txt")

        s3.put_object(Body=real_content,
                      Bucket=configuration.bucket_name,
                      Key=self.content)

        file_container = content[3].find(class_='file')
        files = None
        file_link = []
        if file_container is not None:
            files = file_container.findAll('a')
        if files is not None:
            for file in files:
                link = ("http://cse.ssu.ac.kr" + file['href'])
                file_link.append(link)
        self.file_url = file_link
        self.title = children[1].text.strip()
        self.image_url = []
        self.category = "컴퓨터학부"

        created_date = list(map(int, children[3].text.split(".")))
        self.created_at = date(created_date[0], created_date[1], created_date[2])
        self.updated_at = date(created_date[0], created_date[1], created_date[2])

        with engine.connect() as connect:
            department_table = Table("department", metadata_obj, schema="main", autoload_with=engine)
            query = department_table.select().where(department_table.c.name == "컴퓨터학부")
            results = connect.execute(query)
            for result in results:
                self.department_id = result.id

    def __str__(self):
        return ("title: {0}\n"
                "content: {1}\n"
                "image_url: {2}\n"
                "file_url: {3}\n"
                "department_id: {4}".format(
            self.title, self.content, self.image_url, self.file_url, self.department_id
        ))


def computer_department_crawling():
    try:
        page = 1  # 1 ~
        base_url = URL + "?page={0}".format(page)
        req = requests.get(base_url)
        soup = BeautifulSoup(req.text, 'lxml')
        content = soup.find('table', summary='글목록').find('tbody')
        rows = content.findChildren("tr")
        results = []
        for row in rows:
            results.append(ComputerNotification(row))

        with session_maker() as session:
            for result in results:
                session.add(result)
            session.commit()
    except (Exception,):
        return JSONResponse(content="Internal Server Error", status_code=500)

    return JSONResponse(content="OK", status_code=200)


if __name__ == "__main__":
    print(computer_department_crawling().status_code)
