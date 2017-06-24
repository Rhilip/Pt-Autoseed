import json
import logging
import re
import time

from utils.loadsetting import tc, db, setting

MIN_KEEP_TIME = 86400  # The download torrent keep time even no reseed and stopped status.


class Connect(object):
    db_column = [fi["Field"] for fi in db.get_sql("SHOW COLUMNS FROM `seed_list`", r_dict=True)]
    tracker_list = db_column[3:]  # ['id','title','download_id',...]

    def __init__(self, seed_list):
        self.reseed_tracker_list = [seed.db_column for seed in seed_list]
        self.un_reseed_tracker_list = [item for item in self.tracker_list if item not in self.reseed_tracker_list]

    def update_torrent_info_from_rpc_to_db(self, last_id_check=0, last_id_db=None, force_clean_check=False):
        """
        Sync torrent's id from transmission to database,
        List Start on last check id,and will return the max id as the last check id.
        """
        torrent_id_list = [t.id for t in tc.get_torrents() if t.id > last_id_check]
        if torrent_id_list:
            last_id_check = max(torrent_id_list)
            if last_id_db is None:
                last_id_db = db.get_max_in_columns(table="seed_list", column_list=self.db_column[2:])
            logging.debug("Max tid, transmission: {tr},database: {db}".format(tr=last_id_check, db=last_id_db))
            if not force_clean_check:  # Normal Update
                logging.info("Some new torrents were add to transmission,Sync to db~")
                for i in torrent_id_list:
                    t = tc.get_torrent(i)
                    try:
                        to_tracker_host = re.search(r"p[s]?://(?P<host>.+?)/", t.trackers[0]["announce"]).group("host")
                    except AttributeError:
                        to_tracker_host = "download_id"

                    if to_tracker_host in self.tracker_list:
                        sql = "UPDATE seed_list SET `{cow}` = {id:d} " \
                              "WHERE title='{name}'".format(cow=to_tracker_host, name=t.name, id=t.id)
                    else:
                        sql = "INSERT INTO seed_list (title,download_id) VALUES ('{}',{:d})".format(t.name, t.id)
                    db.commit_sql(sql)

                # Set un_reseed column into -1
                for tracker in self.un_reseed_tracker_list:
                    db.commit_sql(sql="UPDATE seed_list SET `{cow}` = -1 WHERE `{cow}` = 0 ".format(cow=tracker))
            elif last_id_check != last_id_db:  # 第一次启动检查(force_clean_check)
                logging.error(
                    "It seems the torrent list didn't match with db-records,Clean the \"seed_list\" for safety.")
                db.commit_sql(sql="DELETE FROM seed_list")  # Delete all line from seed_list
                self.update_torrent_info_from_rpc_to_db(last_id_db=0)
        else:
            logging.debug("No new torrent(s),Return with nothing to do.")
        return last_id_check

    @staticmethod
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
                        if int(time.time() - seed_torrent.addedDate) > MIN_KEEP_TIME:  # At least seed time
                            reseed_stop_list.append(seed_torrent)
                    elif setting.pre_delete_judge(torrent=seed_torrent):
                        tc.stop_torrent(seed_torrent.id)
                        logging.warning("Reach Target you set,Torrents({0}) now stop.".format(seed_torrent.name))
                if len(reseed_list) == len(reseed_stop_list):
                    delete = True
                    logging.info(
                        "All torrents reach target,Which name: \"{0}\" ,DELETE them with data.".format(s_title))
            else:
                delete = True
                logging.error("some Torrents (\"{name}\",{er} of {co}) may not found,"
                              "Delete all records from db".format(name=s_title, er=err, co=len(torrent_id_list)))

            if delete:  # Delete torrents with it's data and db-records
                for tid in torrent_id_list:
                    tc.remove_torrent(tid, delete_data=True)
                db.commit_sql(sql="DELETE FROM seed_list WHERE id = {0}".format(sid))

    def generate_web_json(self):
        data = []
        other_decision = "ORDER BY id DESC LIMIT {sum}".format(sum=setting.web_show_entries_number)
        data_list = db.get_table_seed_list_limit(tracker_list=self.reseed_tracker_list, operator="AND",
                                                 condition="!=-1", other_decision=other_decision)
        for cow in data_list:
            sid = cow.pop("id")
            s_title = cow.pop("title")
            try:
                download_torrent_id = cow.pop("download_id")
                download_torrent = tc.get_torrent(download_torrent_id)
                reseed_info_list = []
                for tracker, tid in cow.items():
                    if int(tid) == 0:
                        reseed_status = "Not found."
                        reseed_ratio = 0
                    else:
                        reseed_torrent = tc.get_torrent(tid)
                        reseed_status = reseed_torrent.status
                        reseed_ratio = reseed_torrent.uploadRatio
                    reseed_info_list.append((tracker, reseed_status, reseed_ratio))
            except KeyError:
                logging.error("One of torrents (Which name: \"{0}\") may delete from transmission.".format(s_title))
            else:
                start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(download_torrent.addedDate))
                torrent_reseed_list = []
                for tracker, reseed_status, reseed_ratio in reseed_info_list:
                    torrent_dict = {
                        "reseed_tracker": tracker,
                        "reseed_status": reseed_status,
                        "reseed_ratio": "{:.2f}".format(reseed_ratio)
                    }
                    torrent_reseed_list.append(torrent_dict)
                info_dict = {
                    "tid": sid,
                    "title": s_title,
                    "size": "{:.2f} MiB".format(download_torrent.totalSize / (1024 * 1024)),
                    "download_start_time": start_time,
                    "download_status": download_torrent.status,
                    "download_upload_ratio": "{:.2f}".format(download_torrent.uploadRatio),
                    "reseed_info": torrent_reseed_list
                }
                data.append(info_dict)
        out_list = {
            "last_update_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "data": data
        }

        with open(setting.web_loc + "/tostatus.json", "wt") as f:
            json.dump(out_list, f)

        logging.debug("Generate Autoseed's status OK.")
