from apscheduler.schedulers.background import BackgroundScheduler

# import notice.ai
import notice.computer
import notice.ssu_catch
import fun_system.fun_system

def test():
    print("start")
    # notice.ai.ai_department_crawling()
    notice.computer.computer_department_crawling()
    notice.ssu_catch.ssu_catch_crawling()
    fun_system.fun_system.fun_system_crawling()
    print("end")
    

scheduler = BackgroundScheduler(daemon=True, timezone='Asia/Seoul')
scheduler.add_job(test, 'cron', hour='0', minute='10')

def start_scheduling():
    scheduler.start()