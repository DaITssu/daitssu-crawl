import bs4.element
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, CHAR, ARRAY, DateTime, String
import sqlalchemy
import boto3
import configuration
from fastapi.responses import JSONResponse

from control_db import update_notification
from notification import Notification

AI_BASE_URL = "http://aix.ssu.ac.kr/"

db_url = sqlalchemy.engine.URL.create(
    drivername="postgresql",
    username=configuration.db_user_name,
    password=configuration.db_pw,
    host=configuration.db_host,
    database=configuration.db_name,
)

engine = create_engine(db_url)
session_maker = sessionmaker(autoflush=False, autocommit=False, bind=engine)
metadata_obj = MetaData()

s3 = boto3.client(
    "s3",
    aws_access_key_id=configuration.aws_access_key_id,
    aws_secret_access_key=configuration.aws_secret_access_key,
)


class AiNotification(Notification):
    def __init__(self, row: bs4.element.Tag):
        childrens = row.find_all("td")

        if childrens:
            href = childrens[0].find("a")["href"]
            self.__link = AI_BASE_URL + href
        else:
            return

        req = requests.get(self.__link)
        soup = BeautifulSoup(req.text, "lxml")
        contents = soup.find("table", class_="table").find_all("p")

        # 제목
        self.title = childrens[0].text.strip()

        # 내용
        self.content = ""
        for content in contents:
            self.content += content.text

        if len(self.content.encode("utf-8")) > 2048:
            file_name = "AI" + str(datetime.now().strftime("%Y%m%d%H%M%S")) + ".txt"

            with open(file_name, "w", encoding="utf-8") as file:
                file.write(self.content)

            # S3 삽입 코드
            s3 = boto3.resource("s3")
            bucket_name = configuration.bucket_name
            bucket = s3.Bucket(bucket_name)

            local_file = file_name
            obj_file = file_name

            bucket.upload_file(local_file, obj_file)

            # S3 저장 파일 경로 삽입
            self.content = f"https://{configuration.bucket_name}.s3.amazonaws.com/{configuration.file_path}{file_name}"

        # 카테고리
        self.category = "UNDERGRADUATE"

        # 이미지
        self.image_url = []

        # 파일
        file_link = []

        contents = soup.find("table", class_="table").find_all("li")
        for content in contents:
            link_tag = content.find("a")

            if link_tag is not None and "href" in link_tag.attrs:
                file_link.append(AI_BASE_URL + link_tag["href"])

        self.file_url = file_link

        # 생성 시각
        created_date = list(map(int, childrens[2].text.split(".")))
        self.created_at = date(created_date[0], created_date[1], created_date[2])

        # 업데이트 시각
        self.updated_at = datetime.now().strftime("%Y-%m-%d")

        # 조회수
        self.views = childrens[3].text.strip()

        # 학과
        with engine.connect() as connect:
            department_table = Table(
                "department", metadata_obj, schema="main", autoload_with=engine
            )
            query = department_table.select().where(department_table.c.name == "AI융합학부")
            results = connect.execute(query)

            for result in results:
                self.department_id = result.id

    def __str__(self):
        return (
            "title: {0}\n"
            "content: {1}\n"
            "image_url: {2}\n"
            "file_url: {3}\n"
            "department_id: {4}".format(
                self.title,
                self.content,
                self.image_url,
                self.file_url,
                self.department_id,
            )
        )


def ai_department_crawling():
    try:
        page = 1
        url = AI_BASE_URL + "notice.html?searchKey=ai"
        # 페이지 옵션: &page=
        req = requests.get(url)
        soup = BeautifulSoup(req.text, "lxml")
        content = soup.find("table", class_="table")
        rows = content.find_all("tr")
        results = []

        for row in rows[1:]:
            results.append(AiNotification(row))

        notification_table = Table(
            "notice", "metadata_obj", schema="notice", autoload_with=engine
        )

        with session_maker() as session:
            for result in results:
                update_notification = ("CSE", result, session, s3, notification_table)

            session.commit()

    except:
        return JSONResponse(content="Internal Server Error", status_code=500)

    return JSONResponse(content="OK", status_code=200)


if __name__ == "__main__":
    ai_department_crawling()
