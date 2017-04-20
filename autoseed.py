# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time
import os
import logging
from http.cookies import SimpleCookie  # Python3模块   （Py2: from Cookie import SimpleCookie）

import transmissionrpc
import requests
from bs4 import BeautifulSoup

import utils

try:
    import usersetting as setting
except ImportError:
    import setting

logging_level = logging.INFO
if setting.logging_debug_level:
    logging_level = logging.DEBUG

logging.basicConfig(level=logging_level, format=setting.logging_format, datefmt=setting.logging_datefmt)

tc = transmissionrpc.Client(address=setting.trans_address, port=setting.trans_port, user=setting.trans_user,
                            password=setting.trans_password)

db = utils.Database(setting)

cookie = SimpleCookie(setting.byr_cookies)
cookies = {}
for key, morsel in cookie.items():
    cookies[key] = morsel.value

server_chan = utils.ServerChan(setting.ServerChan_SCKEY)

search_pattern = re.compile(setting.search_series_pattern)
logging.debug("Initialization settings Success~")


def update_torrent_info_from_rpc_to_db(force_clean_check=False):
    result = db.get_table_seed_list()
    title_list = []
    for i in result:
        title_list.append(i[1])
    if not force_clean_check:  # 正常更新
        last_seed_id = db.get_max_in_column("seed_list", "seed_id")
        for t in tc.get_torrents():
            if t.id > last_seed_id:
                if t.name in title_list:
                    sort_id = result[title_list.index(t.name)][0]
                    if t.trackers[0]["announce"].find("tracker.byr.cn") != -1:
                        sql = "UPDATE seed_list SET seed_id = '%d' WHERE id = '%d'" % (t.id, sort_id)
                        db.commit_sql(sql)
                elif t.trackers[0]["announce"].find("tracker.byr.cn") == -1:
                    sql = "INSERT INTO seed_list (title,download_id,seed_id) VALUES ('%s','%d',0)" % (t.name, t.id)
                    db.commit_sql(sql)
        logging.debug("Update torrent info from rpc to db OK~")
    else:  # 第一次启动检查(force_clean_check)
        torrent_list_now_in_trans = tc.get_torrents()
        last_torrent_id_in_tran = 0
        for t in torrent_list_now_in_trans:
            if t.id > last_torrent_id_in_tran:
                last_torrent_id_in_tran = t.id
        last_torrent_id_in_db = max(db.get_max_in_column("seed_list", "download_id"),
                                    db.get_max_in_column("seed_list", "seed_id"))
        if not last_torrent_id_in_db == last_torrent_id_in_tran:  # 如果对不上，说明系统重新启动过或者tr崩溃过
            logging.error(
                "It seems that torrent's id in transmission didn't match with db-records,"
                "Clean the whole table \"seed_list\"")
            db.commit_sql(sql="DELETE FROM seed_list")  # 直接清表
            # 清表后首次更新，这样可以在正常更新阶段（main中）保证(?)所有种子均插入表中。防止重复下载种子
            update_torrent_info_from_rpc_to_db()
        else:
            logging.info("The torrent's info in transmission match with db-records,DB check OK~")


# 从transmission和数据库中删除种子及其数据
def check_to_del_torrent_with_data_and_db():
    logging.debug("Begin torrent's status check.If reach condition you set,You will get a warning.")
    result = db.get_table_seed_list(decision="WHERE seed_id > 0")
    for t in result:
        try:  # 本处保证t[2],t[3]对应的种子仍存在
            tc.get_torrent(t[2])
            seed_torrent = tc.get_torrent(t[3])
        except KeyError:  # 不存在的处理方法 - 删表，清种子
            logging.error("Torrent is not found,Witch name:\"{0}\",Will delete it's record from db".format(t[1]))
            db.commit_sql(sql="DELETE FROM seed_list WHERE id = {0}".format(t[0]))
            tc.remove_torrent(t[2], delete_data=True)  # remove_torrent()不会因为种子不存在而出错
            tc.remove_torrent(t[3], delete_data=True)  # (错了也直接打log，不会崩)
        else:
            seed_status = seed_torrent.status
            if setting.pre_delete_judge(seed_status, time.time(), seed_torrent.addedDate, seed_torrent.uploadRatio):
                tc.stop_torrent(t[3])
                tc.stop_torrent(t[2])
                logging.warning("Reach Target you set,Torrents({0}) will be delete.".format(seed_torrent.name))
            if seed_status == "stopped":  # 前一轮暂停的种子 -> 删除种子及其文件，清理db条目
                db.commit_sql(sql="DELETE FROM seed_list WHERE id = {0}".format(t[0]))
                tc.remove_torrent(t[3], delete_data=True)
                tc.remove_torrent(t[2], delete_data=True)
                logging.info("Delete torrents: {0} {1} ,Which name: \"{2}\" OK.".format(t[2], t[3], t[1]))


