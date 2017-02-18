#!/usr/bin/env python

import json
import re

import pymysql
import requests
from bs4 import BeautifulSoup
from Magnet_To_Torrent2 import magnet2torrent

class JSONObject:
    def __init__(self, d):
        self.__dict__ = d


model_setting_file = "model_rss_ZhuixinFan.json"

model_setting = json.loads(open(model_setting_file, "r").read(), object_hook=JSONObject)
main_setting = json.loads(open(model_setting.main_setting_loc, "r").read(), object_hook=JSONObject)

search_pattern = re.compile(
    "(?P<full_name>(?P<search_name>.+?)(?:\.| )(?P<tv_season>(?:[Ss]\d+)?[Ee][Pp]?\d+(?:-[Ee]?[Pp]?\d+)?).+-(?P<group>.+?))"
    "(?:\.(?P<tv_filetype>\w+)$|$)")


def serialize_instance(obj):
    d = {'last_check_id': obj.last_check_id}
    d.update(vars(obj))
    return d


def get_info_from_db(torrent_search_name):
    db = pymysql.connect(host=main_setting.db_address, port=main_setting.db_port,
                         user=main_setting.db_user, password=main_setting.db_password,
                         db=main_setting.db_name, charset='utf8')
    cursor = db.cursor()
    sql = "SELECT * FROM tv_info WHERE tv_ename='%s'" % torrent_search_name
    cursor.execute(sql)
    result = list(cursor.fetchall()[0])
    cursor.close()
    return result


def main():
    i = model_setting.last_check_id
    while True:
        bs_page = BeautifulSoup(
            requests.get("http://www.zhuixinfan.com/main.php?mod=viewresource&sid={0}".format(i)).text, "html5lib")
        i += 1
        series_name = bs_page.find("span", id="pdtname").get_text()
        if not series_name:
            break
        elif series_name.find('1280X720') > 0:
            try:
                search = re.search(search_pattern, series_name)
                torrent_info_raw_from_db = get_info_from_db(search.group("search_name"))
            except ValueError:
                continue
            except IndexError:
                continue
            else:
                magnet_link = bs_page.find("dd", id="torrent_url").get_text()
                # print(series_name,search_name,i,magnet_link)
                if magnet_link and torrent_info_raw_from_db:
                    magnet2torrent(magnet_link,
                                   output_name=main_setting.trans_watchdir + "/" + series_name + ".torrent")

    model_setting.last_check_id = i
    with open(model_setting_file, 'w') as f:
        json.dump(model_setting, f, default=serialize_instance, indent=4)


if __name__ == '__main__':
    main()