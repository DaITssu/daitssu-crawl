from bs4 import BeautifulSoup
import requests
from datetime import datetime
import psycopg2
import configuration

from fastapi.responses import JSONResponse

def do_fun_system_crawling():

    # 웹 페이지에서 프로그램 정보 가져오기
    Fun = "https://fun.ssu.ac.kr/ko/program"
    html = requests.get(Fun)
    html_text = html.text
    soup = BeautifulSoup(html_text, "html.parser")
    tag_ul = soup.find("ul", {"class": "columns-4"})

    # 데이터베이스에 연결 설정
    conn = psycopg2.connect(
        host=configuration.db_host,
        database=configuration.db_name,
        user=configuration.db_user_name,
        password=configuration.db_pw,
        port=5432,
    )

    cursor = conn.cursor()


    # 각 프로그램 정보를 크롤링하여 데이터베이스에 삽입
    for data in tag_ul.find_all("li"):
        data_title = data.select_one("b.title").get_text()
        data_link = data.find("a")
        img_style = data.find("div", {"class": "cover"})["style"]
        strat = img_style.index("(") + 1
        end = img_style.index(")")
        image = img_style[strat:end]
        created_time_element = data_link.find("span", {"class": "created-time"})

        if created_time_element:
            created_time = created_time_element.get_text(strip=True)
        else:
            created_time = None

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 프로그램 내용 가져오기 (이전 내용 유지)
        content_url = "https://fun.ssu.ac.kr" + data_link.get("href")
        html_content = requests.get(content_url)
        html_content_text = html_content.text
        soup_content = BeautifulSoup(html_content_text, "html.parser")
        content = ""

        for tag in soup_content.find_all(["p", "table"]):
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

        # 데이터 존재 여부 확인 및 업데이트 시각 설정
        cursor.execute(
            "SELECT * FROM programs WHERE url=%s",
            ("https://fun.ssu.ac.kr" + data_link.get("href"),),
        )
        existing_data = cursor.fetchone()

        if existing_data:
            updated_time = current_time
            cursor.execute(
                """
                UPDATE programs
                SET updated_time=%s, content=%s
                WHERE url=%s
            """,
                (updated_time, content, "https://fun.ssu.ac.kr" + data_link.get("href")),
            )
        else:
            updated_time = None
            cursor.execute(
                """
                INSERT INTO programs (title, url, image_url, created_time, updated_time, content)
                VALUES (%s, %s, %s, %s, %s, %s)
            """,
                (
                    data_title,
                    "https://fun.ssu.ac.kr" + data_link.get("href"),
                    "https://fun.ssu.ac.kr" + image,
                    created_time,
                    updated_time,
                    content,
                ),
            )

        conn.commit()

    # 데이터베이스 연결 닫기
    conn.close()


def fun_system_crawling():
    try:
        do_fun_system_crawling()
    except:
        return JSONResponse(content="Internal Server Error", status_code=500)
    
    return JSONResponse(content="OK", status_code=200)


if __name__ == "__main__":
    fun_system_crawling()
