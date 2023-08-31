from django.db import models
import requests

class SmartCampusData(models.Model): # 과목 정보를 받아오고 과목 코드에 따라 과목의 이름, 색상 코드 저장
    course_id = models.IntegerField(primary_key=True)
    course_title = models.CharField(max_length=255)
    color_code = models.CharField(max_length=10)

class AttendanceRecord(models.Model): # 과목 코드에 따라 출결 정보를 저장하는 레코드
    course = models.ForeignKey(SmartCampusData, on_delete=models.CASCADE)
    attendance_id = models.IntegerField()
    attendance_status = models.CharField(max_length=50)

class DateRecord(models.Model): # 과목 코드에 따라 강의 및 과제의 기한을 저장하는 레코드
    course = models.ForeignKey(SmartCampusData, on_delete=models.CASCADE)
    module_item_id = models.IntegerField(unique=True)
    module_item_title = models.CharField(max_length=255)
    unlock_at = models.DateTimeField(null=True)
    due_at = models.DateTimeField(null=True)
    late_at = models.DateTimeField(null=True)
    video_url = models.URLField(null=True)

class SmartCampus:
    color_list = ['FF8DC4', 'FF7171', 'FF9E68', 'FFD057', 'B7E532', '35CC7B', '73E4DE', '6197FF', 'B69BE3', 'A48172']
    over_color = 'BDBDBD'
    # 과목 코드에 따라 지정될 색상 코드
    def save_subject_data(self, course_id, course_title, color_code):
        SmartCampusData.objects.create(course_id=course_id, course_title=course_title, color_code=color_code)
        # 학기별로 수강중인 과목을 저장하는 함수

    def get_subject(self, token): # 토큰을 받아 해당 학기에 수강중인 과목의 과목 코드, 제목을 받고 색상코드를 부여하는 함수
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
                self.save_subject_data(course_id, course_title, color_code)
                cnt += 1

    def get_attendance_data(self, token, subject_num): # 과목 코드를 기준으로 출결 상태를 받아와 저장하는 함수
        subject = subject_num
        url = f"https://canvas.ssu.ac.kr/learningx/api/v1/courses/{subject}/attendance_items/summary?only_use_attendance=true"
        headers = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            attendance_statuses = data['attendance_summaries']
            for item_id, attendance in attendance_statuses.items():
                attendance_status = attendance['attendance_status']
                try:
                    existing_data = AttendanceRecord.objects.get(course__course_id=subject_num,
                                                                attendance_status=attendance_status, attendance_id=item_id)
                    pass
                except AttendanceRecord.DoesNotExist:
                    self.save_attendance_data(subject_num, item_id, attendance_status)
        else:
            print("요청에 실패했습니다. 응답 코드:", response.status_code)

    def save_attendance_data(self, course_id, item_id, attendance_status): # 출결상태를 레코드에 저장하는 함수
        course = SmartCampusData.objects.get(course_id=course_id)
        AttendanceRecord.objects.create(course=course, attendance_id=item_id, attendance_status=attendance_status)

    def get_date(self, token, subject_num): # 과목 코드에 따라 강의의 동영상 강의 url, 과제의 제출 및 마감 기한등을 받아오고 저장하는 함수
        subject = subject_num
        url = f"https://canvas.ssu.ac.kr/learningx/api/v1/courses/{subject}/modules?include_detail=true"
        headers = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for module in data:
                module_items = module["module_items"]
                for item in module_items:
                    module_item_id = item["module_item_id"]  # 모듈 아이템의 ID
                    title = item["title"]
                    if item["content_type"] == "attendance_item":
                        unlock_at = item["content_data"]["unlock_at"]
                        due_at = item["content_data"]["due_at"]
                        late_at = item["content_data"]["late_at"]
                        video_url = item["content_data"]["item_content_data"]["view_url"]
                        self.save_date_data(subject_num, title, module_item_id, unlock_at, due_at, late_at, video_url)
                    elif item["content_type"] == "assignment":
                        unlock_at = item["content_data"]["unlock_at"]
                        due_at = item["content_data"]["due_at"]
                        self.save_date_data(subject_num, title, module_item_id, unlock_at, due_at, None, None)

    def save_date_data(self, course_id, title, module_item_id, unlock_at, due_at, late_at, video_url): #받아온 데이터를 레코드에 추가하는 함수
        course = SmartCampusData.objects.get(course_id=course_id)
        DateRecord.objects.create(course=course, module_item_title = title, module_item_id=module_item_id,
                                  unlock_at=unlock_at, due_at=due_at, late_at=late_at, video_url=video_url)
