# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import re
import time
import os
import logging
from http.cookies import SimpleCookie  # Python3模块   （Py2: from Cookie import SimpleCookie）

import pymysql
import transmissionrpc
import requests
from bs4 import BeautifulSoup

from model.mediainfo import show_media_info


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

search_pattern = re.compile(
    "(?:[\W]+?\.|^)(?P<full_name>(?P<search_name>[\w\-. ]+?)(?:\.| )(?P<tv_season>(?:[Ss]\d+)|(?:(?:[Ss]\d+)?[Ee][Pp]?\d+(?:-[Ee]?[Pp]?\d+)?)).+-(?P<group>.+?))"
    "(?:\.(?P<tv_filetype>\w+)$|$)")

# 日志文件
if not os.path.exists("log"):
    os.makedirs("log")
logging.basicConfig(level=logging.INFO,
                    filename='log/autoseed_{0}.log'.format(time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())),
                    filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

# 种子简介头部通知信息
descr_header_bs = BeautifulSoup(open("descr_header.html", 'rb'), "html5lib")
# 根据setting.json中的信息（最小最大数值修改header）
descr_header_bs.find(id="min_reseed_time").string = str(int(setting.torrent_minSeedTime / 86400))
descr_header_bs.find(id="max_reseed_time").string = str(int(setting.torrent_maxSeedTime / 86400))


# 提交SQL语句
def commit_cursor_into_db(sql):
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        db.commit()
        cursor.close()
    except:
        logging.error("A commit to db ERROR,DDL: " + sql)
        db.rollback()


# 从数据库中找到最后的发布种子
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


# 从db获取seed_list
def get_table_seed_list():
    cursor = db.cursor()
    sql = "SELECT id,title,download_id,seed_id FROM seed_list"
    cursor.execute(sql)
    return_info = cursor.fetchall()
    cursor.close()
    return return_info


def update_torrent_info_from_rpc_to_db(force_clean_check=False):
    result = get_table_seed_list()
    title_list = []
    for i in result:
        title_list.append(i[1])
    if not force_clean_check:  # 正常更新
        last_seed_id = find_max("seed_id", "seed_list")
        for t in tc.get_torrents():
            if t.id > last_seed_id:
                if t.name in title_list:
                    sort_id = result[title_list.index(t.name)][0]
                    if t.trackers[0]["announce"].find("tracker.byr.cn") != -1:
                        sql = "UPDATE seed_list SET seed_id = '%d' WHERE id = '%d'" % (t.id, sort_id)
                        commit_cursor_into_db(sql)
                elif t.trackers[0]["announce"].find("tracker.byr.cn") == -1:
                    sql = "INSERT INTO seed_list (title,download_id,seed_id) VALUES ('%s','%d',0)" % (t.name, t.id)
                    commit_cursor_into_db(sql)
        logging.info("Update torrent info from rpc to db OK~")
    else:  # 第一次启动检查(force_clean_check)
        torrent_list_now_in_trans = tc.get_torrents()
        last_torrent_id_in_tran = 0
        for t in torrent_list_now_in_trans:
            if t.id > last_torrent_id_in_tran:
                last_torrent_id_in_tran = t.id
        last_torrent_id_in_db = max(find_max("download_id", "seed_list"), find_max("seed_id", "seed_list"))
        if not last_torrent_id_in_db == last_torrent_id_in_tran:  # 如果对不上，说明系统重新启动过或者tr崩溃过
            logging.error(
                "It seems that torrent's id in transmission didn't match with db-records,Clean the whole table \"seed_list\"")
            commit_cursor_into_db(sql="DELETE FROM seed_list")  # 直接清表
            # 清表后首次更新，这样可以在正常更新阶段（main中）保证(?)所有种子均插入表中。防止重复下载种子
            update_torrent_info_from_rpc_to_db()
        else:
            logging.info("The torrent's info in transmission match with db-records,DB check OK~")


