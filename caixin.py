import requests, logging,json, os, urllib, time, traceback
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

template = ""
header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        }

def main():
    name = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(filename = name + ".txt",level = logging.INFO, format = LOG_FORMAT, encoding = 'utf-8')
    pass

'''
def download_total(session:requests.Session):
    rsp = requests.get("https://weekly.caixin.com/", headers = header)
    soup = BeautifulSoup(rsp.text.replace('style="display:none;>', '>'), 'html.parser')
    wangqi = soup.find("div", class_ = "wangqi")
    lis = wangqi.find("div", class_ = "wqCon").find_all("li")
    weeklys = []
    for i in lis:
        a = i.find("a")
        weeklys.append({"href": a.get("href"), "title": a.get_text()})
    with open("total.json", "w", encoding = "utf") as f:
        json.dump(weeklys, f, ensure_ascii = False)
    
    weeklys = []
    with open("total.json", encoding = "utf") as f:
        weeklys = json.load(f)
    for i in weeklys:
        download_weekly(session, i["href"])
        logging.info(i)
'''

def download_img(url, path, cookie = None, session = None):
    url = url.strip()
    urlparse = urllib.parse.urlparse(url)
    if urlparse.scheme == "":
        urlparse = urlparse._replace(scheme = 'https')
        url = urllib.parse.urlunparse(urlparse)
    if session:
        response = session.get(url)
    else:
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        }
        if cookie != None:
            header["Cookie"] = cookie
        response = requests.get(url, headers=header)
    assert response.status_code == 200
    with open(path, "wb") as f:
        f.write(response.content)

def download_article(session:requests.Session, path, article_id, title):
    rsp = session.get("http://gateway.caixin.com/api/newauth/checkAuthByIdJsonp?type=0&page=0&id={}".format(article_id))
    logging.info("rsp: {}, article_id: {}.".format(rsp.text, article_id))
    rsp_json = rsp.json()
    assert rsp_json != None and rsp_json.get("code") == 0, 'article_id: {},title: {},rsp.text:{}'.format(article_id, title, rsp.text)
    content = rsp_json["data"][len("resetContentInfo("):-1]
    content = json.loads(content)
    soup = BeautifulSoup(content["content"], 'html.parser')
    imgs = soup.find_all("img")
    for i in imgs:
        src = i.get("src")
        if src == "https://www.caixin.com/favicon.ico":
            i["src"] = "/favicon.ico"
            continue
        urlparse = urllib.parse.urlparse(src)
        basename = "{}_{}".format(article_id, os.path.basename(urlparse.path))
        img_path = os.path.join(path, basename)
        download_img(src, img_path)
        i["src"] = urllib.request.pathname2url(basename)
    file_name = os.path.join(path, "{}.html".format(article_id))
    with open(file_name, "w", encoding="utf") as f:
        f.write(template.format(title = title, content = str(soup)))

def download_articles(article_list, path):
    ser = webdriver.ChromeService(executable_path="chromedriver.exe")
    #ser = webdriver.EdgeService(executable_path="msedgedriver.exe")
    #options = webdriver.EdgeOptions()
    options = webdriver.ChromeOptions()
    user_data_dir = os.path.join(os.getcwd(), "UserData")
    os.makedirs(user_data_dir, exist_ok=True)
    options.add_argument("user-data-dir={}".format(user_data_dir))
    try:
        driver = webdriver.Chrome(service=ser, options=options)
        #driver = webdriver.Edge(service=ser)
        driver.get("https://u.caixin.com/web/login?url=https%3A%2F%2Fweekly.caixin.com%2F")
        time.sleep(60)
        for article in article_list:
            logging.info(article)
            download_article(driver, article, path)
        driver.close()
    finally:
        driver.quit()
    pass

def download_article(driver, article, path):
    try:
        content = getContent(driver, "{}?p0".format(article["href"].strip()))
    except:
        logging.error("Exception: %s", traceback.format_exc())
        logging.error(article)
        return
    soup = BeautifulSoup(content, 'html.parser')
    aitt = soup.find_all("p", class_ = "aitt")
    for i in aitt:
        i.decompose()
    imgs = soup.find_all("img")
    for img in imgs:
        src = img.get("src")
        src = src.strip()
        if src == "https://www.caixin.com/favicon.ico":
            img["src"] = "/favicon.ico"
            continue
        urlparse = urllib.parse.urlparse(src)
        basename = "{}_{}".format(article["article_id"], os.path.basename(urlparse.path))
        basename = basename.strip()
        img_path = os.path.join(path, basename)
        try:
            download_img(src, img_path)
        except:
            logging.error("Exception: %s", traceback.format_exc())
            logging.error("article: {}, src: {}".format(article, src))
            continue
        img["src"] = urllib.request.pathname2url(basename)
    file_name = os.path.join(path, "{}.html".format(article["article_id"]))
    with open(file_name, "w", encoding="utf") as f:
        f.write(template.format(title = article["title"], content = str(soup)))

def getContent(driver:webdriver.Chrome, url):
    url = url.strip()
    driver.get(url)
    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, "end_ico"))
        )
    except TimeoutException: #handle WebDriverWait
        logging.warning("TimeoutException: end_ico, url: {}".format(driver.current_url))
        try:
            driver.find_element(By.LINK_TEXT, "余下全文").click()
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CLASS_NAME, "end_ico"))
            )
        except NoSuchElementException: #handle driver.find_element
            pass
        except TimeoutException: #handle WebDriverWait
            logging.warning("TimeoutException: left end_ico, url: {}".format(driver.current_url))
    content = driver.find_element(By.ID, "Main_Content_Val")
    return content.get_attribute("innerHTML")

def download_magazine(session:requests.Session, url, magazine_path):
    rsp = session.get(url)
    soup = BeautifulSoup(rsp.text, 'html.parser')
    main_conntent = soup.find("div", class_ = "mainMagContent")
    title = main_conntent.find("div", class_ = "title").get_text()
    main_conntent.find("div", class_ = "date").decompose()
    cover = main_conntent.find("div", class_ = "cover")
    img = cover.find("img")
    src = img.get("src")
    src.strip()
    path = urllib.parse.urlparse(src).path
    img_name = "cover" + path[path.find("."):]
    img_path = os.path.join(magazine_path, img_name)
    download_img(src, img_path)
    img["src"] = urllib.request.pathname2url(img_name)
    cover.clear()
    cover.insert(0, img)
    articles = main_conntent.find_all("a")
    article_list = []
    for i in articles:
        href = i.get("href")
        if href is None:
            logging.error("article: {} has no link.".format(i))
            continue
        basename = os.path.basename(urllib.parse.urlparse(href).path)
        article_list.append({"href": href, "title": i.get_text(), "article_id": os.path.splitext(basename)[0]})
        i["href"] = urllib.request.pathname2url(basename)
    with open(os.path.join(magazine_path, "index.html"), "w", encoding="utf") as f:
        f.write(template.format(title = title, content = str(main_conntent)))
    logging.debug(article_list)
    return article_list

if __name__ == "__main__":
    main()

if __name__ == "caixin":
    with open("template.html", encoding="utf") as f:
        template = f.read()
