from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import *
import time
import sys
import requests
from requests.adapters import HTTPAdapter

import json
import argparse
import configparser
import pyautogui
from paddleocr import PaddleOCR
from PIL import Image
from collections import defaultdict

from src.chapter import *
from src.config import GlobalConst as gc
from src.cookies import *
from src.answer import *

#初始化配置命令行参数
def init_config() :
    parser = argparse.ArgumentParser(description='Samueli924/chaoxing')
    parser.add_argument('-c','--config',type=str,default=None, help='使用配置文件')
    parser.add_argument('-u','--username',type=str,default=None, help='配置用户参数')
    parser.add_argument('-p','--password',type=str,default=None, help='配置密码参数1')
    parser.add_argument("-l", "--list", type=str, default=None, help="要学习的课程ID列表")
    parser.add_argument("-t", "--TiKu", type=str, default=None, help="使用AI")
    parser.add_argument("-api", "--api", type=str, default=None, help="API")
    parser.add_argument("-url", "--url", type=str, default=None, help="URL")
    #parser.add_argument("-s", "--speed", type=float, default=1.0, help="视频播放倍速(默认1，最大2)")

    args = parser.parse_args()
    if args.config :
        config = configparser.ConfigParser()
        config.read(args.config, encoding="utf8")
        reload_api(str(config.get("TiKu", "api")),str(config.get("TiKu", "url")))
        return (config.get("common", "username"),
                config.get("common", "password"),
                str(config.get("common", "course_list")),
                str(config.get("TiKu", "Use_Ai")),
                str(config.get("TiKu", "api")),
                str(config.get("TiKu", "url")))
    else:
        reload_api(args.api, args.url)
        return (args.username, args.password, args.list, args.TiKu, args.api, args.url)


#初始化web网页驱动
def init_driver() :
    # 设置Edge选项
    options = Options()
    options.use_chromium = True
    options.add_experimental_option("detach", True)  # 添加这行代码

    # 指定驱动程序路径
    service = Service(executable_path='driver/msedgedriver.exe')

    # 创建Edge浏览器实例
    driver = webdriver.Edge(service=service, options=options)
    return driver


#登录chaoxing，截获cookie
def login(username, password):
    _session = requests.session()
    _url = "https://passport2.chaoxing.com/fanyalogin"
    _data = {"fid": "-1",
                "uname": username,
                "password": password,
                "refer": "https%3A%2F%2Fi.chaoxing.com",
                "t": True,
                "forbidotherlogin": 0,
                "validate": "",
                "doubleFactorLogin": 0,
                "independentId": 0
            }
    print("正在尝试登录...")
    #logger.trace("正在尝试登录...")
    resp = _session.post(_url, headers=gc.HEADERS, data=_data)
    if resp and resp.json()["status"] == True:
        save_cookies(_session)
        print("登录成功...")
        #logger.info("登录成功...")
        return {"status": True, "msg": "登录成功"}
    else:
        return {"status": False, "msg": str(resp.json()["msg2"])}


#初始化requests的session会话
def init_session(isVideo: bool = False, isAudio: bool = False):
    _session = requests.session()
    _session.mount('http://', HTTPAdapter(max_retries=3))
    _session.mount('https://', HTTPAdapter(max_retries=3))
    if isVideo:
        _session.headers = gc.VIDEO_HEADERS
    elif isAudio:
        _session.headers = gc.AUDIO_HEADERS
    else:
        _session.headers = gc.HEADERS
    _session.cookies.update(use_cookies())
    return _session


def get_fid():
    _session = init_session()
    return _session.cookies.get("fid")


def get_video_durations(video_objectid):
    #print(video_objectid)
    # 目标URL
    url = f"https://mooc1.chaoxing.com/ananas/status/{video_objectid}?k={get_fid()}&flag=normal"

    # 设置请求头部
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "Cookie": f"{use_cookies()}",
        "Referer": "https://mooc1.chaoxing.com/ananas/modules/video/index.html?v=2024-0913-1842",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "X-Requested-With": "XMLHttpRequest"
    }

    # 发送GET请求
    response = requests.get(url, headers=headers).json()

    # 打印响应内容
    print(response["duration"])
    return response["duration"]


def time_converter(time_str: str) -> int:
    parts = time_str.split(':')
    if len(parts) != 3:
        hour = 0
        minute, second = int(parts[0]), int(parts[1])

    else:
        hour, minute, second = int(parts[0]), int(parts[1]), int(parts[2])


    seconds = hour * 3600 + minute * 60 + second
    return seconds