# 如果种子在byr存在，返回种子id，不存在返回0，已存在且种子一致返回种子号，不一致返回-1
def exist_judge(search_title, torrent_file_name):
    exits_judge_raw = requests.get(
        url="http://bt.byr.cn/torrents.php?secocat=&cat=&incldead=0&spstate=0&inclbookmarked=0&search="
            + search_title + "&search_area=0&search_mode=2",
        cookies=cookies)
    bs = BeautifulSoup(exits_judge_raw.text, "lxml")
    tag = 0
    if bs.find_all("a", href=re.compile("download.php")):  # 如果存在（还有人比Autoseed快。。。
        href = bs.find_all("a", href=re.compile("download.php"))[0]["href"]
        tag_temp = re.search("id=(\d+)", href).group(1)  # 找出种子id
        # 使用待发布种子全名匹配已有种子的名称
        details_page = requests.get("http://bt.byr.cn/details.php?id={0}&hit=1".format(tag_temp), cookies=cookies)
        details_bs = BeautifulSoup(details_page.text, "lxml")
        torrent_title_in_site = details_bs.find("a", class_="index", href=re.compile(r"^download.php")).string
        torrent_title = re.search(r"\[BYRBT\]\.(.+?\.torrent)", torrent_title_in_site).group(1)
        if torrent_file_name == torrent_title:  # 如果匹配，返回种子号
            tag = tag_temp
        else:  # 如果不匹配，返回-1
            tag = -1
    return tag


def download_reseed_torrent_and_update_tr_with_db(torrent_download_id, thanks=True):
    download_torrent_link = "http://bt.byr.cn/download.php?id=" + torrent_download_id
    torrent_file = requests.get(download_torrent_link, cookies=cookies)  # 下载种子
    with open(setting.trans_watchdir + "/" + torrent_download_id + ".torrent.get", "wb") as code:
        code.write(torrent_file.content)  # 保存种子文件到watch目录
    os.rename(setting.trans_watchdir + "/" + torrent_download_id + ".torrent.get",
              setting.trans_watchdir + "/" + torrent_download_id + ".torrent")  # 下载完成后，重命名成正确的后缀名
    logging.info("Download Torrent which id = {id} OK!".format(id=torrent_download_id))
    time.sleep(5)  # 等待transmission读取种子文件
    update_torrent_info_from_rpc_to_db()  # 更新数据库
    if thanks:
        requests.post(url="http://bt.byr.cn/thanks.php", cookies=cookies, data={"id": str(torrent_download_id)})  # 自动感谢


# 发布种子主函数
def seed_post(tid, multipart_data: tuple):
    flag = 0
    post = requests.post(url="http://bt.byr.cn/takeupload.php", cookies=cookies, files=multipart_data)
    if post.url != "http://bt.byr.cn/takeupload.php":  # 发布成功检查
        seed_torrent_download_id = re.search("id=(\d+)", post.url).group(1)  # 获取种子编号
        logging.info("Post OK,The torrent id in Byrbt: {id}".format(seed_torrent_download_id))
        download_reseed_torrent_and_update_tr_with_db(seed_torrent_download_id)  # 下载种子，并更新
        flag = seed_torrent_download_id
    else:  # 未发布成功打log
        outer_bs = BeautifulSoup(post.text, "lxml").find("td", id="outer")
        if outer_bs.find_all("table"):  # 移除不必要的table信息
            for table in outer_bs.find_all("table"):
                table.extract()
        outer_message = outer_bs.get_text().replace("\n", "")
        logging.error("Upload this torrent Error,The Server echo:\"{0}\",Stop Posting".format(outer_message))
        db.commit_sql("UPDATE seed_list SET seed_id = -1 WHERE download_id='%d'" % tid)
    return flag


