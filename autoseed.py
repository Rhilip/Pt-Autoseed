# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time
import logging

import transmissionrpc

import utils
import site

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

autoseed = site.Autoseed(setting=setting)

server_chan = utils.ServerChan(setting.ServerChan_SCKEY)

search_series_pattern = re.compile(setting.search_series_pattern)
search_anime_pattern = re.compile(setting.search_anime_pattern)

logging.debug("Initialization settings Success~")


def update_torrent_info_from_rpc_to_db(force_clean_check=False):
    # TODO Optimization logic
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
        last_id_tran = 0
        for t in torrent_list_now_in_trans:
            if t.id > last_id_tran:
                last_id_tran = t.id
        last_id_db = max(db.get_max_in_column("seed_list", "download_id"), db.get_max_in_column("seed_list", "seed_id"))
        logging.debug("torrent count: transmission: {tr},db-record: {db}.".format(tr=last_id_tran, db=last_id_db))
        if not last_id_db == last_id_tran:  # 如果对不上，说明系统重新启动过或者tr崩溃过
            logging.error(
                "It seems that torrent's id in transmission didn't match with db-records,"
                "Clean the whole table \"seed_list\"")
            db.commit_sql(sql="DELETE FROM seed_list")  # 直接清表
            # 清表后首次更新，这样可以在正常更新阶段（main中）保证(?)所有种子均插入表中。防止重复下载种子
            update_torrent_info_from_rpc_to_db()
        else:
            logging.info("The torrent's info in transmission match with db-records,DB check OK~")


def check_to_del_torrent_with_data_and_db():
    """Delete torrent(both download and reseed) with data from transmission and database"""
    logging.debug("Begin torrent's status check.If reach condition you set,You will get a warning.")
    result = db.get_table_seed_list(decision="WHERE seed_id > 0")
    for t in result:
        try:  # Ensure torrent exist
            tc.get_torrent(t["download_id"])
            seed_torrent = tc.get_torrent(t["seed_id"])
        except KeyError:  # 不存在的处理方法 - 删表，清种子
            db.commit_sql(sql="DELETE FROM seed_list WHERE id = {0}".format(t["id"]))
            tc.remove_torrent(t["download_id"], delete_data=True)  # remove_torrent()不会因为种子不存在而出错
            tc.remove_torrent(t["seed_id"], delete_data=True)  # (错了也直接打log，不会崩)
            logging.error("Torrent is not found,Witch name:\"{0}\",Delete it's record from db".format(t["title"]))
        else:
            seed_status = seed_torrent.status
            if setting.pre_delete_judge(seed_status, time.time(), seed_torrent.addedDate, seed_torrent.uploadRatio):
                tc.stop_torrent(t["download_id"])
                tc.stop_torrent(t["seed_id"])
                logging.warning("Reach Target you set,Torrents({0}) will be delete.".format(seed_torrent.name))
            if seed_status == "stopped":  # 前一轮暂停的种子 -> 删除种子及其文件，清理db条目
                db.commit_sql(sql="DELETE FROM seed_list WHERE id = {0}".format(t["id"]))
                tc.remove_torrent(t["download_id"], delete_data=True)
                tc.remove_torrent(t["seed_id"], delete_data=True)
                logging.info("Delete torrents,Which name: \"{0}\" OK.".format(t["title"]))