def get_playing_time(driver):
    wait = WebDriverWait(driver, 10)  # 等待最多10秒
    for i in range(10):
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.vjs-control-bar[dir='ltr']"))).click()
        element=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"span.vjs-current-time-display[aria-live='off']")))
        _playing_time = element.text
    return time_converter(_playing_time)


def show_progress(video_name:str,_playing_time:int, duration:int):
    # 计算已完成的百分比
    percent_complete = _playing_time / duration

    # 定义进度条的总长度
    bar_length = 40

    # 计算进度条中已填充的部分
    filled_length = int(round(bar_length * percent_complete))

    # 创建进度条的字符串表示
    bar = '#' * filled_length + '-' * (bar_length - filled_length)

    # 显示进度条
    sys.stdout.write(f'\r{video_name}: [{bar}] {percent_complete:.2%}')
    sys.stdout.flush()


def study_video(driver,video_name:str,duration:int):
    playing_time = 0
    _isFinished = False
    print(f"开始任务: {video_name}, 总时长: {duration}秒")
    while not _isFinished:
        if playing_time >= int(duration):
            _isFinished = True

        playing_time = int(get_playing_time(driver))
        # 播放进度条
        show_progress(video_name, playing_time, duration)
    print("\r", end="", flush=True)
    print(f"任务完成: {video_name}")


from selenium import webdriver
from PIL import Image
import time


def preprocess_image(input_image_path, border_size=100, new_width=1200):
    # 打开原始图片
    image = Image.open(input_image_path)

    # 计算新的尺寸和宽高比
    original_width, original_height = image.size
    aspect_ratio = original_height / original_width
    new_height = int(new_width * aspect_ratio)

    # 放大图片
    image_resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 创建新的图片，添加边框
    new_image = Image.new('RGB', (new_width + 2 * border_size, new_height + 2 * border_size), (255, 255, 255))  # 白色背景
    new_image.paste(image_resized, (border_size, border_size))

    # 保存预处理后的图片
    new_image.save(input_image_path)

def scroll_and_capture(driver,url, scroll_pause=0.5, step=500):
    i=1
    output_file = f'images/temp_screenshot{i}.png'
    # 新打开一个窗口
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])  # 切换到新窗口
    driver.get(url)

    # 等待页面加载
    time.sleep(3)  # 等待3秒以确保页面完全加载

    # 获取网页的总高度
    total_height = driver.execute_script("return document.body.parentNode.scrollHeight")
    browser_height = driver.execute_script("return window.innerHeight")

    # 初始化截图列表
    images = []
    x_offset = 0

    # 逐步滚动并截图
    while True:
        # 滚动到指定位置
        driver.execute_script(f"window.scrollTo(0, {x_offset})")
        time.sleep(scroll_pause)  # 等待滚动完成

        # 截图并保存为图片
        driver.save_screenshot(output_file)

        # 将截图添加到列表
        images.append(Image.open(output_file))

        # 更新x_offset
        x_offset += browser_height
        i=i+1
        output_file = f'images/temp_screenshot{i}.png'
        # 如果已经滚动到页面底部，停止滚动
        if x_offset >= total_height:
            # i=i-1
            # output_file = f'images/temp_screenshot{i}.png'
            # 设置窗口大小和位置，使其仅显示下半部分
            # driver.execute_script(f"""
            #         window.resizeTo(1920, {browser_height - (float(x_offset)-float(total_height))});
            #         window.moveTo(0, {(float(x_offset)-float(total_height))});
            #     """)
            # # 截图并保存为图片
            # driver.save_screenshot(output_file)
            # images[-1] = Image.open(output_file)
            break

    if x_offset > total_height+100:
        # 假设 last_image 是最后一张截图的PIL图像对象
        last_image = images[-1]

        # 裁剪掉顶端100像素的高度
        crop_rectangle = (0, float(x_offset)-float(total_height), last_image.size[0], last_image.size[1])
        cropped_image = last_image.crop(crop_rectangle)

        # 将裁剪后的图像替换原来的最后一张截图
        images[-1] = cropped_image


        # 合并截图
        widths, heights = zip(*(i.size for i in images))
        total_width = max(widths)
        max_height = sum(heights)

        new_im = Image.new('RGB', (total_width, max_height))
        y_offset = 0
        for im in images:
            new_im.paste(im, (0, y_offset))
            y_offset += im.size[1]
        final_output_file = 'images/final_screenshot.png'
        new_im.save(final_output_file)
        #preprocess_image(final_output_file)

    # 关闭WebDriver
    driver.close()