# 从transmission和数据库中删除种子及其数据
def check_to_del_torrent_with_data_and_db():
    logging.info("Begin torrent's status check.If reach condition you set,You will get a warning.")
    result = get_table_seed_list()
    for t in result:
        try:  # 本处保证t[2],t[3]对应的种子仍存在
            tc.get_torrent(t[2])
            if t[3] > 0:
                seed_torrent = tc.get_torrent(t[3])
            else:
                continue     # t[3]<=0（且种子仍存在）的情况进入下一轮循环，不进入else
        except KeyError:  # 不存在的处理方法 - 删表，清种子
            logging.error("Torrent is not found,Witch name:\"{0}\",Will delete it's record from db".format(t[1]))
            commit_cursor_into_db(sql="DELETE FROM seed_list WHERE id = {0}".format(t[0]))
            tc.remove_torrent(t[2], delete_data=True)  # remove_torrent()不会因为种子不存在而出错
            tc.remove_torrent(t[3], delete_data=True)  # (错了也直接打log，不会崩)
        else:
            # 发布种子无上传速度  ->  达到最小做种时间  ->   达到最大做种时间  或者 最大分享率  -> 暂停种子
            if seed_torrent.status == "seeding" and seed_torrent.rateUpload == 0:
                if ((int(time.time()) - seed_torrent.addedDate) >= setting.torrent_minSeedTime) and (
                                seed_torrent.uploadRatio >= setting.torrent_maxUploadRatio or (
                                    int(time.time()) - seed_torrent.addedDate) >= setting.torrent_maxSeedTime):
                    tc.stop_torrent(t[3])
                    tc.stop_torrent(t[2])
                    logging.warning(
                        "Reach The Setting Seed time or ratio,Torrents (Which name:\"{0}\") will be delete"
                        "in next check time.".format(seed_torrent.name))
            if seed_torrent.status == "stopped":  # 前一轮暂停的种子 -> 删除种子及其文件，清理db条目
                logging.warning("Will delete torrent: {0} {1},Which name {2}".format(t[2], t[3], t[1]))
                commit_cursor_into_db(sql="DELETE FROM seed_list WHERE id = {0}".format(t[0]))
                tc.remove_torrent(t[3], delete_data=True)
                tc.remove_torrent(t[2], delete_data=True)
                logging.info("Delete torrents: {0} {1} ,Which name \"{2}\" OK.".format(t[2], t[3], t[1]))


# 从数据库中获取剧集简介（根据种子文件的search_name搜索数据库中的tv_ename）
def get_info_from_db(torrent_search_name):
    cursor = db.cursor()
    sql = "SELECT * FROM tv_info WHERE tv_ename='%s'" % torrent_search_name
    cursor.execute(sql)
    result = list(cursor.fetchall()[0])
    cursor.close()
    return result


# 如果种子在byr存在，返回种子id，不存在返回0
def exist_judge(torrent_info_search):
    full_name = torrent_info_search.group("full_name")
    exits_judge_raw = requests.get(
        url="http://bt.byr.cn/torrents.php?secocat=&cat=&incldead=0&spstate=0&inclbookmarked=0&search=" + full_name + "&search_area=0&search_mode=2",
        cookies=cookies)
    bs = BeautifulSoup(exits_judge_raw.text, "html5lib")
    tag = 0
    if bs.find_all("a", href=re.compile("download.php")):  # 如果存在（还有人比Autoseed快。。。
        href = bs.find_all("a", href=re.compile("download.php"))[0]["href"]
        tag = re.search("id=(\d+)", href).group(1)  # 找出种子id
    return tag