def data_series_raw2tuple(download_torrent) -> tuple:
    # TODO move to site.byrbt,and Split this function
    torrent_info_search = re.search(search_series_pattern, download_torrent.name)
    torrent_file_name = re.search("torrents/(.+?\.torrent)", download_torrent.torrentFile).group(1)

    torrent_raw_info_dict = db.data_raw_info(torrent_info_search, table="info_series", column="tv_ename")

    # 副标题 small_descr
    small_descr = "{0} {1}".format(torrent_raw_info_dict["small_descr"], torrent_info_search.group("tv_season"))
    if str(torrent_info_search.group("group")).lower() == "fleet":
        small_descr += " |fleet慎下"

    file = setting.trans_downloaddir + "/" + download_torrent.files()[0]["name"]
    screenshot_file = "screenshot/{file}.png".format(file=str(download_torrent.files()[0]["name"]).split("/")[-1])

    # 简介 descr
    descr = """{before}{raw}{screenshot}{mediainfo}{clone_info}""" \
        .format(before=setting.descr_before(),
                raw=torrent_raw_info_dict["descr"],
                screenshot=utils.screenshot(setting, screenshot_file, file),
                mediainfo=utils.show_media_info(setting, file=file),
                clone_info=setting.descr_clone_info(before_torrent_id=torrent_raw_info_dict["before_torrent_id"]))

    return (  # Submit form
        ("type", ('', str(torrent_raw_info_dict["type"]))),
        ("second_type", ('', str(torrent_raw_info_dict["second_type"]))),
        ("file", (torrent_file_name, open(download_torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
        ("tv_type", ('', str(torrent_raw_info_dict["tv_type"]))),
        ("cname", ('', torrent_raw_info_dict["cname"])),
        ("tv_ename", ('', torrent_info_search.group("full_name"))),
        ("tv_season", ('', torrent_info_search.group("tv_season"))),
        ("tv_filetype", ('', torrent_raw_info_dict["tv_filetype"])),
        ("type", ('', str(torrent_raw_info_dict["type"]))),
        ("small_descr", ('', small_descr)),
        ("url", ('', torrent_raw_info_dict["url"])),
        ("dburl", ('', torrent_raw_info_dict["dburl"])),
        ("nfo", ('', torrent_raw_info_dict["nfo"])),  # 实际上并不是这样的，但是nfo一般没有，故这么写
        ("descr", ('', descr)),
        ("uplver", ('', torrent_raw_info_dict["uplver"])),
    )


def seed_judge():
    """发布判定"""
    result = db.get_table_seed_list(decision="WHERE seed_id = 0")  # Get un-reseed info from Database
    for t in result:  # Traversal seed_list
        try:
            download_torrent = tc.get_torrent(t["download_id"])  # 获取下载种子信息
        except KeyError:  # 种子不存在了
            logging.error("The pre-reseed Torrent (which name: \"{0}\") isn't found in result,"
                          "It will be deleted from db in next delete-check time".format(t["title"]))
            continue
        else:
            torrent_full_name = download_torrent.name
            logging.info("New get torrent: " + torrent_full_name)
            if download_torrent.status == "seeding":  # 种子下载完成
                # TODO Anime
                torrent_info_search = re.search(search_series_pattern, torrent_full_name)
                if torrent_info_search:  # 如果种子名称结构符合search_pattern（即属于剧集）
                    tag = autoseed.exist_judge(torrent_info_search.group("full_name"), torrent_info_search.group(0))
                    if tag == 0:  # 种子不存在，则准备发布
                        logging.info("Begin post The torrent {0},which name: {1}".format(t["download_id"],
                                                                                         download_torrent.name))
                        flag = autoseed.post_torrent(tr_client=tc,
                                                     multipart_data=data_series_raw2tuple(download_torrent))
                        if flag < 0:
                            db.commit_sql(
                                "UPDATE seed_list SET seed_id = -1 WHERE download_id={:d}".format(t["download_id"]))
                        else:
                            db.commit_sql(
                                "UPDATE seed_list SET seed_id = {flag} WHERE download_id={tid}".format(flag=flag, tid=t[
                                    "download_id"]))
                            if setting.ServerChan_status:
                                server_chan.send_torrent_post_ok(dl_torrent=download_torrent)
                    elif tag == -1:  # 如果种子存在，但种子不一致
                        db.commit_sql(
                            "UPDATE seed_list SET seed_id = -1 WHERE download_id={:d}".format(t["download_id"]))
                        logging.warning(
                            "Find dupe torrent,and the exist torrent's title is not the same as pre-reseed torrent."
                            "Stop Posting~")
                    else:  # 如果种子存在（已经有人发布）  -> 辅种
                        autoseed.download_torrent(tr_client=tc, tid=tag, thanks=False)
                        logging.warning("Find dupe torrent,which id: {0},assist it~".format(tag))
                else:  # 不符合，更新seed_id为-1
                    db.commit_sql("UPDATE seed_list SET seed_id = -1 WHERE id='{:d}'".format(t["id"]))
                    logging.warning("Mark Torrent {0} (Name: \"{1}\") As Un-reseed torrent,"
                                    "Stop watching it.".format(t["download_id"], torrent_full_name))
            else:
                logging.warning("This torrent is still download.Wait until next check time.")


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
