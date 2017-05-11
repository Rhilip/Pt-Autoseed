# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time
import logging
from logging.handlers import RotatingFileHandler

import utils
import transmissionrpc
import extractors

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
# Transmission
tc = transmissionrpc.Client(address=setting.trans_address, port=setting.trans_port,
                            user=setting.trans_user, password=setting.trans_password)
# Database with its function
db = utils.Database(setting)

# Autoseed Stie
autoseed_list = []
reseed_tracker_host = []

# Byrbt
Byrbt_autoseed = extractors.Byrbt(setting=setting, tr_client=tc, db_client=db)
if Byrbt_autoseed.status:
    autoseed_list.append(Byrbt_autoseed)
    reseed_tracker_host.append(Byrbt_autoseed.db_column)

logging.info("Initialization settings Success~ The assign autoseed model:{lis}".format(lis=autoseed_list))


# -*- End of Loading Model -*-


def update_torrent_info_from_rpc_to_db(last_id_check=0, force_clean_check=False):
    """
    Sync torrent's id from transmission to database,
    List Start on last check id,and will return the max id as the last check id.
    """
    torrent_id_list = [t.id for t in tc.get_torrents() if t.id > last_id_check]
    if torrent_id_list:
        last_id_check = max(torrent_id_list)
        last_id_db = db.get_max_in_column(table="seed_list", column_list=["download_id"] + reseed_tracker_host)
        logging.debug("Now,Torrent id count: transmission: {tr},database: {db}".format(tr=last_id_check, db=last_id_db))
        if not force_clean_check:  # Normal Update
            logging.info("Some new torrents were add to transmission,Sync to db~")
            for i in torrent_id_list:
                t = tc.get_torrent(i)
                to_tracker_host = re.search(r"http[s]?://(.+?)/", t.trackers[0]["announce"]).group(1)
                if to_tracker_host not in reseed_tracker_host:  # TODO use UPsert instead
                    sql = "INSERT INTO seed_list (title,download_id) VALUES ('{}',{:d})".format(t.name, t.id)
                else:
                    sql = "UPDATE seed_list SET `{cow}` = {id:d} WHERE title='{name}'".format(cow=to_tracker_host,
                                                                                              name=t.name, id=t.id)
                db.commit_sql(sql)
        else:  # 第一次启动检查(force_clean_check)
            logging.error("It seems the torrent list didn't match with db-records,Clean the \"seed_list\" for safety.")
            db.commit_sql(sql="DELETE FROM seed_list")  # Delete all line from seed_list
            update_torrent_info_from_rpc_to_db()
    else:
        logging.debug("No new torrent(s),Return with nothing to do.")
    return last_id_check


def check_to_del_torrent_with_data_and_db():
    """Delete torrent(both download and reseed) with data from transmission and database"""
    logging.debug("Begin torrent's status check.If reach condition you set,You will get a warning.")
    for cow in db.get_table_seed_list():
        sid = cow.pop("id")
        s_title = cow.pop("title")
        err = 0
        reseed_list = []
        torrent_id_list = [tid for tracker, tid in cow.items() if tid > 0]
        for tid in torrent_id_list:
            try:  # Ensure torrent exist
                reseed_list.append(tc.get_torrent(torrent_id=tid))
            except KeyError:  # Mark err when the torrent is not exist.
                err += 1

        delete = False
        if err is 0:  # It means all torrents in this cow are exist,then check these torrent's status.
            reseed_stop_list = []
            for seed_torrent in reseed_list:
                seed_status = seed_torrent.status
                if seed_status == "stopped":  # Mark the stopped torrent
                    reseed_stop_list.append(seed_torrent)
                elif setting.pre_delete_judge(torrent=seed_torrent, time_now=time.time()):
                    tc.stop_torrent(seed_torrent.id)
                    logging.warning("Reach Target you set,Torrents({0}) now stop.".format(seed_torrent.name))
            if len(reseed_list) == len(reseed_stop_list):
                delete = True
                logging.info("All torrents reach target,Which name: \"{0}\" ,DELETE them with data.".format(s_title))
        else:
            delete = True
            logging.error("some Torrents (\"{name}\",{er} of {co}) may not found,"
                          "Delete all records from db".format(name=s_title, er=err, co=len(torrent_id_list)))

        if delete:  # Delete torrents with it's data and db-records
            for tid in torrent_id_list:
                tc.remove_torrent(tid, delete_data=True)
            db.commit_sql(sql="DELETE FROM seed_list WHERE id = {0}".format(sid))


def feed_torrent():
    """Judge to reseed depend on un-reseed torrent's status,With Database update after reseed."""
    result = db.get_table_seed_list_limit(tracker_list=reseed_tracker_host, operator="OR", condition="=0")
    for t in result:  # Traversal all unseed_list
        try:
            dl_torrent = tc.get_torrent(t["download_id"])  # 获取下载种子信息
        except KeyError:  # 种子不存在了
            logging.error("The pre-reseed Torrent (which name: \"{0}\") isn't found in result,"
                          "It will be deleted from db in next delete-check time".format(t["title"]))
        else:
            tname = dl_torrent.name

            reseed_judge = False
            if int(dl_torrent.progress) is 100:  # Get the download progress in percent.
                reseed_judge = True
                logging.info("New completed torrent: \"{name}\" ,Judge reseed or not.".format(name=tname))
            else:
                logging.warning("Torrent:\"{name}\" is still downloading,Wait until the next round.".format(name=tname))

            if reseed_judge:
                reseed_status = False
                for pat in utils.pattern_group:
                    search_group = re.search(pat, tname)
                    if search_group:
                        for autoseed in autoseed_list:  # Site feed
                            autoseed.feed(torrent=dl_torrent, torrent_info_search=search_group)
                        reseed_status = True
                        break
                if not reseed_status:  # 不符合，更新seed_id为-1
                    logging.warning("Mark Torrent \"{}\" As Un-reseed torrent,Stop watching.".format(tname))
                    for tr in reseed_tracker_host:
                        sql = "UPDATE seed_list SET `{}` = {:d} WHERE download_id = {:d}".format(tr, -1, dl_torrent.id)
                        db.commit_sql(sql)


def main():
    logging.info("Autoseed start~,will check database record at the First time.")
    last_id_check = update_torrent_info_from_rpc_to_db(force_clean_check=True)
    i = 0
    while True:
        last_id_check = update_torrent_info_from_rpc_to_db(last_id_check=last_id_check)  # 更新表
        feed_torrent()  # reseed判断主函数
        if i % setting.delete_check_round == 0:
            check_to_del_torrent_with_data_and_db()  # 清理种子

        if setting.web_show_status:  # 发种机运行状态展示
            data_list = db.get_table_seed_list_limit(tracker_list=reseed_tracker_host, operator="AND", condition="!=-1",
                                                     other_decision="ORDER BY id DESC LIMIT {sum}".format(
                                                         sum=setting.web_show_entries_number))
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
