import requests

class smart_campus:
    color_list = ['FF8DC4', 'FF7171', 'FF9E68', 'FFD057', 'B7E532', '35CC7B', '73E4DE', '6197FF', 'B69BE3', 'A48172'] #과목별로 짝지어질 색상코드
    over_color = 'BDBDBD' #11개 이상의 과목을 받아오는 경우 모두 회색의 색상을 중복으로 부여받기에 11개 이상이 되었을 때 과목과 짝지어질 색상의 코
    course_dict = {} #아래의 과목 코드를 받아오는 함수에서 받아온 과목코드와 색상 코드를 묶어서 저장할 dictionary
    
    def get_subject(token): #토큰을 받아 학기에 수강 중인 과목의 이름과 과목 코드를 출력하는(받아오는) 함수
        url = "https://canvas.ssu.ac.kr/learningx/api/v1/learn_activities/courses?term_ids[]=26"

        headers = {
            "Authorization": "Bearer " + token
        }

        response = requests.get(url, headers=headers)
        cnt = 1
        if response.status_code == 200:
            data = response.json()
            for module in data:
                course_title = module["name"]
                course_id = module["id"]
                if (cnt < 11): #받아온 과목의 수가 10개 이하라면 color_list에 저장된 색상 코드를 순서대로 받아와 과목 코드와 묶어 저장
                    course_dict[course_id] = color_list[cnt - 1]
                else: #이후 과목이 11개 이상이 된다면 이후의 모든 과목의 짝지어질 색상을 회색의 색상코드로 묶는다
                    course_dict[course_id] = over_color
                cnt += 1
                print(f"수강중인 과목 이름 : {course_title} \n과목 id : {course_id}")
                print("-------------------------------------------------------------------------------------------")
        else:
            print("요청에 실패했습니다. 응답 코드:", response.status_code)

    

    def get_attendence_data(token, subjectNum): #토큰과 과목 코드를 전달 받음으로 보고자하는 과목의 출결 상태를 출력하는(받아오는) 함수
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

    
    def get_date(token, subjectNum): #토큰과 과목코드를 전달 받음으로 해당 과목의 동영상 강의의 기한과 url, 혹은 과제의 기한을 출력하는(받아오는) 함수
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
