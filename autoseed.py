# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time
import logging
from logging.handlers import RotatingFileHandler

import utils
import transmissionrpc
from extractors import Autoseed

try:
    import usersetting as setting
except ImportError:
    import setting

# -*- Logging Setting -*-
logging_level = logging.INFO
if setting.logging_debug_level:
    logging_level = logging.DEBUG

logFormatter = logging.Formatter(fmt=setting.logging_format, datefmt=setting.logging_datefmt)
rootLogger = logging.getLogger('')
rootLogger.setLevel(logging.NOTSET)

fileHandler = RotatingFileHandler(filename=setting.logging_filename, mode='a', backupCount=2,
                                  maxBytes=setting.logging_file_maxBytes, encoding=None, delay=0)
fileHandler.setFormatter(logFormatter)
fileHandler.setLevel(logging_level)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
# -*- End of Logging Setting -*-

# -*- Loading Model -*-
tc = transmissionrpc.Client(address=setting.trans_address, port=setting.trans_port,
                            user=setting.trans_user, password=setting.trans_password)
db = utils.Database(setting)
autoseed = Autoseed(setting=setting, tr_client=tc, db_client=db)
# -*- End of Loading Model -*-

logging.info("Initialization settings Success~")


def tracker_condition(condition, raw_trakcer_list=autoseed.reseed_tracker_list) -> list:
    tracker_list_judge = []
    for i in raw_trakcer_list:
        tracker_list_judge.append("`{j}` {con}".format(j=i, con=condition))
    return tracker_list_judge


def update_torrent_info_from_rpc_to_db(last_id_check=0, force_clean_check=False):
    # check torrent id both in transmission and database
    last_id_tran = last_id_check
    torrent_now_in_tran = tc.get_torrents()
    for t in torrent_now_in_tran:
        if t.id > last_id_tran:
            last_id_tran = t.id
    last_id_db = db.get_max_in_column(table="seed_list", column_list=["download_id"] + autoseed.reseed_tracker_list)
    logging.debug("Torrent max-id count: transmission: {tr},db-record: {db}.".format(tr=last_id_tran, db=last_id_db))

    if last_id_tran != last_id_db:
        if not force_clean_check:  # Normal Update
            logging.info("Some new torrents were add to transmission,Sync to db~")
            result = db.get_table_seed_list()
            title_list = []
            for cow in result:
                title_list.append(cow["title"])
            for i in range(last_id_db + 1, last_id_tran + 1):
                try:
                    t = tc.get_torrent(i)
                except KeyError:  # Not exist torrent
                    logging.error("The pre-syncing Torrent(id: {i}) isn't found in result,Please check.".format(i=i))
                else:
                    to_tracker_host = re.search(r"http[s]?://(.+?)/", t.trackers[0]["announce"]).group(1)
                    if t.name in title_list:
                        sid = result[title_list.index(t.name)]["id"]
                        if to_tracker_host in autoseed.reseed_tracker_list:
                            sql = "UPDATE seed_list SET `{}` = {:d} WHERE id = {:d}".format(to_tracker_host, t.id, sid)
                            db.commit_sql(sql)
                    elif to_tracker_host not in autoseed.reseed_tracker_list:
                        sql = "INSERT INTO seed_list (title,download_id) VALUES ('{}',{:d})".format(t.name, t.id)
                        db.commit_sql(sql)
        else:  # 第一次启动检查(force_clean_check)
            logging.error("It seems the torrent list didn't match with db-records,Clean the \"seed_list\" for safety.")
            db.commit_sql(sql="DELETE FROM seed_list")  # Delete all line from seed_list
            update_torrent_info_from_rpc_to_db()
    else:
        logging.debug("The torrent's info in transmission match with db-records,DB check OK~")

    return last_id_tran


