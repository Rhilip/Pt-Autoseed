import json
import logging
import re
import time

from utils.loadsetting import tc, db, setting
from utils.pattern import pattern_group

TIME_RESEEDER_ONLINE_CHECK = 3600
TIME_TORRENT_KEEP_MIN = 86400  # The download torrent keep time even no reseed and stopped status.


class Connect(object):
    # List of Reseeder Object
    active_reseeder_list = []
    active_online_reseeder_list = []

    # List of Tracker String
    db_column = [fi["Field"] for fi in db.get_sql("SHOW COLUMNS FROM `seed_list`", r_dict=True)]
    whole_tracker_list = db_column[3:]  # ['id','title','download_id',...]
    reseed_tracker_list = []
    reseed_online_tracker_list = []
    un_reseed_tracker_list = []

    last_online_check_timestamp = 0
    downloading_torrent_id_queue = []

    def __init__(self):
        # Active the reseeder Object
        self.reseeders_active()

    def reseeders_active(self):
        """Active the reseeder objects and append it to self.active_reseeder_list."""
        # Byrbt
        if setting.site_byrbt["status"]:
            from extractors.byrbt import Byrbt
            autoseed_byrbt = Byrbt(site_setting=setting.site_byrbt)
            if autoseed_byrbt.status:
                self.active_reseeder_list.append(autoseed_byrbt)

        # NPUBits
        if setting.site_npubits["status"]:
            from extractors.npubits import NPUBits
            autoseed_npubits = NPUBits(site_setting=setting.site_npubits)
            if autoseed_npubits.status:
                self.active_reseeder_list.append(autoseed_npubits)

        # nwsuaf6
        if setting.site_nwsuaf6["status"]:
            from extractors.nwsuaf6 import MTPT
            autoseed_nwsuaf6 = MTPT(site_setting=setting.site_nwsuaf6)
            if autoseed_nwsuaf6.status:
                self.active_reseeder_list.append(autoseed_nwsuaf6)

        # TJUPT
        if setting.site_tjupt["status"]:
            from extractors.tjupt import TJUPT
            autoseed_tjupt = TJUPT(site_setting=setting.site_tjupt)
            if autoseed_tjupt.status:
                self.active_reseeder_list.append(autoseed_tjupt)

        # Update the Related list
        self.reseed_tracker_list = [seed.db_column for seed in self.active_reseeder_list]
        self.un_reseed_tracker_list = [item for item in self.whole_tracker_list if item not in self.reseed_tracker_list]

        logging.info("The assign reseeder objects:{lis}".format(lis=self.active_reseeder_list))

    def reseeders_online_check(self):
        self.active_online_reseeder_list = [site for site in self.active_reseeder_list if
                                            site.online_check() and site.status]
        self.reseed_online_tracker_list = [site.db_column for site in self.active_online_reseeder_list]

    def reseeders_feed(self, dl_torrent, cow):
        reseed_status = False

        tname = dl_torrent.name
        for pat in pattern_group:
            search = re.search(pat, tname)
            if search:
                logging.debug("The search group: {gr}".format(gr=search.groups()))
                key_raw = re.sub(r"[_\-.']", " ", search.group("search_name"))
                clone_dict = db.get_data_clone_id(key=key_raw)
                for site in self.active_online_reseeder_list:  # Site feed
                    if int(cow[site.db_column]) is 0:
                        tag = site.torrent_feed(torrent=dl_torrent, name_pattern=search, clone_db_dict=clone_dict)
                        db.reseed_update(did=dl_torrent.id, rid=tag, site=site.db_column)
                reseed_status = True
                break

        if not reseed_status:  # Update seed_id == -1 if no matched pattern
            logging.warning("No match pattern,Mark \"{}\" As Un-reseed torrent,Stop watching.".format(tname))
            for tracker in self.active_online_reseeder_list:
                db.reseed_update(did=dl_torrent.id, rid=-1, site=tracker.db_column)

    def reseeders_update(self):
        """Get the pre-reseed list from database."""
        if time.time() - self.last_online_check_timestamp > TIME_RESEEDER_ONLINE_CHECK:
            self.reseeders_online_check()
            self.last_online_check_timestamp = time.time()

        result = db.get_table_seed_list_limit(tracker_list=self.reseed_online_tracker_list, operator="OR",
                                              condition="=0")
        for t in result:  # Traversal all un-reseed list
            try:
                dl_torrent = tc.get_torrent(t["download_id"])
            except KeyError:  # Un-exist pre-reseed torrent
                logging.error("The pre-reseed Torrent (which name: \"{0}\") isn't found in result,"
                              "It will be deleted from db in next delete-check time".format(t["title"]))
            else:
                tname = dl_torrent.name
                if int(dl_torrent.progress) is 100:  # Get the download progress in percent.
                    logging.info("New completed torrent: \"{name}\" ,Judge reseed or not.".format(name=tname))
                    self.reseeders_feed(dl_torrent=dl_torrent, cow=t)
                    if dl_torrent.id in self.downloading_torrent_id_queue:
                        self.downloading_torrent_id_queue.remove(dl_torrent.id)
                elif dl_torrent.id in self.downloading_torrent_id_queue:
                    pass  # Wait until this torrent download completely.
                else:
                    logging.warning("Torrent:\"{name}\" is still downloading,Wait......".format(name=tname))
                    self.downloading_torrent_id_queue.append(dl_torrent.id)

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

                    name = t.name.replace("'", r"\'")
                    if to_tracker_host in self.whole_tracker_list:
                        sql = "UPDATE seed_list SET `{cow}` = {id:d} " \
                              "WHERE title='{name}'".format(cow=to_tracker_host, name=name, id=t.id)
                    else:
                        sql = "INSERT INTO seed_list (title,download_id) VALUES ('{}',{:d})".format(name, t.id)
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
        time_now = time.time()
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
                        if int(time_now - seed_torrent.addedDate) > TIME_TORRENT_KEEP_MIN:  # At least seed time
                            reseed_stop_list.append(seed_torrent)
                    elif setting.pre_delete_judge(torrent=seed_torrent):
                        tc.stop_torrent(seed_torrent.id)
                        logging.warning("Reach Target you set,Torrent \"{0}\" now stop.".format(seed_torrent.name))
                if len(reseed_list) == len(reseed_stop_list):
                    delete = True
                    logging.info("All torrents of \"{0}\" reach target,Will DELETE them soon.".format(s_title))
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
