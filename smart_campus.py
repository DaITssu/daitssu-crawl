import requests

class smart_campus:
    def get_attendence_data(token, subjectNum):
        subject = subjectNum
        print("과목코드 입력")
        url = "https://canvas.ssu.ac.kr/learningx/api/v1/courses/"+subject+"/attendance_items/summary?only_use_attendance=true"


        headers = {
            "Authorization": "Bearer " + token
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            attendance_statuses = data['attendance_summaries']
            for item_id, attendance in attendance_statuses.items():
                attendance_status = attendance['attendance_status']
                if attendance_status =="attendance":
                    print(f"출결상태: 출석")
                elif attendance_status =="late":
                    print(f"출결상태: 지각")
                else:
                    print(f"출결상태: 결석")
        else:
            print("요청에 실패했습니다. 응답 코드:", response.status_code)

    def get_subject(token):
        url = "https://canvas.ssu.ac.kr/learningx/api/v1/learn_activities/courses?term_ids[]=26"

        headers = {
            "Authorization": "Bearer " + token
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            for module in data:
                course_title = module["name"]
                course_id = module["id"]
                if (cnt < 11):
                    course_dict[course_id] = color_list[cnt - 1]
                else:
                    course_dict[course_id] = over_color
                cnt += 1
                print(f"수강중인 과목 이름 : {course_title} \n과목 id : {course_id}")
                print("-------------------------------------------------------------------------------------------")
        else:
            print("요청에 실패했습니다. 응답 코드:", response.status_code)

    def get_date(token, subjectNum):
        subject = subjectNum
        url = "https://canvas.ssu.ac.kr/learningx/api/v1/courses/" + subject + "/modules?include_detail=true"

        headers = {
            "Authorization": "Bearer " + token
        }

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
                        if late_at is None:
                            if video_url == "":
                                print(f"{title} \n시작: {unlock_at} 마감: {due_at}")
                                print("-----------------------------------------------------------------------")
                            else:
                                print(f"{title} \n시작: {unlock_at} 마감: {due_at}\n영상 url: {video_url}")
                                print("-----------------------------------------------------------------------")
                        else:
                            if video_url == "":
                                print(f"{title} \n시작: {unlock_at} 마감: {due_at} 지각: {late_at}")
                                print("-----------------------------------------------------------------------")
                            else:
                                print(f"{title} \n시작: {unlock_at} 마감: {due_at} 지각: {late_at}\n영상 url: {video_url}")
                                print("-----------------------------------------------------------------------")
                    elif item["content_type"] == "assignment":
                        unlock_at = item["content_data"]["unlock_at"]
                        due_at = item["content_data"]["due_at"]
                        print(f"{title} \n과제 시작일 {unlock_at} 종료일 {due_at}")
                        print("-----------------------------------------------------------------------")
        else:
            print("요청에 실패했습니다. 응답 코드:", response.status_code)
