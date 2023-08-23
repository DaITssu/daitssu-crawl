import requests
import psycopg2
import dev_db


class SmartCampus:
    color_list = ['FF8DC4', 'FF7171', 'FF9E68', 'FFD057', 'B7E532', '35CC7B', '73E4DE', '6197FF', 'B69BE3', 'A48172']
    over_color = 'BDBDBD'

    conn = psycopg2.connect(
        host=dev_host,
        database=dev_db_name,
        user=dev_user_name,
        password=dev_db_pw,
        port=5432,
    )
    print(conn)
    cursor = conn.cursor()

    # 사용자에게 스키마 또는 테이블에 대한 권한 부여
    cursor.execute("GRANT ALL PRIVILEGES ON SCHEMA public TO your_user;")
    cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;")


    def create_data_table(self):
        # smart_campus_data 테이블 생성 쿼리 실행
        create_data_table_query = """
            CREATE TABLE IF NOT EXISTS smart_campus_data (
                id SERIAL PRIMARY KEY,
                course_id INTEGER UNIQUE NOT NULL,
                course_title TEXT NOT NULL,
                attendance_status TEXT,
                unlock_at TIMESTAMP,
                due_at TIMESTAMP,
                late_at TIMESTAMP,
                video_url TEXT,
                color_code TEXT NOT NULL
            )
        """
        self.cursor.execute(create_data_table_query)
        self.conn.commit()

    def save_subject_data(self, course_id, course_title, attendance_status, unlock_at, due_at, late_at, video_url,
                          color_code):
        # 과목 정보를 smart_campus_data 테이블에 저장
        insert_query = """
            INSERT INTO smart_campus_data (course_id, course_title, attendance_status, unlock_at, due_at, late_at, video_url, color_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        data = (course_id, course_title, attendance_status, unlock_at, due_at, late_at, video_url, color_code)
        self.cursor.execute(insert_query, data)
        self.conn.commit()

    def get_subject(self, token):
        # 학기 중인 과목 정보 받아와서 테이블에 저장
        url = "https://canvas.ssu.ac.kr/learningx/api/v1/learn_activities/courses?term_ids[]=26"
        headers = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)
        cnt = 1
        if response.status_code == 200:
            data = response.json()
            for module in data:
                course_title = module["name"]
                course_id = module["id"]
                color_code = self.color_list[cnt - 1] if cnt < 11 else self.over_color
                self.save_subject_data(course_id, course_title, '', None, None, None, '', color_code)
                cnt += 1

    def get_attendance_data(self, token, subject_num):
        # 과목의 출결 정보 받아와서 테이블에 저장
        subject = subject_num
        url = f"https://canvas.ssu.ac.kr/learningx/api/v1/courses/{subject}/attendance_items/summary?only_use_attendance=true"
        headers = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            attendance_statuses = data['attendance_summaries']
            for item_id, attendance in attendance_statuses.items():
                attendance_status = attendance['attendance_status']
                self.save_subject_data(subject_num, '', attendance_status, None, None, None, '', '')
        else:
            print("요청에 실패했습니다. 응답 코드:", response.status_code)

    def get_date(self, token, subject_num):
        # 과목의 날짜 정보(강의 및 과제 기한) 받아와서 테이블에 저장
        subject = subject_num
        url = f"https://canvas.ssu.ac.kr/learningx/api/v1/courses/{subject}/modules?include_detail=true"
        headers = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for module in data:
                module_items = module["module_items"]
                for item in module_items:
                    title = item["title"]
                    if item["content_type"] == "attendance_item":
                        unlock_at = item["content_data"]["unlock_at"]
                        due_at = item["content_data"]["due_at"]
                        late_at = item["content_data"]["late_at"]
                        video_url = item["content_data"]["item_content_data"]["view_url"]
                        self.save_subject_data(subject_num, '', '', unlock_at, due_at, late_at, video_url, '')
                    elif item["content_type"] == "assignment":
                        unlock_at = item["content_data"]["unlock_at"]
                        due_at = item["content_data"]["due_at"]
                        self.save_subject_data(subject_num, '', '', unlock_at, due_at, None, '', '')

    def close_connection(self):
        self.cursor.close()
        self.conn.close()
