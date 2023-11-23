from bs4 import BeautifulSoup
import requests
from datetime import datetime
import psycopg2
import configuration
<<<<<<< HEAD
import boto3
from enum import Enum 

# 데이터베이스에 연결 설정
conn = psycopg2.connect(
    host=configuration.db_host,
    database=configuration.db_name,
    user=configuration.db_user_name,
    password=configuration.db_pw,
    port=5432,
)
cursor = conn.cursor()
=======

from fastapi.responses import JSONResponse

def do_fun_system_crawling():
>>>>>>> 397c3afe786a09a799a06bd937f36f5e6960aeb5

# S3 클라이언트 생성
s3 = boto3.client(
    's3',
    aws_access_key_id=configuration.aws_access_key_id,
    aws_secret_access_key=configuration.aws_secret_access_key
)

<<<<<<< HEAD
class Category(Enum):
    전체 = "ALL"
    구독 = "SUBSCRIPTION"
    학습역량 = "LEARNING_SKILLS"
    공모전 = "COMPETITION"
    경진대회 = "COMPETITION"
    자격증 = "CERTIFICATION"
    특강 = "CERTIFICATION"
    학생활동 = "STUDENT_ACTIVITIES"
    해외연수 = "STUDY_ABROAD"
    교환학생 = "STUDY_ABROAD"
    인턴 = "INTERNSHIP"
    봉사 = "VOLUNTEERING"
    체험활동 = "EXPERIENTIAL_ACTIVITIES"
    심리 = "COUNSELING"
    상담 = "COUNSELING"
    진단 = "COUNSELING"
    진로지원 = "CAREER_SUPPORT"
    창업지원 = "STARTUP_SUPPORT"
    취업지원 = "EMPLOYMENT_SUPPORT"
=======
    # 데이터베이스에 연결 설정
    conn = psycopg2.connect(
        host=configuration.db_host,
        database=configuration.db_name,
        user=configuration.db_user_name,
        password=configuration.db_pw,
        port=5432,
    )

    cursor = conn.cursor()
>>>>>>> 397c3afe786a09a799a06bd937f36f5e6960aeb5


class CrawlingFinishedException(Exception):
    pass

# 해시맵 초기화
title_hashmap = set()

def fun_system_crawling(page_count):
    try:
        for page_number in range(1, page_count + 1):
            # 웹 페이지에서 프로그램 정보 가져오기
            Fun = f"https://fun.ssu.ac.kr/ko/program/all/list/all/{page_number}"
            html = requests.get(Fun)
            html_text = html.text
            soup = BeautifulSoup(html_text, "html.parser")
            tag_ul = soup.find("ul", {"class": "columns-4"})

            for data in tag_ul.find_all("li"):
                #마감된 프로그램인지 확인하기 closed 혹은 schesuled이면 넘어감.
                label = data.select_one("label").get_text()

                if "마감" in label:
                    pass
                elif "예정" in label:
                    pass
                else:
                    raise CrawlingFinishedException()

                #title 크롤링
                title = data.select_one("b.title").get_text()

                # 중복된 title 체크
                if title in title_hashmap:
                    continue  # 이미 크롤링한 title이면 무시

                # title을 해시맵에 추가
                title_hashmap.add(title)


                # DB에서 이미 저장된 데이터의 title 조회
                cursor.execute(f"SELECT title FROM notice.notice_fs WHERE title = '{title}'")
                existing_title = cursor.fetchone()

                # 이미 저장된 데이터의 title과 크롤링 중인 데이터의 title이 동일하면 넘어감
                if existing_title:
                    continue


                #image_url 크롤링
                data_link = data.find("a")
                image = []

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
                content = wysiwyg_content.text

                for tag in wysiwyg_content(["p", "table"]):
                    if tag.name == "p":
                        # 이미지, 링크, 동영상인 경우
                        if tag.find("img"):
                            img_src = tag.find("img")["src"]
                            image.append(img_src)

                # category 크롤링.
                target = soup_content.find("div", {"class": "info"})
                category_element = target.find("div", {"class": "category"})
                i_tag = category_element.find('i', class_='fa fa-angle-right')
                if i_tag:
                    category_text = i_tag.find_previous_sibling(string=True).strip()
                else:
                    category_text = category_element.get_text(strip=True)

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
                    INSERT INTO notice.notice_fs (title, content, image_url, url, created_at, updated_at, category, views)
                    VALUES ('{title}', '{"https://daitssu-bucket.s3.amazonaws.com/daitssu-dev/"+content_file}', ARRAY[{image}]::text[],'{content_url}', '{created_at}', '{updated_at}','{category}','{views}')
                    """,
                )

                conn.commit()

    except CrawlingFinishedException:
        pass
    finally:
        # 데이터베이스 연결 닫기
        conn.close()

def fun_system_crawling():
    try:
        do_fun_system_crawling()
    except:
        return JSONResponse(content="Internal Server Error", status_code=500)
    
    return JSONResponse(content="OK", status_code=200)


if __name__ == "__main__":
<<<<<<< HEAD
    fun_system_crawling(10)
=======
    fun_system_crawling()
>>>>>>> 397c3afe786a09a799a06bd937f36f5e6960aeb5
