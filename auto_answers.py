from src.tool import *
from src.chapter import *
from src.config import GlobalConst as gc
from src.cookies import *
from src.answer import *
API = ''
Base_URL = ''

def get_api() :
    return API
def get_base_url() :
    return Base_URL

if __name__ == '__main__':

    # 初始化登录信息
    username, password, course_list ,Use_Ai, API, Base_URL= init_config()
    print(API)
    print(Base_URL)
    driver = init_driver()
    # 等待弹出登录窗口，并输入账号（手机号）
    wait = WebDriverWait(driver, 10)  # 等待最多10秒


    # 打开chaoxing网页
    driver.get("http://www.chaoxing.com")

    while True:
        try:
            # 查找并点击登录按钮
            wait.until(EC.element_to_be_clickable((By.LINK_TEXT, '登录'))).click()
            break
        except ElementClickInterceptedException:
            pass


    wait.until(EC.visibility_of_element_located((By.ID, 'phone'))).send_keys(username)

    # 等待并输入密码
    wait.until(EC.visibility_of_element_located((By.ID, 'pwd'))).send_keys(password)

    login(username, password)
    # 点击登录
    loginBtn = wait.until(EC.element_to_be_clickable((By.ID, 'loginBtn')))
    print(loginBtn.get_attribute('id'))
    loginBtn.click()

    # 等待特定元素出现，确认新页面已加载
    # 等待某个特定元素出现，这里以课程ID为例，假设它是新页面上最后加载的元素之一
    iframe = wait.until(EC.presence_of_element_located((By.ID, 'frame_content')))

    print(iframe.get_attribute('id'))
    driver.switch_to.frame(iframe)

    #获取所有课程信息
    courses=wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.course.clearfix')))


    #定义要筛选的courseid
    #target_courseid = course_list

    # 遍历所有课程元素，找到具有特定courseid的元素
    for course in courses:
        #print(course.text)
        # 获取元素的courseid属性
        courseid = str(course.get_attribute("courseid"))
        # 切换到新窗口，假设新窗口是列表中的最后一个
        #driver.switch_to.window(window_handles[0])
        #print(courseid)
        course_isfinished= False
        if courseid in course_list:

            print(f"已找到课程ID：{courseid}，准备进入学习......")

        #     # 找到了具有特定courseid的元素
        #     # 执行所需的操作，例如点击或获取信息
        #     # 例如，点击该课程的链接
        #一个一个课程查看
            course.find_element(By.TAG_NAME, "a").click()
            # 获取所有窗口句柄
            window_handles = driver.window_handles

            # 切换到新窗口，假设新窗口是列表中的最后一个
            driver.switch_to.window(window_handles[-1])
            #点击进入章节
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'a[title="章节"]'))).click()
            #主逻辑
            driver.switch_to.frame(wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,f"iframe[src*='{course_list}']"))))
            chapter=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,f"div.chapter_item[onclick*='{course_list}']")))
            print(chapter.get_attribute('title'))
            chapter.click()
            #切回主文档
            driver.switch_to.default_content()
            s=wait.until(EC.presence_of_element_located((By.ID, 'iframe')))


            print(s.get_attribute('id'))

            course=Course(driver,course_list)
            chapters_title=course.get_chapters()
            for i in chapters_title:
                driver.switch_to.default_content()

                #在每次操作前重新获取元素引用
                try:
                    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,f"{course.chapter_class}[title='{i}']"))).click()

                except StaleElementReferenceException:
                    chapter_element = wait.until(EC.presence_of_element_located((By.ID, 'content1')))
                    # 计算章节元素的位置
                    location = chapter_element.location
                    size = chapter_element.size

                    # 移动到章节元素的中心位置
                    driver.execute_script("arguments[0].scrollIntoView(true);", chapter_element)
                    # 模拟鼠标滚轮向下滚动操作
                    # 注意：量值可能需要根据实际情况调整
                    scroll_script = f"""
                    var element = arguments[0];
                    var scrollAmount = 200; // 向下滚动元素自身的高度
                    element.scrollTop += scrollAmount;
                    """
                    driver.execute_script(scroll_script, chapter_element)


                    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"{course.chapter_class}[title='{i}']"))).click()
                except TimeoutException:
                    chapter_element = wait.until(EC.presence_of_element_located((By.ID, 'content1')))
                    # 计算章节元素的位置
                    location = chapter_element.location
                    size = chapter_element.size

                    # 移动到章节元素的中心位置
                    driver.execute_script("arguments[0].scrollIntoView(true);", chapter_element)

                    # 模拟鼠标滚轮向下滚动操作
                    # 注意：量值可能需要根据实际情况调整
                    scroll_script = f"""
                    var element = arguments[0];
                    var scrollAmount = 200; // 向下滚动元素自身的高度
                    element.scrollTop += scrollAmount;
                    """
                    driver.execute_script(scroll_script, chapter_element)
                    try:
                        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"{course.chapter_class}[title='{i}']"))).click()
                    except TimeoutException:
                        continue
                except ElementClickInterceptedException :
                    continue
                    #wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"{course.chapter_class}[title='{i}']"))).click()

                #每个章节名称
                print(i)
                #time.sleep(0.5)

                #进入主iframe1,每个章节对应一个主iframe
                while True:
                    try:
                        iframe1 = wait.until(EC.presence_of_element_located((By.ID,'iframe')))
                        # # #print(iframe1.get_attribute('id'))
                        driver.switch_to.frame(iframe1)
                        break
                    except TimeoutException :
                        pass
                    except StaleElementReferenceException:
                        pass

                #iframe2 = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'iframe')))
                #获取本章节的所有内容
                iframe2_list = course.get_iframe()
                #print(iframe2_list)
                if iframe2_list == None:

                    continue
                for j in iframe2_list:
                    print(j)
                    try:
                        #此处需要优化一下匹配，复杂度太高
                        iframe2=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"iframe[data*='{j}']")))
                        data=json.loads(iframe2.get_attribute('data'))
                        print(data)
                        print(data.get('name',None))
                        #获取该视频的objectid(只有视频才有objectid)
                        video_objectid=iframe2.get_attribute('objectid')


                    except StaleElementReferenceException:
                        continue

                    except NoSuchElementException:
                        continue
                    except TimeoutException:
                        continue



                    #此处进入第二个iframe，执行完应该退出该iframe
                    driver.switch_to.frame(iframe2)

                    if "pdf" in data.get('name', '0'):
                        print("pdf ")
                        driver.switch_to.parent_frame()
                    elif "ppt" in data.get('name','0'):
                        print("pptx ")
                        driver.switch_to.parent_frame()
                    elif "doc" in data.get('name','0'):
                        print("doc")
                        driver.switch_to.parent_frame()
                    elif "docx" in data.get('name','0'):
                        print("docx")
                        driver.switch_to.parent_frame()

                    # 处理章节测验
                    elif data.get('name', None) == None:
                        print("章节测验")
                        if Use_Ai == '0' :
                            driver.switch_to.parent_frame()
                            print("跳过该题目")
                            continue
                        #获取题目表单
                        form_data,test_question_url=course.get_test_questions()
                        print(form_data)

                        #填写答案
                        complete_answer(driver, form_data,test_question_url,j)
                        # 返回两次，回到第一个iframe
                        driver.switch_to.parent_frame()
                        driver.switch_to.parent_frame()
                    # 处理视频文件
                    elif course.get_video_playing() is not None:
                        driver.switch_to.parent_frame()
                        #检验视频任务点是否完成
                        try:
                            # 使用 JavaScript 获取 iframe 的 parentNode
                            iframe_parent_script = """
                            var iframe = arguments[0];
                            return iframe.parentNode;
                            """
                            iframe_parent = driver.execute_script(iframe_parent_script, iframe2)

                            # 在 iframe 的父节点中查找特定的 div 元素
                            target_div_script = """
                            var iframeParent = arguments[0];
                            return iframeParent.querySelector(".ans-job-icon-clear");
                            """
                            target_div = driver.execute_script(target_div_script, iframe_parent)

                            # 现在你可以对 target_div 进行操作，例如获取属性或文本
                            print(target_div.get_attribute('aria-label'))

                        except NoSuchElementException:
                            print(f"该任务点异常，跳过此任务点......")

                        #若完成，则跳过
                        if target_div.get_attribute('aria-label') == "任务点已完成":
                            # 现在你可以对 target_div 进行操作，例如获取属性或文本
                            print(f"{target_div.get_attribute('aria-label')}，跳过该任务点......")
                            continue

                        #进入主ifram1的iframe2
                        driver.switch_to.frame(iframe2)

                        print(course.get_video_playing().get_attribute('title'))

                        #点击播放按钮
                        course.get_video_playing().click()

                        #获取视频总时长
                        duration = get_video_durations(video_objectid)

                        #学习视频
                        study_video(driver, data.get('name'), duration)

                        # 返回到第一个iframe
                        driver.switch_to.parent_frame()
                    else :
                        print("其他类型文件")

                #需要跳转到下一个章节
                driver.switch_to.default_content()

                try:
                    wait.until(EC.presence_of_element_located((By.ID, 'prevNextFocusNext'))).click()
                    #driver.switch_to.default_content()
                    pre_next_button = driver.find_element(By.CSS_SELECTOR,'a.jb_btn[onclick*="PCount.next"]')
                    pre_next_button.click()
                except NoSuchElementException:
                    #print("下一节按钮找不到")
                    pass

            # 该课程已全部学习
            course_isfinished = True

        if course_isfinished:
            print(f"课程ID：{courseid}，该课程已学习完毕！")



    driver.close()

