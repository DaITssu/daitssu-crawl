from bs4 import BeautifulSoup
import requests
from datetime import datetime
import psycopg2
import dev_db

# 데이터베이스에 연결 설정
conn = psycopg2.connect(
    host=dev_db.dev_host,
    database=dev_db.dev_db_name,
    user=dev_db.dev_user_name,
    password=dev_db.dev_db_pw,
    port=5432,
)
cursor = conn.cursor()


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
        img_style = data.find("div", {"class": "cover"})["style"]
        strat = img_style.index("(") + 1
        end = img_style.index(")")
        image_url = img_style[strat:end]

        #생성시각 및 업데이트 시각 크롤링.
        created_time_element = data_link.find("span", {"class": "created-time"})
        if created_time_element:
            created_at = created_time_element.get_text(strip=True)
        else:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
                    content += f"Image: {img_src}\n"
                elif tag.find("a"):
                    link_tag = tag.find("a")
                    link_href = link_tag["href"]
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
                content += "Table Contents:\n"
                for row in tag.find_all("tr"):
                    row_contents = [
                        cell.get_text(strip=True) for cell in row.find_all("td")
                    ]
                    content += "\t/ ".join(row_contents) + "\n"

        #DB INSERT
        cursor.execute(
            f"""
            INSERT INTO notice.notice_fs (title, content, image_url, url, created_at, updated_at,category)
            VALUES ('{title}', '{content}', '{{image_url}}','{content_url}', '{created_at}', '{updated_at}','{category}')
            """,
        )

        conn.commit()

    # 데이터베이스 연결 닫기
    conn.close()


if __name__ == "__main__":
    fun_system_crawling(1)
