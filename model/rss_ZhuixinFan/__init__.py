#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import shutil

import pymysql
import requests
from bs4 import BeautifulSoup
from Magnet_To_Torrent import magnet2torrent


class JSONObject:
    def __init__(self, d):
        self.__dict__ = d


setting = json.loads(open("settings.json", "r").read(), object_hook=JSONObject)

db = pymysql.connect(host=setting.db_address, port=setting.db_port,
                     user=setting.db_user, password=setting.db_password,
                     db=setting.db_name, charset='utf8')
search_pattern = re.compile(
    "(?:[\W]+?\.|^)(?P<full_name>(?P<search_name>[\w.]+?)(?:\.| )(?P<tv_season>(?:[Ss]\d+)?[Ee][Pp]?\d+(?:-[Ee]?[Pp]?\d+)?).+-(?P<group>.+?))"
    "(?:\.(?P<tv_filetype>\w+)$|$)")


def find_max_in_rss_record():
    cursor = db.cursor()
    sql = "SELECT MAX(id) FROM `ZhuixinFan`"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    t = result[0][0]
    if not t:
        t = 0
    return t


def commit_cursor_into_db(sql):
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        db.commit()
        cursor.close()
    except:
        db.rollback()


# 从数据库中获取剧集简介
def get_info_from_db(torrent_search_name):
    cursor = db.cursor()
    sql = "SELECT * FROM tv_info WHERE tv_ename='%s'" % torrent_search_name
    cursor.execute(sql)
    result = list(cursor.fetchall()[0])
    cursor.close()
    return result


def find_new():
    i = find_max_in_rss_record()
    while True:
        bs_page = BeautifulSoup(
            requests.get("http://www.zhuixinfan.com/main.php?mod=viewresource&sid={0}".format(i)).text, "html5lib")
        series_name = bs_page.find("span", id="pdtname").get_text()
        if not series_name:
            break
        else:
            # 记入SQL
            size = int(re.search(r"\d+", bs_page.find("span", text=re.compile(r"\[\d+M\]")).get_text()).group(0))
            magnet_link = bs_page.find("dd", id="torrent_url").get_text()
            code = re.search(r"urn\:btih\:(?P<code>\w+)", magnet_link).group("code")
            torrent_loc = magnet2torrent(magnet_link, output_name="./torrent/{0}.torrent".format(code))
            sql = "INSERT INTO ZhuixinFan (id,title,size,magnet_link,torrent_loc) VALUES ('%d','%s','%d','%s','%s')" \
                  % (i, series_name, size, magnet_link, torrent_loc)
            commit_cursor_into_db(sql=sql)
            i += 1
            # 筛选，符合记录的种子送入watch目录
            torrent_info_search = re.search(search_pattern, series_name)
            try:
                get_info_from_db(torrent_info_search.group("search_name"))
            except IndexError:
                continue
            else:
                if re.search(r'1280X720', series_name):
                    shutil.move(torrent_loc, setting.trans_watchdir)
