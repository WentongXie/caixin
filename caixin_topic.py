import logging
import requests
import os
import urllib
import time
import json
import datetime
import caixin

topic_file = "topic.json"
articles_file = "articles.json"
topic_html_template = '<a href="{}"><h4 >{}</h4><p>{}</p><img src="{}"></a><br/>'


class topic_article(caixin.article):
    def __init__(self, article_id: str, title: str, href: str, time: int, pics: str, dir_path: str):
        super().__init__(article_id, title, href)
        self.time = time
        self.pics = pics.strip()
        self.dir_path = dir_path.strip()

    def __str__(self):
        return str(self)


def main():
    name = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(filename=name + ".txt",
                        level=logging.INFO, format=LOG_FORMAT, encoding='utf-8')
    basedir = "topic"
    os.makedirs(basedir, exist_ok=True)
    topics = []
    articles = {}
    download_articles = []
    with open(topic_file, "r", encoding="utf-8") as f:
        topics = json.load(f)
    with open(articles_file, "r", encoding="utf-8") as f:
        articles = json.load(f)
    with requests.session() as s:
        s.headers.update(caixin.header)
        for topic in topics:
            topic_articles = get_articles(s, topic)
            logging.debug("topic: {}, topic_articles: {}".format(
                topic, topic_articles))
            topic_html = ""
            for i in topic_articles:
                logging.debug("{}".format(i))
                article_path = urllib.request.pathname2url(
                    os.path.join(i.dir_path, "{}.html".format(i.article_id)))
                date_object = datetime.datetime.fromtimestamp(i.time)
                date = "{}-{:02d}-{:02d}".format(date_object.year,
                                                 date_object.month, date_object.day)
                urlparse = urllib.parse.urlparse(i.pics)
                basename = "{}_{}".format(
                    i.article_id, os.path.basename(urlparse.path))
                basename = basename.strip()
                img_path = urllib.request.pathname2url(
                    os.path.join(i.dir_path, basename))
                caixin.download_img(i.pics, os.path.join(
                    basedir, img_path), session=s)
                topic_html += topic_html_template.format(
                    article_path, i.title, date, img_path)
                downloaded = articles.get(i.article_id, None)
                if downloaded:
                    if i.time == downloaded["time"] and i.title == downloaded["title"]:
                        continue
                    else:
                        logging.warning("article change: {}".format(i))
                download_articles.append(i)
            with open("{}/{}.html".format(basedir, topic["topic_id"]), "w", encoding="utf-8") as f:
                f.write(caixin.template.format(
                    title=topic["topic_title"], content=topic_html))


def get_articles(session: requests.Session, topic) -> list[topic_article]:
    articles = []
    pageNum = 1
    while True:
        url = "https://entities.caixin.com/apientry/newTopic/getNewsTabContent?tabId={}&pageNum={}&pageSize=20".format(
            topic["topic_id"], pageNum)
        rsp = session.get(url).json()
        assert rsp["success"] == True, "get_articles fail, topic: {}, rsp: {}".format(
            topic, rsp)
        articles.extend(rsp["data"]["groupList"][0]["mainList"])
        pageNum += 1
        if not rsp["data"].get("hasNext", False):
            break
    logging.debug("articles: {}".format(articles))
    ret = []
    for i in articles:
        parsed_url = urllib.parse.urlparse(i["web_url"])
        href = urllib.parse.urlunparse(
            (parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
        date_object = datetime.datetime.fromtimestamp(i["time"])
        path = "{}-{:02d}".format(date_object.year, date_object.month)
        ret.append(topic_article(i["id"], i["title"],
                   href, i["time"], i["pics"], path))
    logging.debug("ret: {}".format(ret))
    return ret


if __name__ == "__main__":
    main()
