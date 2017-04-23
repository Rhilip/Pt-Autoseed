# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time
import logging
from logging.handlers import RotatingFileHandler

import transmissionrpc

import utils
import extractors

try:
    import usersetting as setting
except ImportError:
    import setting

logging_level = logging.INFO
if setting.logging_debug_level:
    logging_level = logging.DEBUG

log_formatter = logging.Formatter(fmt=setting.logging_format, datefmt=setting.logging_datefmt)

file_handler = RotatingFileHandler(filename=setting.logging_filename, mode='a', maxBytes=setting.logging_file_maxBytes,
                                   backupCount=2, encoding=None, delay=0)
file_handler.setLevel(logging_level)

autoseed_log = logging.getLogger('root')
autoseed_log.addHandler(file_handler)

tc = transmissionrpc.Client(address=setting.trans_address, port=setting.trans_port, user=setting.trans_user,
                            password=setting.trans_password)

db = utils.Database(setting)

autoseed = extractors.Autoseed(setting=setting)

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
                    if t.trackers[0]["announce"].find(autoseed.tracker_pattern) != -1:
                        sql = "UPDATE seed_list SET seed_id = '%d' WHERE id = '%d'" % (t.id, sort_id)
                        db.commit_sql(sql)
                elif t.trackers[0]["announce"].find(autoseed.tracker_pattern) == -1:
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


def seed_judge():
    """
    Judge to reseed depend on un-reseed torrent's status,
    With Database update after reseed.
    """
    result = db.get_table_seed_list(decision="WHERE seed_id = 0")  # Get un-reseed info from Database
    for t in result:  # Traversal seed_list
        try:
            dl_torrent = tc.get_torrent(t["download_id"])  # 获取下载种子信息
        except KeyError:  # 种子不存在了
            logging.error("The pre-reseed Torrent (which name: \"{0}\") isn't found in result,"
                          "It will be deleted from db in next delete-check time".format(t["title"]))
            continue
        else:
            torrent_full_name = dl_torrent.name
            logging.info("New get torrent: " + torrent_full_name)
            if dl_torrent.status == "seeding":  # 种子下载完成
                logging.info("The torrent is seeding now,Judge reseed or not.")
                if re.search(setting.search_series_pattern, torrent_full_name):
                    series_search_group = re.search(setting.search_series_pattern, torrent_full_name)
                    flag = autoseed.shunt_reseed(tr_client=tc, db_client=db, torrent=dl_torrent,
                                                 torrent_info_search=series_search_group, torrent_type="series")
                elif re.search(setting.search_anime_pattern, torrent_full_name):
                    anime_search_group = re.search(setting.search_anime_pattern, torrent_full_name)
                    flag = autoseed.shunt_reseed(tr_client=tc, db_client=db, torrent=dl_torrent,
                                                 torrent_info_search=anime_search_group, torrent_type="anime")
                else:  # 不符合，更新seed_id为-1
                    flag = -1
                    logging.warning("Mark Torrent {0} (Name: \"{1}\") As Un-reseed torrent,"
                                    "Stop watching it.".format(t["download_id"], torrent_full_name))

                if flag > 0 and setting.ServerChan_status:
                    server_chan.send_torrent_post_ok(tc.get_torrent(flag))

                update_sql = "UPDATE seed_list SET seed_id = {fl} WHERE download_id={tid}".format(fl=flag, tid=t["id"])
                db.commit_sql(update_sql)

            else:
                logging.warning("This torrent is still download.Wait until next check time.")


def main():
    logging.info("Autoseed start~")
    logging.warning("First time to run Byrbt-Autoseed,db check~")
    update_torrent_info_from_rpc_to_db(force_clean_check=True)
    i = 0
    while True:
        update_torrent_info_from_rpc_to_db()  # 更新表
        seed_judge()  # reseed判断主函数
        if i % setting.delete_check_round == 0:
            check_to_del_torrent_with_data_and_db()  # 清理种子

        if setting.web_show_status:  # 发种机运行状态展示
            decision = "WHERE seed_id != -1 ORDER BY id DESC LIMIT {sum}".format(sum=setting.web_show_entries_number)
            data_list = db.get_table_seed_list(decision=decision)
            utils.generate_web_json(setting=setting, tr_client=tc, data_list=data_list)

        sleep_time = setting.sleep_free_time
        if setting.busy_start_hour <= int(time.strftime("%H", time.localtime())) < setting.busy_end_hour:
            sleep_time = setting.sleep_busy_time

        logging.debug("Check time {0} OK,Will Sleep for {1} seconds.".format(str(i), str(sleep_time)))
        i += 1
        time.sleep(sleep_time)


if __name__ == '__main__':
    main()
