# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import importlib
import re
import time
from threading import Thread

from utils.constants import period_f, Support_Site
from utils.load.config import setting
from utils.load.handler import rootLogger as Logger
from utils.load.submodules import tc, db

TIME_TORRENT_KEEP_MIN = 86400 * 2  # The download torrent keep time even no reseed and in stopped status.(To avoid H&R.)


class Controller(Thread):
    downloading_torrent_id_queue = []
    active_obj_list = []
    last_id_check = 0

    def __init__(self):
        super().__init__()
        self._active()

    # Add Reseeder
    def _active(self):
        """
        Active the reseeder objects and append it to self.active_reseeder_list.
        Each object will follow those step(s):
            1. Check if config is exist in user setting
            2. Import the package and Instantiation The object if set status as `True` is site config
            3. If The reseeder active successfully (after session check), Append this reseeder to List

        :return: None
        """
        # 1. Active All used reseeder.
        Logger.info("Start to Active all the reseeder objects.")

        for config_name, package_name, class_name in Support_Site:
            if hasattr(setting, config_name):
                config = getattr(setting, config_name)
                if config.setdefault("status", False):
                    package = importlib.import_module(package_name)
                    autoseed_prototype = getattr(package, class_name)(**config)
                    if autoseed_prototype.status:
                        self.active_obj_list.append(autoseed_prototype)

        Logger.info("The assign reseeder objects: {lis}".format(lis=self.active_obj_list))

        # 2. Turn off those unactive reseeder, for database safety.
        unactive_tracker_list = [i for i in db.col_seed_list[3:]
                                 if i not in [i.db_column for i in self.active_obj_list]]

        def _shut_unreseeder_db():
            Logger.debug("Set un-reseeder's column into -1.")
            for tracker in unactive_tracker_list:  # Set un_reseed column into -1
                db.exec(sql="UPDATE `seed_list` SET `{cow}` = -1 WHERE `{cow}` = 0 ".format(cow=tracker))

        Thread(target=period_f, args=(_shut_unreseeder_db, 43200), daemon=True).start()
        Logger.info("Initialization settings Success~")

    # Internal cycle function
    def _online_check(self):
        Logger.debug("The reseeder online check now start.")
        for i in self.active_obj_list:
            i.online_check()

    def _del_torrent_with_db(self, rid=None):
        """Delete torrent(both download and reseed) with data from transmission and database"""
        Logger.debug("Begin torrent's status check. If reach condition you set, You will get a warning.")

        if rid:
            sql = "SELECT * FROM `seed_list` WHERE `id`={}".format(rid)
        else:
            sql = "SELECT * FROM `seed_list`"

        time_now = time.time()
        for cow in db.exec(sql=sql, r_dict=True, fetch_all=True):
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
            if rid:
                delete = True
                Logger.warning("Force Delete. Which name: {}, Affect torrents: {}".format(s_title, torrent_id_list))
            elif err is 0:  # It means all torrents in this cow are exist,then check these torrent's status.
                reseed_stop_list = []
                for t in reseed_list:
                    if int(time_now - t.addedDate) > TIME_TORRENT_KEEP_MIN:  # At least seed time
                        if t.status == "stopped":  # Mark the stopped torrent
                            reseed_stop_list.append(t)
                        elif setting.pre_delete_judge(torrent=t):
                            _tid, _tname, _tracker = self._get_torrent_info(t)
                            tc.stop_torrent(t.id)
                            Logger.warning(
                                "Reach Target you set, Torrent({tid}) \"{name}\" in Tracker \"{tracker}\" now stop, "
                                "With Uploaded {si:.2f} MiB, Ratio {ro:.2f} , Keep time {ho:.2f} h."
                                "".format(tid=_tid, name=_tname, tracker=_tracker, si=t.uploadedEver / 1024 / 1024,
                                          ro=t.uploadRatio, ho=(time.time() - t.startDate) / 60 / 60)
                            )
                if len(reseed_list) == len(reseed_stop_list):
                    delete = True
                    Logger.info("All torrents of \"{0}\" reach target, Will DELETE them soon.".format(s_title))
            else:
                delete = True
                Logger.error("Some Torrents (\"{name}\", {er} of {co}) may not found, "
                             "Delete all it's records from db".format(name=s_title, er=err, co=len(torrent_id_list)))

            if delete:  # Delete torrents with it's data and db-records
                for tid in torrent_id_list:
                    tc.remove_torrent(tid, delete_data=True)
                db.exec(sql="DELETE FROM `seed_list` WHERE `id` = {0}".format(sid))

    @staticmethod
    def _get_torrent_info(t) -> tuple:
        """
        Get torrent's information about tid, name and it's main tracker host.
        For main tracker host,if it is not in whole_tracker_list,will be rewrite to "download_id"

        :param t: int or class 'transmissionrpc.torrent.Torrent'
        :return: (tid, name, tracker)
        """
        if isinstance(t, int):
            t = tc.get_torrent(t)  # Return class 'transmissionrpc.torrent.Torrent'

        try:
            tracker = re.search(r"p[s]?://(?P<host>.+?)/", t.trackers[0]["announce"]).group("host")
            if tracker not in db.col_seed_list:
                raise AttributeError("Not reseed tracker.")
        except AttributeError:
            tracker = "download_id"  # Rewrite tracker
        return t.id, t.name, tracker

    def run(self):
        # Sync status between transmission, database, controller and reseeder modules
        self.update_torrent_info_from_rpc_to_db(force_clean_check=True)
        self.reseeders_update()

        # Start background thread
        thread_args = [
            (self._online_check, setting.CYCLE_CHECK_RESEEDER_ONLINE),
            (self._del_torrent_with_db, setting.CYCLE_DEL_TORRENT_CHECK)
        ]
        for args in thread_args:
            Thread(target=period_f, args=args, daemon=True).start()

        Logger.info("Check period Starting~")
        while True:
            self.update_torrent_info_from_rpc_to_db()  # Read the new torrent's info and sync it to database
            self.reseeders_update()  # Feed those new and not reseed torrent to active reseeder
            time.sleep(setting.SLEEP_TIME)

    def get_online_reseeders(self):
        return [s for s in self.active_obj_list if s.suspended == 0]  # Get active and online reseeder

    def update_torrent_info_from_rpc_to_db(self, last_id_db=None, force_clean_check=False):
        """
        Sync torrent's id from transmission to database,
        List Start on last check id,and will return the max id as the last check id.
        """
        torrent_list = tc.get_torrents()  # Cache the torrent list
        new_torrent_list = [t for t in torrent_list if t.id > self.last_id_check]
        if new_torrent_list:
            last_id_now = max([t.id for t in new_torrent_list])
            if last_id_db is None:
                last_id_db = db.get_max_in_seed_list(column_list=db.col_seed_list[2:])
            Logger.debug("Max tid, transmission: {tr}, database: {db}".format(tr=last_id_now, db=last_id_db))

            if not force_clean_check:  # Normal Update
                Logger.info("Some new torrents were add to transmission, Sync to db~")
                for i in new_torrent_list:  # Upsert the new torrent
                    db.upsert_seed_list(self._get_torrent_info(i))
                self.last_id_check = last_id_now

            elif last_id_now != last_id_db:  # Check the torrent 's record between tr and db
                total_num_in_tr = len(set([t.name for t in torrent_list]))
                total_num_in_db = db.exec(sql="SELECT COUNT(*) FROM `seed_list`")[0]
                if int(total_num_in_tr) >= int(total_num_in_db):
                    db.cache_torrent_list()
                    Logger.info("Upsert the whole torrent id to database.")
                    for t in torrent_list:  # Upsert the whole torrent
                        db.upsert_seed_list(self._get_torrent_info(t))
                else:
                    Logger.error(
                        "The torrent list didn't match with db-records, Clean the whole \"seed_list\" for safety.")
                    db.exec(sql="DELETE FROM `seed_list` WHERE 1")  # Delete all line from seed_list
                    self.update_torrent_info_from_rpc_to_db(last_id_db=0)
        else:
            Logger.debug("No new torrent(s), Return with nothing to do.")
        return self.last_id_check

    def reseeders_update(self):
        """
        Get the pre-reseed list from database.
        And sent those un-reseed torrents to each reseeder depend on it's download status.
        """
        pre_reseeder_list = self.get_online_reseeders()
        pre_cond = " OR ".join(["`{}`=0".format(i.db_column) for i in pre_reseeder_list])
        result = db.exec("SELECT * FROM `seed_list` WHERE `download_id` != 0 AND ({})".format(pre_cond),
                         r_dict=True, fetch_all=True)
        for t in result:  # Traversal all un-reseed list
            try:
                dl_torrent = tc.get_torrent(t["download_id"])
            except KeyError:  # Un-exist pre-reseed torrent
                Logger.error("The pre-reseed Torrent: \"{0}\" isn't found in result, "
                             "It's db-record will be deleted soon.".format(t["title"]))
                self._del_torrent_with_db(rid=t["id"])
                if t["id"] in self.downloading_torrent_id_queue:
                    self.downloading_torrent_id_queue.remove(t["id"])
            else:
                tname = dl_torrent.name
                if int(dl_torrent.progress) is 100:  # Get the download progress in percent.
                    Logger.info("New completed torrent: \"{name}\" , Judge reseed or not.".format(name=tname))
                    for reseeder in pre_reseeder_list:
                        Thread(target=reseeder.torrent_feed, args=(dl_torrent,),
                               name="Thread-{}".format(reseeder.model_name()), daemon=True).start()
                        # reseeder.torrent_feed(torrent=dl_torrent)
                    if dl_torrent.id in self.downloading_torrent_id_queue:
                        self.downloading_torrent_id_queue.remove(dl_torrent.id)
                elif dl_torrent.id in self.downloading_torrent_id_queue:
                    pass  # Wait until this torrent download completely.
                else:
                    Logger.warning("Torrent:\"{name}\" is still downloading, Wait......".format(name=tname))
                    self.downloading_torrent_id_queue.append(dl_torrent.id)
