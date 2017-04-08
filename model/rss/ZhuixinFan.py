#!/usr/bin/python3
# -*- coding: utf-8 -*-

import PyRSS2Gen
import datetime
import re
import requests
from bs4 import BeautifulSoup

import utils

db = utils.db
config = utils.config


def get_new():
    i = utils.find_max_in_rss_record(db, "rss_ZhuixinFan")
    main_page = BeautifulSoup(requests.get("http://www.zhuixinfan.com/main.php").text, "html5lib")
    last_page_tag = main_page.find("a", href=re.compile(r'main.php\?mod=viewresource&sid=(\d+)'))
    last_page_id = int(re.search(r'sid=(\d+)', last_page_tag["href"]).group(1))
    # Blank Table function
    if i == 0:
        top_list = main_page.find("table", class_="top-list-data").find_all("tr")
        min_page = top_list[-1]
        min_id = re.search(r"sid=(\d+)", str(min_page)).group(1)
        i = int(min_id)
    # Normal function
    if i == last_page_id:
        return
    else:
        while i <= last_page_id:
            url = "http://www.zhuixinfan.com/main.php?mod=viewresource&sid={0}".format(i)
            bs_page = BeautifulSoup(requests.get(url=url).text, "html5lib")
            series_name = bs_page.find("span", id="pdtname").get_text()
            if series_name:
                magnet_link = bs_page.find("dd", id="torrent_url").get_text()
                print("Get new torrent,which id:{0}".format(i))
                sql = "INSERT INTO rss_ZhuixinFan (id,title,magnet_link) VALUES ('%d','%s','%s')" % (
                    i, series_name, magnet_link)
                utils.commit_cursor_into_db(db, sql=sql)
            i += 1


def create_rss_feed():
    cursor = db.cursor()
    sql = "SELECT * FROM rss_ZhuixinFan  ORDER BY id DESC LIMIT {0}".format(config.RSS_NUMBER)
    cursor.execute(sql)
    result = cursor.fetchall()
    item = []
    for tid, time, title, magnet_link in result:
        rss_item = PyRSS2Gen.RSSItem(
            title="{0}".format(title.encode('utf-8').decode('unicode_escape')),
            link="{0}".format(magnet_link),
            description="http://www.zhuixinfan.com/main.php?mod=viewresource&sid={0}".format(tid),
            pubDate="{0}".format(time)
        )
        item.append(rss_item)
    rss = PyRSS2Gen.RSS2(
        title="Rhilip's ZhuixinFan feed",
        link="https://github.com/Rhilip/rss_ZhuixinFan",
        description="A rss feed to download ZhuixinFan torrent",
        lastBuildDate=datetime.datetime.now(),
        items=item
    )
    rss.write_xml(open("{0}/ZhuixinFan.xml".format(config.WEB_LOC), "w"))


if __name__ == '__main__':
    print("Run at: {0}".format(datetime.datetime.now()))
    get_new()
    create_rss_feed()
