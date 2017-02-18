#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import os

import pymysql
import requests
from bs4 import BeautifulSoup
from model.Magnet_To_Torrent import magnet2torrent


class JSONObject:
    def __init__(self, d):
        self.__dict__ = d


model_setting_file = "{0}/model_rss_ZhuixinFan.json".format(os.getcwd())

model_setting = json.loads(open(model_setting_file, "r").read(), object_hook=JSONObject)
main_setting = json.loads(open(model_setting.main_setting_loc, "r").read(), object_hook=JSONObject)

search_pattern = re.compile(
    "(?P<full_name>(?P<search_name>.+?)(?:\.| )(?P<tv_season>(?:[Ss]\d+)?[Ee][Pp]?\d+(?:-[Ee]?[Pp]?\d+)?).+-(?P<group>.+?))"
    "(?:\.(?P<tv_filetype>\w+)$|$)")


def serialize_instance(obj):
    d = {'last_check_id': obj.last_check_id}
    d.update(vars(obj))
    return d


def get_table_tv_ename_list():
    db = pymysql.connect(host=main_setting.db_address, port=main_setting.db_port,
                         user=main_setting.db_user, password=main_setting.db_password,
                         db=main_setting.db_name, charset='utf8')
    cursor = db.cursor()
    cursor.execute("SELECT tv_ename FROM tv_info")
    return_title_raw = cursor.fetchall()
    return_title = []
    for i in return_title_raw:
        return_title.append(i[0])
    db.close()
    return return_title


def main():
    i = model_setting.last_check_id
    title_list = get_table_tv_ename_list()
    while True:
        bs_page = BeautifulSoup(
            requests.get("http://www.zhuixinfan.com/main.php?mod=viewresource&sid={0}".format(i)).text, "html5lib")
        series_name = bs_page.find("span", id="pdtname").get_text()
        if not series_name:
            break
        elif series_name.find('1280X720') > 0:
            i += 1
            try:
                search = re.search(search_pattern, series_name)
            except AttributeError:
                continue
            else:
                search_name = search.group("search_name")
                try:
                    title_list.index(search_name)
                except ValueError:
                    continue
                else:
                    magnet_link = bs_page.find("dd", id="torrent_url").get_text()
                    magnet2torrent(magnet_link, output_name=main_setting.trans_watchdir + "/" + re.search(r"urn\:btih\:(?P<code>\w+)", magnet_link).group("code") + ".torrent")

    model_setting.last_check_id = i
    with open(model_setting_file, 'w') as f:
        json.dump(model_setting, f, default=serialize_instance, indent=4)


if __name__ == '__main__':
    main()
