# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import re
import time
import os
from http.cookies import SimpleCookie

import pymysql
import transmissionrpc
import requests
from bs4 import BeautifulSoup


# Config
class JSONObject:
    def __init__(self, d):
        self.__dict__ = d


setting = json.loads(open("settings.json", "r").read(), object_hook=JSONObject)
tc = transmissionrpc.Client(address=setting.trans_address, port=setting.trans_port, user=setting.trans_user,
                            password=setting.trans_password)
db = pymysql.connect(host=setting.db_address, port=setting.db_port, user=setting.db_user, password=setting.db_password,
                     db=setting.db_name, charset='utf8')
cookie = SimpleCookie(setting.byr_cookies)
cookies = {}
for key, morsel in cookie.items():
    cookies[key] = morsel.value


def commit_cursor_into_db(sql):
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        db.commit()
        cursor.close()
    except:
        db.rollback()


def find_max(column, table):
    cursor = db.cursor()
    sql = "SELECT MAX(" + column + ") FROM `" + table + "`"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    t = result[0][0]
    if not t:
        t = 0
    return t


def get_table_seed_list():
    cursor = db.cursor()
    sql = "SELECT id,download_id,seed_id FROM seed_list"
    cursor.execute(sql)
    return_info = cursor.fetchall()
    cursor.close()
    return return_info


def update_torrent_info_from_rpc_to_db():
    cursor = db.cursor()
    sql = "SELECT id,title FROM seed_list"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    title_list = []
    for i in result:
        title_list.append(i[1])
    last_seed_id = find_max("seed_id", "seed_list")
    for t in tc.get_torrents():
        if t.id > last_seed_id:
            if t.name in title_list:
                sort_id = result[title_list.index(t.name)][0]
                if t.trackers[0]["announce"].find(setting.seed_tracker) != -1:
                    sql = "UPDATE seed_list SET seed_id = '%d' WHERE id = '%d'" % (t.id, sort_id)
                    commit_cursor_into_db(sql)
            elif t.trackers[0]["announce"].find(setting.seed_tracker) == -1:
                sql = "INSERT INTO seed_list (title,download_id) VALUES ('%s','%d')" % (t.name, t.id)
                commit_cursor_into_db(sql)


def del_torrent_with_data_and_db():
    result = get_table_seed_list()
    for t in result:
        if t[2] != 0:
            seed_torrent = tc.get_torrent(t[2])
            if seed_torrent.uploadRatio >= setting.torrent_maxUploadRatio or (
                        int(time.time()) - seed_torrent.addedDate) >= setting.torrent_maxSeedTime:
                sql = "DELETE FROM seed_list WHERE id = '%d'" % (t[0])
                commit_cursor_into_db(sql)
                tc.remove_torrent(t[2], delete_data=True)
                tc.remove_torrent(t[1])


def get_info_from_db(torrent_search_name):
    cursor = db.cursor()
    sql = "SELECT * FROM tv_info WHERE tv_ename='%s'" % torrent_search_name
    cursor.execute(sql)
    result = list(cursor.fetchall()[0])
    cursor.close()
    return result


def exist_judge(tid):
    tag = 1
    t = tc.get_torrent(tid)
    torrent_name = t.name
    pattern = re.compile(
        "(?P<full_name>(?P<search_name>.+?)\.(?P<tv_season>[S|s]\d+(?:(?:[E|e]\d+)|(?:[E|e]\d+-[E|e]\d+)))\..+?-(?P<group>.+?))\.(?P<tv_filetype>mkv)")
    torrent_info_search = re.search(pattern, torrent_name)
    if torrent_info_search:
        full_name = torrent_info_search.group("full_name")
        exits_judge_raw = requests.get(
            url="http://bt.byr.cn/torrents.php?secocat=&cat=&incldead=0&spstate=0&inclbookmarked=0&search=" + full_name + "&search_area=0&search_mode=0",
            cookies=cookies)
        bs = BeautifulSoup(exits_judge_raw.text, "html5lib")
        if bs.find_all(text=re.compile("没有种子")):
            tag = 0
        return tag


def seed_post(tid):
    if exist_judge(tid) == 0:
        t = tc.get_torrent(tid)
        torrent_full_name = t.name
        pattern = re.compile("(?P<full_name>(?P<search_name>.+?)\.(?P<tv_season>[S|s]\d+(?:(?:[E|e]\d+)|(?:[E|e]\d+-[E|e]\d+)))\..+?-(?P<group>.+?))\.(?P<tv_filetype>mkv)")
        torrent_info_search = re.search(pattern, torrent_full_name)
        if torrent_info_search:
            torrent_info_raw_from_db = get_info_from_db(torrent_info_search.group("search_name"))
            torrent_name = re.search("torrents/(.+?\.torrent)", t.torrentFile).group(1)
            # 变更部分信息（tv_ename,tv_season）,并交给multipart_data
            multipart_data = (
                ("type", ('', str(torrent_info_raw_from_db[1]))),
                ("second_type", ('', str(torrent_info_raw_from_db[2]))),
                ("file", (torrent_name, open(t.torrentFile, 'rb'), 'application/x-bittorrent')),
                ("tv_type", ('', str(torrent_info_raw_from_db[4]))),
                ("cname", ('', torrent_info_raw_from_db[5])),
                ("tv_ename", ('', torrent_info_search.group("full_name"))),
                ("tv_season", ('', torrent_info_search.group("tv_season"))),
                ("tv_filetype", ('', torrent_info_raw_from_db[8])),
                ("type", ('', str(torrent_info_raw_from_db[9]))),
                ("small_descr", ('', torrent_info_raw_from_db[10])),
                ("url", ('', torrent_info_raw_from_db[11])),
                ("dburl", ('', torrent_info_raw_from_db[12])),
                ("nfo", ('', torrent_info_raw_from_db[13])),
                ("descr", ('', torrent_info_raw_from_db[14])),
                ("uplver", ('', torrent_info_raw_from_db[15])),
            )
            post = requests.post(url="http://bt.byr.cn/takeupload.php", cookies=cookies, files=multipart_data)
            if post.url != "http://bt.byr.cn/takeupload.php":
                seed_torrent_download_id = re.search("id=(\d+)", post.url).group(1)
                download_torrent_link = "http://bt.byr.cn/download.php?id=" + seed_torrent_download_id
                torrent_file = requests.get(download_torrent_link, cookies=cookies)
                with open(setting.trans_watchdir + "/" + seed_torrent_download_id + ".torrent.get", "wb") as code:
                    code.write(torrent_file.content)
                os.rename(setting.trans_watchdir + "/" + seed_torrent_download_id + ".torrent.get",
                          setting.trans_watchdir + "/" + seed_torrent_download_id + ".torrent")
                time.sleep(5)
                new_torrent_id = tc.get_torrents()[-1].id
                while True:
                    if tc.get_torrent(new_torrent_id).status == 'seeding':
                        requests.post(url="http://bt.byr.cn/thanks.php", cookies=cookies,
                                      data={"id": str(seed_torrent_download_id)})
                        update_torrent_info_from_rpc_to_db()
                        break


def seed_judge():
    result = get_table_seed_list()
    for t in result:
        if t[2] == 0:
            get_torrent = tc.get_torrent(t[1])
            if get_torrent.status == "seeding":
                seed_post(t[1])
    update_torrent_info_from_rpc_to_db()


def main():
    while True:
        update_torrent_info_from_rpc_to_db()
        seed_judge()
        del_torrent_with_data_and_db()
        time.sleep(setting.sleep_time)


if __name__ == '__main__':
    main()
