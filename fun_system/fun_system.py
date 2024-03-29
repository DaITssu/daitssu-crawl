import json
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import mysql.connector
import configuration
import boto3
from enum import Enum

# 데이터베이스에 연결 설정
conn = mysql.connector.connect(
    user=configuration.db_user_name,
    password=configuration.db_pw,
    host=configuration.db_host,
    database=configuration.db_name
)

cursor = conn.cursor()

# S3 클라이언트 생성
s3 = boto3.client(
    's3',
    aws_access_key_id=configuration.aws_access_key_id,
    aws_secret_access_key=configuration.aws_secret_access_key
)

class Category(Enum):
    전체 = "ALL"
    구독 = "SUBSCRIPTION"
    학습역량 = "LEARNING_SKILLS"
    공모전_경진대회 = "COMPETITION"
    자격증_특강 = "CERTIFICATION"
    학생활동 = "STUDENT_ACTIVITIES"
    해외연수_교환학생 = "STUDY_ABROAD"
    인턴 = "INTERNSHIP"
    봉사 = "VOLUNTEERING"
    체험활동 = "EXPERIENTIAL_ACTIVITIES"
    심리_상담_진단 = "COUNSELING"
    진로_진학_지원 = "CAREER_SUPPORT"
    창업지원 = "STARTUP_SUPPORT"
    취업지원 = "EMPLOYMENT_SUPPORT"


# 해시맵 초기화
title_hashmap = set()

def fun_system_crawling(page_count):
    for page_number in range(1, page_count + 1):
        # 웹 페이지에서 프로그램 정보 가져오기
        Fun = f"https://fun.ssu.ac.kr/ko/program/all/list/all/{page_number}"
        html = requests.get(Fun)
        html_text = html.text
        soup = BeautifulSoup(html_text, "html.parser")
        tag_ul = soup.find("ul", {"class": "columns-4"})

        for data in tag_ul.find_all("li"):
            #마감된 프로그램인지 확인하기 closed 혹은 schesuled이면 크롤링 중단.
            label = data.select_one("label").get_text()

            if "마감" in label:
                continue
            elif "예정" in label:
                continue

            #title 크롤링
            title = data.select_one("b.title").get_text()

            # 중복된 title 체크
            if title in title_hashmap:
                continue  # 이미 크롤링한 title이면 무시

            # title을 해시맵에 추가
            title_hashmap.add(title)


            # DB에서 이미 저장된 데이터의 title 조회
            cursor.execute(f"SELECT title FROM daitssu.notice_fs WHERE title = '{title}'")
            existing_title = cursor.fetchone()

            # 이미 저장된 데이터의 title과 크롤링 중인 데이터의 title이 동일하면 넘어감
            if existing_title:
                continue


            #image_url 크롤링
            data_link = data.find("a")
            image = {"url": []}

            # 생성시각 및 업데이트 시각 크롤링.
            created_time_element = data_link.find("span", {"class": "created-time"})
            if created_time_element:
                created_at = created_time_element.get_text(strip=True)
            else:
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # views 크롤링.
            views_label = data.find("span", {"class": "hit"})
            views_text = views_label.get_text(strip=True)
            views = int(''.join(filter(str.isdigit, views_text)))

            # content 크롤링
            content_url = "https://fun.ssu.ac.kr" + data_link.get("href")
            html_content = requests.get(content_url)
            html_content_text = html_content.text
            soup_content = BeautifulSoup(html_content_text, "html.parser")

            wysiwyg_content = soup_content.find("div", {"data-role": "wysiwyg-content"})
            content = wysiwyg_content

            for tag in wysiwyg_content(["p", "table"]):
                if tag.name == "p":
                    # 이미지, 링크, 동영상인 경우
                    if tag.find("img"):
                        img_src = tag.find("img")["src"]
                        image["url"].append(img_src)

            # category 크롤링.
            target = soup_content.find("div", {"class": "info"})
            category_element = target.find("div", {"class": "category"})
            i_tag = category_element.find('i', class_='fa fa-angle-right')
            if i_tag:
                category_text = i_tag.find_previous_sibling(string=True).strip()
            else:
                category_text = category_element.get_text(strip=True)

            # "/"와 "("와 ")" 를 "_"로 대체
            category_text = category_text.replace("(", "_").replace(")", "_").replace("/", "_")
            category = Category[category_text].value

            content_file = "notice_fs/FUN" + datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"
            s3_key = content_file

            # 문자열을 바이트로 인코딩하여 S3에 업로드
            s3.put_object(
                Body=content.encode('utf-8'),
                Bucket=configuration.bucket_name,
                Key=s3_key
            )

            # DB INSERT
            cursor.execute(
                f"""
                INSERT INTO notice_fs (title, content, image_url, url, created_at, updated_at, category, views)
                VALUES ('{title}', '{"https://daitssu-bucket.s3.amazonaws.com/daitssu-dev/" + content_file}',
                        '{json.dumps(image)}', '{content_url}', '{created_at}', '{updated_at}', '{category}', '{views}')
                """
            )

            conn.commit()

    conn.close()

if __name__ == "__main__":
    fun_system_crawling(10)