def data_series_raw2tuple(download_torrent) -> tuple:
    torrent_info_search = re.search(search_pattern, download_torrent.name)
    torrent_file_name = re.search("torrents/(.+?\.torrent)", download_torrent.torrentFile).group(1)
    try:  # 从数据库中获取该美剧信息
        search_name = torrent_info_search.group("search_name")
        torrent_info_raw_from_db = db.get_raw_info(search_name, table="tv_info", column="tv_ename")
    except IndexError:  # 数据库没有该种子数据,使用备用剧集信息
        logging.warning("Not Find info from db of torrent: \"{0}\",Use normal template!!".format(download_torrent.name))
        torrent_info_raw_from_db = db.get_raw_info("default", table="tv_info", column="tv_ename")

    # 副标题 small_descr
    small_descr = "{0} {1}".format(torrent_info_raw_from_db[10], torrent_info_search.group("tv_season"))
    if str(torrent_info_search.group("group")).lower() == "fleet":
        small_descr += " |fleet慎下"
    # 简介 descr
    descr = setting.descr_before + torrent_info_raw_from_db[14]

    file = setting.trans_downloaddir + "/" + download_torrent.files()[0]["name"]

    # TODO Screen shot
    screenshot_file = "screenshot/{file}.png".format(file=str(download_torrent.files()[0]["name"]).split("/")[-1])
    ffmpeg_sh = "ffmpeg -ss 00:10:10 -y -i {file} -vframes 1 {web_loc}/{s_file}".format(file=file,
                                                                                        web_loc=setting.web_loc,
                                                                                        s_file=screenshot_file)
    screenshot = os.system(ffmpeg_sh)
    if screenshot == 0:
        descr += setting.descr_screenshot(url="{web_url}/{s_f}".format(web_url=setting.web_url, s_f=screenshot_file))
    else:
        logging.warning("Can't get Screenshot for \"{0}\".".format(torrent_info_search.group(0)))

    # MediaInfo
    try:
        media_info = utils.show_media_info(file=file)
    except IndexError:
        logging.warning("Can't get MediaInfo for \"{0}\"".format(torrent_info_search.group(0)))
    else:
        if media_info:
            descr += setting.descr_mediainfo(info=media_info)

    descr += setting.descr_clone_info(before_torrent_id=torrent_info_raw_from_db[16])

    return (  # 提交表单
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


# 发布判定
def seed_judge():
    # 从数据库中获取seed_list(tuple:(id,title,download_id,seed_id))
    result = db.get_table_seed_list(decision="WHERE seed_id = 0")
    for t in result:  # 遍历seed_list
        try:
            download_torrent = tc.get_torrent(t[2])  # 获取下载种子信息
        except KeyError:  # 种子不存在了
            logging.error("The pre-reseed Torrent (which name: \"{0}\") isn't found in result,"
                          "It will be deleted from db in next delete-check time".format(t[1]))
            continue
        else:
            torrent_full_name = download_torrent.name
            torrent_file_name = re.search("torrents/(.+?\.torrent)", download_torrent.torrentFile).group(1)
            logging.info("New get torrent: " + torrent_full_name)
            if download_torrent.status == "seeding":  # 种子下载完成
                torrent_info_search = re.search(search_pattern, torrent_full_name)
                if torrent_info_search:  # 如果种子名称结构符合search_pattern（即属于剧集）
                    tag = exist_judge(torrent_info_search.group("full_name"), torrent_file_name)
                    if tag == 0:  # 种子不存在，则准备发布
                        logging.info("Begin post The torrent {0},which name: {1}".format(t[2], download_torrent.name))
                        t_id = seed_post(t[2], data_series_raw2tuple(download_torrent))
                        if t_id is not 0 and setting.ServerChan_status:
                            server_chan.send_torrent_post_ok(dl_torrent=download_torrent)
                    elif tag == -1:  # 如果种子存在，但种子不一致
                        logging.warning(
                            "Find dupe torrent,and the exist torrent's title is not the same as pre-reseed torrent."
                            "Stop Posting~")
                        db.commit_sql("UPDATE seed_list SET seed_id = -1 WHERE download_id='%d'" % t[2])
                    else:  # 如果种子存在（已经有人发布）  -> 辅种
                        logging.warning("Find dupe torrent,which id: {0},will assist it~".format(tag))
                        download_reseed_torrent_and_update_tr_with_db(tag, thanks=False)
                else:
                    logging.warning("This torrent is still download.Wait until next check time.")
            else:  # 不符合，更新seed_id为-1
                logging.warning("Mark Torrent {0} (Name: \"{1}\") As Un-reseed torrent,"
                                "Stop watching it.".format(t[2], torrent_full_name))
                db.commit_sql("UPDATE seed_list SET seed_id = -1 WHERE id='%d'" % t[0])


def main():
    logging.info("Autoseed start~")
    i = 0
    while True:
        if i == 0:  # 第一次启动时清除数据表seed_list(因为每次启动tr，种子的id都不同)
            logging.warning("First time to run Byrbt-Autoseed,db check~")
            update_torrent_info_from_rpc_to_db(force_clean_check=True)
        update_torrent_info_from_rpc_to_db()  # 更新表
        seed_judge()  # reseed判断主函数
        if i % setting.delete_check_round == 0:
            check_to_del_torrent_with_data_and_db()  # 清理种子

        if setting.web_show_status:  # 发种机运行状态展示
            data_list = db.get_table_seed_list(
                decision="WHERE seed_id != -1 ORDER BY id DESC LIMIT {sum}".format(sum=setting.web_show_entries_number))
            utils.generate_web_json(setting=setting, tr_client=tc, data_list=data_list)

        if setting.busy_start_hour <= int(time.strftime("%H", time.localtime())) < setting.busy_end_hour:
            sleep_time = setting.sleep_busy_time
        else:  # 其他时间段
            sleep_time = setting.sleep_free_time

        logging.debug("Check time {0} OK,Will Sleep for {1} seconds.".format(str(i), str(sleep_time)))

        time.sleep(sleep_time)
        i += 1


if __name__ == '__main__':
    main()
