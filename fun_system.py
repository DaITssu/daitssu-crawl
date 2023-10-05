from bs4 import BeautifulSoup
import requests
from datetime import datetime
import psycopg2
import configuration
import boto3

# 데이터베이스에 연결 설정
conn = psycopg2.connect(
    host=configuration.db_host,
    database=configuration.db_name,
    user=configuration.db_user_name,
    password=configuration.db_pw,
    port=5432,
)
cursor = conn.cursor()

# S3 클라이언트 생성
s3 = boto3.client(
    's3',
    aws_access_key_id=configuration.aws_access_key_id,
    aws_secret_access_key=configuration.aws_secret_access_key
)

def fun_system_crawling(value):

    # 웹 페이지에서 프로그램 정보 가져오기
    Fun = "https://fun.ssu.ac.kr/ko/program"
    html = requests.get(Fun)
    html_text = html.text
    soup = BeautifulSoup(html_text, "html.parser")
    tag_ul = soup.find("ul", {"class": "columns-4"})



    for data in tag_ul.find_all("li"):

        #title크롤링
        title = data.select_one("b.title").get_text()

        #image_url 크롤링
        data_link = data.find("a")
        image = []

        #생성시각 및 업데이트 시각 크롤링.
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

       #카테고리
        category = "펀시스템"

        # content 크롤링
        content_url = "https://fun.ssu.ac.kr" + data_link.get("href")
        html_content = requests.get(content_url)
        html_content_text = html_content.text
        soup_content = BeautifulSoup(html_content_text, "html.parser")
        content = ""

        wysiwyg_content = soup_content.find("div", {"data-role": "wysiwyg-content"})

        for tag in wysiwyg_content(["p", "table"]):
            if tag.name == "p":
                # 이미지, 링크, 동영상인 경우
                if tag.find("img"):
                    img_src = tag.find("img")["src"]
                    image.append(img_src)
                elif tag.find("a"):
                    link_tag = tag.find("a")
                    if "href" in link_tag.attrs:
                        link_href = link_tag["href"]
                    else:
                        link_href = ""
                    link_text = link_tag.get_text(strip=True)
                    content += f"Link: {link_text} - {link_href}\n"
                elif tag.find("iframe"):
                    link_tag = tag.find("iframe")
                    link_href = link_tag["src"]
                    link_text = link_tag.get_text(strip=True)
                    content += f"Video Link: {link_text} - {link_href}\n"
                else:
                    text_content = tag.get_text(strip=True)
                    content += f"{text_content}\n"

            elif tag.name == "table":
                for row in tag.find_all("tr"):
                    row_contents = []
                    for cell in row.find_all(["td", "th"]):
                        row_contents.append(cell.get_text(strip=True))
                    content += "\t/ ".join(row_contents) + "\n"

        content = content.replace("'", "''")


        # 문자열을 바이트로 인코딩하여 S3에 업로드
        s3.put_object(
            Bucket=configuration.bucket_name,
            Key=configuration.file_path,
            Body=content.encode('utf-8')
        )

        content = f'https: // s3.amazonaws.com / {configuration.bucket_name} / {configuration.file_path}'

        #DB INSERT
        cursor.execute(
            f"""
            INSERT INTO notice.notice_fs (title, content, image_url, url, created_at, updated_at, category, views)
            VALUES ('{title}', '{content}', ARRAY[{image}]::text[],'{content_url}', '{created_at}', '{updated_at}','{category}','{views}')
            """,
        )

        conn.commit()

    # 데이터베이스 연결 닫기
    conn.close()


if __name__ == "__main__":
    fun_system_crawling(1)
