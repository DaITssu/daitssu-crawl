
def fus_system_crawling(value):
    from bs4 import BeautifulSoup
    import requests
    from datetime import datetime

    Fun = "https://fun.ssu.ac.kr/ko/program"
    html = requests.get(Fun)
    html_text = html.text
    soup = BeautifulSoup(html_text, "html.parser")

    # class=columns-4 ul로 이동해 각 프로그램들에 접근
    # class=columns-4 -> 전체 프로그램 리스트
    tag_ul = soup.find("ul", {"class": "columns-4"})

    # 해당 페이지에 대한 프로그램 정보들 크롤링
    for data in tag_ul.find_all("li"):
        # 프로그램 제목
        data_title = data.select_one("b.title").get_text()
        print("제목: " + data_title)

        # 프로그램 게시글 url
        data_link = data.find("a")
        print("게시글url: " + "https://fun.ssu.ac.kr" + data_link.get("href"))

        # 프로그램 이미지
        img_url = soup.find("div", {"class": "cover"})
        img_style = img_url["style"]
        strat = img_style.index("(") + 1
        end = img_style.index(")")
        image = img_style[strat:end]
        print("이미지url: " + "https://fun.ssu.ac.kr" + image)

        #               프로그램 업데이트 시각

        created_time_element = data_link.find("span", {"class": "created-time"})

        if created_time_element:
            created_time = created_time_element.get_text(strip=True)
            print("웹 사이트 생성 시각:", created_time)
        else:
            print("웹 사이트 생성 시각 정보를 찾을 수 없습니다.")

        #                   (프로그램 호출 시각 출력)
        current_time = datetime.now()

        formatted_time = current_time.strftime("%Y.%m.%d(%a)")
        print(formatted_time)

        print()

        # 프로그램 내용
        content = "https://fun.ssu.ac.kr" + data_link.get("href")
        html_content = requests.get(content)
        html_content_text = html_content.text
        soup_content = BeautifulSoup(html_content_text, "html.parser")

        # 공지사항 내용
        for tag in soup_content.find_all(["p", "table"]):
            # p 태그인 경우
            if tag.name == "p":
                if tag.find("img"):
                    img_src = tag.find("img")["src"]
                    print(f"Image: {img_src}")

                # 첨부파일인 경우
                elif tag.find("a"):
                    link_tag = tag.find("a")
                    link_href = link_tag["href"]
                    link_text = link_tag.get_text(strip=True)
                    print(f"Link: {link_text} - {link_href}")

                # 동영상인 경우
                elif tag.find("iframe"):
                    link_tag = tag.find("iframe")
                    link_href = link_tag["src"]
                    link_text = link_tag.get_text(strip=True)
                    print(f"video Link: {link_text} - {link_href}")

                # 텍스트인 경우
                else:
                    text_content = tag.get_text(strip=True)
                    print(f"{text_content}")

            # table 태그인 경우
            elif tag.name == "table":
                print("Table Contents:")
                # 테이블 내의 각 행(<tr>)을 찾기
                for row in tag.find_all("tr"):
                    # 각 셀(<td>)의 내용을 출력
                    row_contents = [
                        cell.get_text(strip=True) for cell in row.find_all("td")
                    ]
                    # tab을 이용해서 표 출력
                    print("\t/ ".join(row_contents))

        print(
            "========================================================================================"
        )
        