def download_reseed_torrent_and_update_tr_with_db(torrent_download_id, thanks=True):
    download_torrent_link = "http://bt.byr.cn/download.php?id=" + torrent_download_id
    torrent_file = requests.get(download_torrent_link, cookies=cookies)  # 下载种子
    with open(setting.trans_watchdir + "/" + torrent_download_id + ".torrent.get", "wb") as code:
        code.write(torrent_file.content)  # 保存种子文件到watch目录
    os.rename(setting.trans_watchdir + "/" + torrent_download_id + ".torrent.get",
              setting.trans_watchdir + "/" + torrent_download_id + ".torrent")  # 下载完成后，重命名成正确的后缀名
    logging.info("Download Torrent which id = " + torrent_download_id + "OK!")
    time.sleep(5)  # 等待transmission读取种子文件
    update_torrent_info_from_rpc_to_db()  # 更新数据库
    if thanks:
        requests.post(url="http://bt.byr.cn/thanks.php", cookies=cookies, data={"id": str(torrent_download_id)})  # 自动感谢


# 发布种子主函数
def seed_post(tid, torrent_info_search):
    if tc.get_torrent(tid).status == "seeding":  # 种子下载完成
        tag = exist_judge(torrent_info_search)
        if tag == 0:  # 种子不存在，则准备发布
            download_torrent = tc.get_torrent(tid)
            torrent_file_name = re.search("torrents/(.+?\.torrent)", download_torrent.torrentFile).group(1)
            try:
                torrent_info_raw_from_db = get_info_from_db(torrent_info_search.group("search_name"))  # 从数据库中获取该美剧信息
            except IndexError:  # 数据库没有该种子数据,使用备用剧集信息
                logging.warning(
                    "Not Find info from db of torrent: \"{0}\",Use normal template!!".format(download_torrent.name))
                torrent_info_raw_from_db = get_info_from_db("default")
            # 副标题 small_descr
            small_descr = "{0} {1}".format(torrent_info_raw_from_db[10], torrent_info_search.group("tv_season"))
            if str(torrent_info_search.group("group")).lower() == "fleet":
                small_descr += " |fleet慎下"
            # 简介 descr
            descr = str(descr_header_bs.fieldset) + "<br />" + torrent_info_raw_from_db[14]
            try:
                media_info = show_media_info(
                    file=setting.trans_downloaddir + "/" + download_torrent.files()[0]["name"])
            except IndexError:
                logging.warning("Can't get MediaInfo,Use raw descr.")
            else:
                if media_info:
                    descr += media_info
            # 提交表单
            multipart_data = (
                ("type", ('', str(torrent_info_raw_from_db[1]))),
                ("second_type", ('', str(torrent_info_raw_from_db[2]))),
                ("file", (torrent_file_name, open(download_torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
                ("tv_type", ('', str(torrent_info_raw_from_db[4]))),
                ("cname", ('', torrent_info_raw_from_db[5])),
                ("tv_ename", ('', torrent_info_search.group("full_name"))),
                ("tv_season", ('', torrent_info_search.group("tv_season"))),
                ("tv_filetype", ('', torrent_info_raw_from_db[8])),
                ("type", ('', str(torrent_info_raw_from_db[9]))),
                ("small_descr", ('', small_descr)),
                ("url", ('', torrent_info_raw_from_db[11])),
                ("dburl", ('', torrent_info_raw_from_db[12])),
                ("nfo", ('', torrent_info_raw_from_db[13])),  # 实际上并不是这样的，但是nfo一般没有，故这么写
                ("descr", ('', descr)),
                ("uplver", ('', torrent_info_raw_from_db[15])),
            )
            # 发布种子
            logging.info("Begin post The torrent {0},which name :{1}".format(tid, download_torrent.name))
            post = requests.post(url="http://bt.byr.cn/takeupload.php", cookies=cookies, files=multipart_data)
            if post.url != "http://bt.byr.cn/takeupload.php":  # 发布成功检查
                seed_torrent_download_id = re.search("id=(\d+)", post.url).group(1)  # 获取种子编号
                logging.info("Post OK,The torrent id in Byrbt :" + seed_torrent_download_id)
                download_reseed_torrent_and_update_tr_with_db(seed_torrent_download_id)  # 下载种子，并更新
        else:  # 如果种子存在（已经有人发布）  -> 辅种
            logging.warning("Find dupe torrent,which id: {0}.Ohhhhh".format(tag))
            download_reseed_torrent_and_update_tr_with_db(tag, thanks=False)
    else:
        logging.warning("This torrent is still download.Wait until next check time.")


# 发布判定
def seed_judge():
    result = get_table_seed_list()  # 从数据库中获取seed_list(tuple:(id,title,download_id,seed_id))
    for t in result:  # 遍历seed_list
        if t[3] == 0:  # 如果种子没有被重发布过(t[3] == 0)    ,另不发布(t[3] == -1)
            try:
                torrent = tc.get_torrent(t[2])  # 获取下载种子信息
            except KeyError:  # 种子不存在了
                logging.error(
                    "The pre-reseed Torrent (which name: \"{0}\") isn't found in result,"
                    "It will be deleted from db in next delete-check time".format(t[1]))
                continue
            else:
                torrent_full_name = torrent.name
                logging.info("New get torrent: " + torrent_full_name)
                torrent_info_search = re.search(search_pattern, torrent_full_name)
                if torrent_info_search:  # 如果种子名称结构符合search_pattern（即属于剧集）
                    seed_post(t[2], torrent_info_search)  # 发布种子
                else:  # 不符合，更新seed_id为-1
                    logging.info("Mark Torrent {0} (Name: \"{1}\") As Un-reseed torrent,Stop watching it.".format(t[2],
                                                                                                                  torrent_full_name))
                    commit_cursor_into_db("UPDATE seed_list SET seed_id = -1 WHERE id='%d'" % t[0])


# 生成展示信息
def generate_web_json():
    result = list(get_table_seed_list())
    result.reverse()  # 倒置展示
    data = []
    for t in result:
        if t[3] != -1:  # 对于不发布的种子不展示
            try:
                download_torrent = tc.get_torrent(t[2])
                if t[3] == 0:
                    reseed_status = "Not found."
                    reseed_ratio = 0
                else:
                    reseed_torrent = tc.get_torrent(t[3])
                    reseed_status = reseed_torrent.status
                    reseed_ratio = reseed_torrent.uploadRatio
            except KeyError:
                logging.error("This torrent (Which name: {0}) has been deleted from transmission (By other "
                              "Management software).".format(t[1]))
                continue
            else:
                info_dict = {
                    "title": download_torrent.name,
                    "size": "{:.2f} MiB".format(download_torrent.totalSize / (1024 * 1024)),
                    "download_start_time": time.strftime("%Y-%m-%d %H:%M:%S",
                                                         time.localtime(download_torrent.addedDate)),
                    "download_status": download_torrent.status,
                    "download_upload_ratio": "{:.2f}".format(download_torrent.uploadRatio),
                    "reseed_status": reseed_status,
                    "reseed_ratio": "{:.2f}".format(reseed_ratio)
                }
            data.append((t[0], info_dict))
    out_list = {
        "last_update_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "data": data
    }
    with open(setting.web_loc + "/tostatus.json", "wt") as f:
        json.dump(out_list, f)


def main():
    logging.info("Autoseed start~")
    i = 0
    while True:
        if i == 0:  # 第一次启动时清除数据表seed_list(因为每次启动tr，种子的id都不同)
            logging.warning("First time to run Byrbt-Autoseed,db check~")
            update_torrent_info_from_rpc_to_db(force_clean_check=True)
        update_torrent_info_from_rpc_to_db()  # 更新表
        seed_judge()  # reseed判断主函数
        if i % 5 == 0:  # 每5次运行检查一遍
            check_to_del_torrent_with_data_and_db()  # 清理种子
        generate_web_json()  # 生成展示信息
        now_hour = int(time.strftime("%H", time.localtime()))
        if 8 <= now_hour < 16:  # 这里假定8:00-16:00为美剧更新的频繁期
            sleep_time = setting.sleep_busy_time
        else:  # 其他时间段
            sleep_time = setting.sleep_free_time
        logging.info("Check time {0} OK,Will Sleep for {1} seconds.".format(str(i), str(sleep_time)))
        time.sleep(sleep_time)
        i += 1


if __name__ == '__main__':
    main()
