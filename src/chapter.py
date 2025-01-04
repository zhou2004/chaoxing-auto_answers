from src.decode import *
from src.config import GlobalConst as gc
from src.tool import *
from src.cookies import *
from src.answer import *
#实例化一个课程对象（使用selenium操作chaoxing网页对应的课程）
class Course :
    #两个初始参数，driver:实例化web驱动，courseid:课程id
    def __init__(self,driver,courseid) :
        self.courseid = courseid
        self.driver = driver
        self.chapter_class = '.posCatalog_name'

    #获取所有章节元素，以列表形式返回
    def get_chapters(self) :
        wait = WebDriverWait(self.driver, 10)  # 等待最多10秒
        #获取课程所有的章节
        chapters = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, f"{self.chapter_class}")))
        chapters_title=[]
        for chapter in chapters :
            chapters_title.append(chapter.get_attribute('title'))
        return chapters_title


    #获取视频对应的播放按钮
    def get_video_playing(self) :
        wait = WebDriverWait(self.driver, 3)
        try:
            video_playing = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"button[title='播放视频']")))

        except TimeoutException :
            video_playing = None

        return video_playing

    def init_session(self,isVideo: bool = False, isAudio: bool = False):
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

    #获取chaoxing试题的html
    def get_test_questions(self):
        wait = WebDriverWait(self.driver, 10)
        try:
            #进入试对应的iframe
            iframe_questions = wait.until(EC.presence_of_element_located((By.ID, 'frame_content')))
            qeustion_id=iframe_questions.get_attribute('id')
            self.driver.switch_to.frame(iframe_questions)

            # 执行JavaScript来获取iframe的document对象(拿到试题的html内容)
            iframe_document_url = self.driver.execute_script("return document.URL;")
            print(iframe_document_url)
            _session = self.init_session()

            # 这里拿到了所有试题以及选项(通过url获取html页面信息)
            res = _session.get(str(iframe_document_url))

            #试题html页面汉字加密了，交给decode函数解析出来
            questions=decode_questions_info(res.text)

        except TimeoutException :
            self.driver.switch_to.parent_frame()
            return None,None
        except NoSuchElementException:
            self.driver.switch_to.parent_frame()
            return None,None
        except StaleElementReferenceException:
            self.driver.switch_to.parent_frame()
            return None,None
        return questions,iframe_document_url


    #获取一个章节的所有iframe框架，以列表形式返回（每个章节对应的iframe都包含视频，pdf,题目这些内容）
    def get_iframe(self):
        wait = WebDriverWait(self.driver, 10)
        try:
            iframes = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'iframe')))
            if not iframes:
                return None
            iframes_list = []
            for iframe in iframes:
                #将iframe的mid属性添加到列表(mid为iframe的唯一属性)
                #ifram_decode解码iframe的json信息，若没有则返回空值None
                iframes_list.append(iframe_decode(iframe).get('mid', None))
        except TimeoutException:
            iframes_list = None
        except NoSuchElementException:
            iframes_list = None
        return iframes_list












