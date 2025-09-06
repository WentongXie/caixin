import logging, requests, os, urllib, time, re
from bs4 import BeautifulSoup
import caixin

def main():
    name = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(filename = name + ".txt",level = logging.INFO, format = LOG_FORMAT, encoding = 'utf-8')
    with requests.session() as s:
        s.headers.update(caixin.header)
        #new_weekly = "https://weekly.caixin.com/2025/cw1156/"
        new_weekly = update(s)
        weekly_path = urllib.parse.urlparse(new_weekly).path[1:]
        os.makedirs(weekly_path, exist_ok=True)
        article_list = caixin.download_magazine(s, new_weekly, weekly_path)
        #article_list = [{'href': 'https://weekly.caixin.com/2025-08-15/102352024.html', 'title': '显影｜少年极客的代码嘉年华', 'article_id': '102352024'}]
        caixin.download_articles(article_list, weekly_path)

def update(session:requests.Session):
    rsp = session.get("https://weekly.caixin.com/")
    soup = BeautifulSoup(rsp.text.replace('style="display:none;>', ">"), 'html.parser')
    focus = soup.find("div", class_ = "focusCon")
    wangqi = soup.find("div", class_ = "wangqi")
    del_dom = []
    del_dom.extend(wangqi.find_all("script"))
    del_dom.extend(wangqi.find_all("style"))
    del_dom.extend(wangqi.find_all("div", class_="more"))
    del_dom.extend(wangqi.find_all("div", class_="clear"))
    del_dom.extend(wangqi.find_all("ul", class_="wqNav"))
    for i in del_dom:
        i.decompose()
    lis = wangqi.find("div", class_ = "wqCon").find_all("li")
    for i in lis:
        a = i.find("a")
        href = urllib.parse.urlparse(a.get("href")).path[1:]
        a["href"] = href
        img = i.find("img")
        path = urllib.parse.urlparse(img.get("data-src")).path
        img_src = urllib.request.pathname2url(os.path.join(href, "cover" + path[path.find("."):]))
        img["data-src"] = img_src
        #img["src"]= img_src
    focus.find("div", class_ = "app").decompose()
    mi = focus.find("div", class_ = "mi")
    new_weekly = mi.find("a")
    new_weekly_url = new_weekly.get("href")
    href = urllib.parse.urlparse(new_weekly_url).path[1:]
    new_weekly["href"] = href
    img = mi.find("img")
    path = urllib.parse.urlparse(img.get("src")).path
    img["src"] = urllib.request.pathname2url(os.path.join(href, "cover" + path[path.find("."):]))
    for i in ["lf", "ri"]:
        div = focus.find("div", class_ = i)
        a = div.find_all("a")
        for j in a:
            j_href = j.get("href")
            j["href"] = urllib.request.pathname2url(os.path.join(href, os.path.basename(urllib.parse.urlparse(j_href).path)))
    wangqi_str = re.sub('style=".*?"', "", str(wangqi))
    with open("index.html", "w", encoding="utf") as f:
        f.write(caixin.template.format(title = "财新周刊", content = str(focus) + wangqi_str))
    return new_weekly_url

if __name__ == "__main__":
    main()