#根据获取到的dict题目，操作web完成答案填写
def complete_answer(driver,form_data,test_question_url:str,mid) :
    # 等待题目元素加载完成
    wait = WebDriverWait(driver, 10)
    if form_data == None:
        print("题目解析失败！程序控制暂停，请在Web中手动答题，请答完题再启动程序")
        ocr = PaddleOCR(use_angle_cls=False,
                        lang="ch",
                        det_limit_type='min',
                        det_limit_side_len=100,
                        use_gpu=True,
                det_model_dir= r'D:\pycharm\pythonProject\auto_answers\src\OCR_Model\det\ch\ch_PP-OCRv4_det_infer',
                rec_model_dir= r'D:\pycharm\pythonProject\auto_answers\src\OCR_Model\rec\ch\ch_PP-OCRv4_rec_infer'
                        )
        # 保存初始窗口句柄
        main_window_handle = driver.current_window_handle
        scroll_and_capture(driver,test_question_url)
        driver.switch_to.window(main_window_handle)
        iframe1 = wait.until(EC.presence_of_element_located((By.ID, 'iframe')))
        driver.switch_to.frame(iframe1)
        iframe2 = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"iframe[data*='{mid}']")))
        driver.switch_to.frame(iframe2)
        iframe_questions = wait.until(EC.presence_of_element_located((By.ID, 'frame_content')))
        driver.switch_to.frame(iframe_questions)
        result = ocr.ocr('images/final_screenshot.png')
        print("试题结果：",result)
        lines = defaultdict(list)
        for line in result:
            #遍历每行
            for word in line:
                # 提取出识别数据中的文字元组
                coordinates, (text, confidence) = word
                # 假设第一个坐标点的y值可以代表整行的y值
                y1 = coordinates[0][1]
                y2 = coordinates[2][1]
                y = int((y1 + y2)/2)
                # 检查y值与现有行号的差距，如果差距小于等于2，则归为同一行
                for key in lines:
                    if abs(key - y) <= 5:
                        y = key
                lines[y].append(str(text))
        form_data=decode_ocr_question(lines)
        print()
        #time.sleep(5)
        #获取所有问题
        questions = form_data['questions']
        print(questions)
        # form = wait.until(EC.presence_of_element_located((By.ID,'form1')))
        # print(form.get_attribute('id'))
        #使用driver获取html的题目
        question_elements = driver.find_elements(By.CSS_SELECTOR, "div.TiMu")
        #题目索引，用于标记第几个题目
        i = 0

        #循环遍历表单所有题目
        for question_element in question_elements:
            # 获取题目类型
            question_type = questions[i]['type']
            print(question_type)


            #根据题目类型完成作答
            if question_type == 'single':
                question = (f"{questions[i]['title']}\n"
                            f"{questions[i]['options']}")
                print(question)
                an = Ansewer(question, question_type)
                ans=an.get_answer()
                print(ans)
                time.sleep(5)

                #获取选项
                options = question_element.find_elements(By.CSS_SELECTOR, "li.font-cxsecret")

                # 遍历选项并打印
                for option in options:

                    # 获取选项文本
                    # 可点击的选项
                    _option = option.find_element(By.CSS_SELECTOR, "span.num_option")
                    if ans == _option.text:
                        _option.click()
                        print("点击了"+_option.text)
                        break
                    option_text = option.find_element(By.CSS_SELECTOR, 'a.fl').text
                    # print(f"{_option}. {option_text}")
                #question_text = question_element.find_element(By.CSS_SELECTOR, "span.newZy_TItle").text
                #print("题目文本:", question_text)
            elif question_type == 'multiple' :
                question = (f"{questions[i]['title']}\n"
                            f"{questions[i]['options']}")
                print(question)
                an = Ansewer(question, question_type)
                ans=an.get_answer()
                print(ans)
                time.sleep(5)

                # 获取选项
                options = question_element.find_elements(By.CSS_SELECTOR, "li.font-cxsecret")

                遍历选项并打印
                for option in options:

                    # 获取选项文本
                    # 可点击的选项
                    _option = option.find_element(By.CSS_SELECTOR, "span.num_option")
                    if ans == _option.text:
                        _option.click()
                        print("点击了"+_option.text)
                        break
                pass
            elif question_type == 'judgement' :
                question = (f"{questions[i]['title']}\n"
                            f"{questions[i]['options']}")
                print(question)
                an = Ansewer(question, question_type)
                ans=an.get_answer()
                print(ans)
                time.sleep(5)

                # 获取选项
                options = question_element.find_elements(By.CSS_SELECTOR, "li.font-cxsecret")

                ## 遍历选项并打印
                for option in options:

                    # 获取选项文本
                    # 可点击的选项
                    _option = option.find_element(By.CSS_SELECTOR, "span.num_option")
                    if _option.text in ans :
                        _option.click()
                        print("点击了"+_option.text)
                        break
                pass
            if question_type == 'completion' :
                question = (f"{questions[i]['title']}\n")
                print(question)
                an = Ansewer(question, question_type)
                ans = an.get_answer()
                print(ans)
                time.sleep(5)
                #进入textarea的iframe,将答案填到textarea
                iframe_ueditor_0=wait.until(EC.presence_of_element_located((By.ID,'ueditor_0')))
                driver.switch_to.frame(iframe_ueditor_0)
                textarea=wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,"body.view")))
                textarea.clear()
                textarea.send_keys(ans)
                #退出iframe
                driver.switch_to.parent_frame()

                pass
            else :
                pass
            i=i+1
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[onclick*='btnBlueSubmit();']"))).click()
        except TimeoutException:
            pass
        current_position = pyautogui.position()
        # current_x, current_y = driver.execute_script("return [window.screenX, window.screenY];")
        # print(current_x, current_y)
        # 打印当前鼠标的位置
        # print(f"当前鼠标位置：X={current_position.x}, Y={current_position.y}")
        # 移动到屏幕上的绝对坐标 (1128, 595)
        time.sleep(5)
        pyautogui.moveTo(1128, 595)
        pyautogui.click()
        time.sleep(5)
        pyautogui.moveTo(1128, 595)
        pyautogui.click()

    else :
        ocr = PaddleOCR(use_angle_cls=False,
                        lang="ch",
                        det_limit_type='min',
                        det_limit_side_len=100,
                        use_gpu=True,
                        det_model_dir=r'D:\pycharm\pythonProject\auto_answers\src\OCR_Model\det\ch\ch_PP-OCRv4_det_infer',
                        rec_model_dir=r'D:\pycharm\pythonProject\auto_answers\src\OCR_Model\rec\ch\ch_PP-OCRv4_rec_infer'
                        )
        # 保存初始窗口句柄
        main_window_handle = driver.current_window_handle
        scroll_and_capture(driver, test_question_url)
        driver.switch_to.window(main_window_handle)
        iframe1 = wait.until(EC.presence_of_element_located((By.ID, 'iframe')))
        driver.switch_to.frame(iframe1)
        iframe2 = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"iframe[data*='{mid}']")))
        driver.switch_to.frame(iframe2)
        iframe_questions = wait.until(EC.presence_of_element_located((By.ID, 'frame_content')))
        driver.switch_to.frame(iframe_questions)
        result = ocr.ocr('images/final_screenshot.png')
        print("试题结果：", result)
        lines = defaultdict(list)
        for line in result:
            # 遍历每行
            for word in line:
                # 提取出识别数据中的文字元组
                coordinates, (text, confidence) = word
                # 假设第一个坐标点的y值可以代表整行的y值
                y1 = coordinates[0][1]
                y2 = coordinates[2][1]
                y = int((y1 + y2) / 2)
                # 检查y值与现有行号的差距，如果差距小于等于2，则归为同一行
                for key in lines:
                    if abs(key - y) <= 5:
                        y = key
                lines[y].append(str(text))
        form_data = decode_ocr_question(lines)
        print()
        # time.sleep(5)
        # 获取所有问题
        questions = form_data['questions']
        print(questions)
        # form = wait.until(EC.presence_of_element_located((By.ID,'form1')))
        # print(form.get_attribute('id'))
        # 使用driver获取html的题目
        question_elements = driver.find_elements(By.CSS_SELECTOR, "div.TiMu")
        # 题目索引，用于标记第几个题目
        i = 0

        # 循环遍历表单所有题目
        for question_element in question_elements:
            # 获取题目类型
            question_type = questions[i]['type']
            print(question_type)

            # 根据题目类型完成作答
            if question_type == 'single':
                question = (f"{questions[i]['title']}\n"
                            f"{questions[i]['options']}")
                print(question)
                an = Ansewer(question, question_type)
                ans = an.get_answer()
                print(ans)
                time.sleep(5)

                # 获取选项
                options = question_element.find_elements(By.CSS_SELECTOR, "li.font-cxsecret")

                # 遍历选项并打印
                for option in options:

                    # 获取选项文本
                    # 可点击的选项
                    _option = option.find_element(By.CSS_SELECTOR, "span.num_option")
                    if ans == _option.text:
                        _option.click()
                        print("点击了" + _option.text)
                        break
                    option_text = option.find_element(By.CSS_SELECTOR, 'a.fl').text
                    # print(f"{_option}. {option_text}")
                # question_text = question_element.find_element(By.CSS_SELECTOR, "span.newZy_TItle").text
                # print("题目文本:", question_text)
            elif question_type == 'multiple':
                question = (f"{questions[i]['title']}\n"
                            f"{questions[i]['options']}")
                print(question)
                an = Ansewer(question, question_type)
                ans = an.get_answer()
                print(ans)
                time.sleep(5)

                # 获取选项
                options = question_element.find_elements(By.CSS_SELECTOR, "li.font-cxsecret")

                遍历选项并打印
                for option in options:

                    # 获取选项文本
                    # 可点击的选项
                    _option = option.find_element(By.CSS_SELECTOR, "span.num_option")
                    if ans == _option.text:
                        _option.click()
                        print("点击了" + _option.text)
                        break
                pass
            elif question_type == 'judgement':
                question = (f"{questions[i]['title']}\n"
                            f"{questions[i]['options']}")
                print(question)
                an = Ansewer(question, question_type)
                ans = an.get_answer()
                print(ans)
                time.sleep(5)

                # 获取选项
                options = question_element.find_elements(By.CSS_SELECTOR, "li.font-cxsecret")

                ## 遍历选项并打印
                for option in options:

                    # 获取选项文本
                    # 可点击的选项
                    _option = option.find_element(By.CSS_SELECTOR, "span.num_option")
                    if _option.text in ans:
                        _option.click()
                        print("点击了" + _option.text)
                        break
                pass
            if question_type == 'completion':
                question = (f"{questions[i]['title']}\n")
                print(question)
                an = Ansewer(question, question_type)
                ans = an.get_answer()
                print(ans)
                time.sleep(5)
                # 进入textarea的iframe,将答案填到textarea
                iframe_ueditor_0 = wait.until(EC.presence_of_element_located((By.ID, 'ueditor_0')))
                driver.switch_to.frame(iframe_ueditor_0)
                textarea = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "body.view")))
                textarea.clear()
                textarea.send_keys(ans)
                # 退出iframe
                driver.switch_to.parent_frame()

                pass
            else:
                pass
            i = i + 1
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[onclick*='btnBlueSubmit();']"))).click()
        except TimeoutException:
            pass
        current_position = pyautogui.position()
        # current_x, current_y = driver.execute_script("return [window.screenX, window.screenY];")
        # print(current_x, current_y)
        # 打印当前鼠标的位置
        # print(f"当前鼠标位置：X={current_position.x}, Y={current_position.y}")
        # 移动到屏幕上的绝对坐标 (1128, 595)
        time.sleep(5)
        pyautogui.moveTo(1128, 595)
        pyautogui.click()
        time.sleep(5)
        pyautogui.moveTo(1128, 595)
        pyautogui.click()

        # #获取所有问题
        # questions = form_data['questions']
        #
        # form = wait.until(EC.presence_of_element_located((By.ID,'form1')))
        # print(form.get_attribute('id'))
        #
        # #使用driver获取html的题目
        # question_elements = form.find_elements(By.CSS_SELECTOR, "div.TiMu")
        # #题目索引，用于标记第几个题目
        # i = 0
        # #循环遍历表单所有题目
        # for question_element in question_elements:
        #     # 获取题目类型
        #     question_type = questions[i]['type']
        #     print(question_type)
        #
        #
        #     #根据题目类型完成作答
        #     if question_type == 'single':
        #         question = (f"{questions[i]['title']}\n"
        #                     f"{questions[i]['options']}")
        #         print(question)
        #         an = Ansewer(question, question_type)
        #         ans=an.get_answer()
        #         print(ans)
        #         time.sleep(5)
        #
        #         #获取选项
        #         options = question_element.find_elements(By.CSS_SELECTOR, "li.font-cxsecret")
        #
        #         # 遍历选项并打印
        #         for option in options:
        #
        #             # 获取选项文本
        #             # 可点击的选项
        #             _option = option.find_element(By.CSS_SELECTOR, "span.num_option")
        #             if ans == _option.text:
        #                 _option.click()
        #                 print("点击了"+_option.text)
        #             option_text = option.find_element(By.CSS_SELECTOR, 'a.fl').text
        #             # print(f"{_option}. {option_text}")
        #         #question_text = question_element.find_element(By.CSS_SELECTOR, "span.newZy_TItle").text
        #         #print("题目文本:", question_text)
        #     elif question_type == 'multiple' :
        #         question = (f"{questions[i]['title']}\n"
        #                     f"{questions[i]['options']}")
        #         print(question)
        #         an = Ansewer(question, question_type)
        #         ans=an.get_answer()
        #         print(ans)
        #         time.sleep(5)
        #
        #         # 获取选项
        #         options = question_element.find_elements(By.CSS_SELECTOR, "li.font-cxsecret")
        #
        #         遍历选项并打印
        #         for option in options:
        #
        #             # 获取选项文本
        #             # 可点击的选项
        #             _option = option.find_element(By.CSS_SELECTOR, "span.num_option")
        #             if ans == _option.text:
        #                 _option.click()
        #                 print("点击了"+_option.text)
        #         pass
        #     elif question_type == 'judgement' :
        #         question = (f"{questions[i]['title']}\n"
        #                     f"{questions[i]['options']}")
        #         print(question)
        #         an = Ansewer(question, question_type)
        #         ans=an.get_answer()
        #         print(ans)
        #         time.sleep(5)
        #
        #         # 获取选项
        #         options = question_element.find_elements(By.CSS_SELECTOR, "li.font-cxsecret")
        #
        #         ## 遍历选项并打印
        #         for option in options:
        #
        #             # 获取选项文本
        #             # 可点击的选项
        #             _option = option.find_element(By.CSS_SELECTOR, "span.num_option")
        #             if _option.text in ans :
        #                 _option.click()
        #                 print("点击了"+_option.text)
        #         pass
        #     if question_type == 'completion' :
        #         question = (f"{questions[i]['title']}\n")
        #         print(question)
        #         an = Ansewer(question, question_type)
        #         ans = an.get_answer()
        #         print(ans)
        #         time.sleep(5)
        #         #进入textarea的iframe,将答案填到textarea
        #         iframe_ueditor_0=wait.until(EC.presence_of_element_located((By.ID,'ueditor_0')))
        #         driver.switch_to.frame(iframe_ueditor_0)
        #         textarea=wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,"body.view")))
        #         textarea.clear()
        #         textarea.send_keys(ans)
        #         #退出iframe
        #         driver.switch_to.parent_frame()
        #
        #         pass
        #     else :
        #         pass
        #     i=i+1
        # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[onclick*='btnBlueSubmit();']"))).click()
        # current_position = pyautogui.position()
        # # current_x, current_y = driver.execute_script("return [window.screenX, window.screenY];")
        # # print(current_x, current_y)
        # # 打印当前鼠标的位置
        # #print(f"当前鼠标位置：X={current_position.x}, Y={current_position.y}")
        # # 移动到屏幕上的绝对坐标 (1128, 595)
        # time.sleep(5)
        # pyautogui.moveTo(1128, 595)
        # pyautogui.click()
        # time.sleep(5)
        # pyautogui.moveTo(1128, 595)
        # pyautogui.click()






        # #获取当前窗口的位置
        # current_x, current_y = driver.execute_script("return [window.screenX, window.screenY];")
        # print(current_x, current_y)
        # 获取当前鼠标的位置



        # 创建ActionChains对象
        #actions = ActionChains(driver)

        # 移动到屏幕上的绝对坐标 (694, 636)
        #actions.move_to_location(xoffset=1128, yoffset=595).click().perform()


        # 在该坐标处执行点击操作

        # 目标坐标
        # target_x = 1128
        # target_y = 595
        #
        # # 计算需要移动的偏移量
        # offset_x = target_x - current_x
        # offset_y = target_y - current_y
        #




