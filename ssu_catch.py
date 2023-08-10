import json
import requests
from bs4 import BeautifulSoup
from enum import Enum, auto
from datetime import date

URL = "https://scatch.ssu.ac.kr/%ea%b3%b5%ec%a7%80%ec%82%ac%ed%95%ad"


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
            "학사": Category.school,
            "장학": Category.scholarship,
            "국제교류": Category.international,
            "외국인유학생": Category.foreigner,
            "채용": Category.employment,
            "비교과·행사": Category.event,
            "교원채용": Category.faculty_recruitment,
            "봉사": Category.volunteer,
            "교직": Category.teaching_profession,
            "기타": Category.etc,
            "코로나19관련소식": Category.covid19
        }
        target = column.find('span', class_='label')
        self.category = category_dict.get(target.text.strip())

    def __init_title(self, column):  # 제목 크롤링
        target = column.findAll("span")[2]
        self.title = target.text.strip()

    def __init_department(self, column):  # 등록 부서 크롤링
        self.department = column.text.strip()

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
    for (idx, item) in enumerate(content_iterator):
        if idx % 2 == 0:
            content_list.append(Content(item.find('div')).to_dict())

    return json.dumps(content_list, indent=4)