def check_to_del_torrent_with_data_and_db():
    """Delete torrent(both download and reseed) with data from transmission and database"""
    logging.debug("Begin torrent's status check.If reach condition you set,You will get a warning.")
    result = db.get_table_seed_list(decision='WHERE {0}'.format(' AND '.join(tracker_condition(condition=">0"))))
    for cow in result:
        sid = cow.pop("id")
        s_title = cow.pop("title")
        try:  # Ensure torrent exist
            reseed_list = []
            for tracker, tid in cow.items():
                reseed_list.append(tc.get_torrent(torrent_id=tid))
        except KeyError:  # 不存在的处理方法 - 删表，清种子
            logging.error("One of Torrents may not found,Witch name:\"{0}\",Delete all record from db".format(s_title))
            for tracker, tid in cow.items():
                tc.remove_torrent(tid, delete_data=True)
            db.commit_sql(sql="DELETE FROM seed_list WHERE id = {0}".format(sid))
        else:
            reseed_stop_list = []
            for seed_torrent in reseed_list:
                seed_status = seed_torrent.status
                if setting.pre_delete_judge(seed_status, time.time()):
                    tc.stop_torrent(seed_torrent.id)
                    logging.warning("Reach Target you set,Torrents({0}) will be delete.".format(seed_torrent.name))
                if seed_status == "stopped":  # 前一轮暂停的种子 -> 标记
                    reseed_stop_list.append(seed_torrent)
            if len(reseed_list) == len(reseed_stop_list):  # 全部reseed种子达到分享目标 -> 删除种子及其文件，清理db条目
                logging.info("All torrents reach target,Which name: \"{0}\" ,DELETE them with data.".format(s_title))
                db.commit_sql(sql="DELETE FROM seed_list WHERE id = {0}".format(sid))
                for reseed_torrent in reseed_list:
                    tc.remove_torrent(reseed_torrent.id)


def seed_judge():
    """Judge to reseed depend on un-reseed torrent's status,With Database update after reseed."""
    result = db.get_table_seed_list(decision='WHERE {0}'.format(' OR '.join(tracker_condition(condition="=0"))))
    for t in result:  # Traversal all unseed_list
        try:
            dl_torrent = tc.get_torrent(t["download_id"])  # 获取下载种子信息
        except KeyError:  # 种子不存在了
            logging.error("The pre-reseed Torrent (which name: \"{0}\") isn't found in result,"
                          "It will be deleted from db in next delete-check time".format(t["title"]))
        else:
            torrent_full_name = dl_torrent.name
            logging.info("New get torrent: " + torrent_full_name)
            if dl_torrent.status == "seeding":  # 种子下载完成
                logging.info("This torrent is seeding now,Judge reseed or not.")
                autoseed.feed_torrent(dl_torrent)
            else:
                logging.warning("This torrent is still download.Wait until next check time.")


def main():
    logging.info("Autoseed start~,will check database record at the First time.")
    last_id_check = update_torrent_info_from_rpc_to_db(force_clean_check=True)
    i = 0
    while True:
        last_id_check = update_torrent_info_from_rpc_to_db(last_id_check=last_id_check)  # 更新表
        seed_judge()  # reseed判断主函数
        if i % setting.delete_check_round == 0:
            check_to_del_torrent_with_data_and_db()  # 清理种子

        if setting.web_show_status:  # 发种机运行状态展示
            co = ' AND '.join(tracker_condition(condition="!=-1"))
            decision = "WHERE {co} ORDER BY id DESC LIMIT {sum}".format(co=co, sum=setting.web_show_entries_number)
            data_list = db.get_table_seed_list(decision=decision)
            utils.generate_web_json(setting=setting, tr_client=tc, data_list=data_list)

        sleep_time = setting.sleep_free_time
        if setting.busy_start_hour <= int(time.strftime("%H", time.localtime())) < setting.busy_end_hour:
            sleep_time = setting.sleep_busy_time

        logging.debug("Check time {ti} OK, Reach check id {cid},"
                      " Will Sleep for {slt} seconds.".format(ti=i, cid=last_id_check, slt=sleep_time))
        i += 1
        time.sleep(sleep_time)


if __name__ == '__main__':
    main()
