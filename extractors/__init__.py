import re
import logging

from utils.pattern import pattern_group
from utils.loadsetting import tc, db, setting


class Autoseed(object):
    active_seed = []
    active_tracker = []

    def __init__(self):
        self.load_autoseed()

    def load_autoseed(self):
        # Byrbt
        if setting.site_byrbt["status"]:
            from .byrbt import Byrbt
            autoseed_byrbt = Byrbt(site_setting=setting.site_byrbt)
            if autoseed_byrbt.status:
                self.active_seed.append(autoseed_byrbt)

        # NPUBits
        if setting.site_npubits["status"]:
            from .npubits import NPUBits
            autoseed_npubits = NPUBits(site_setting=setting.site_npubits)
            if autoseed_npubits.status:
                self.active_seed.append(autoseed_npubits)

        for site in self.active_seed:
            self.active_tracker.append(site.db_column)
        logging.info("The assign autoseed module:{lis}".format(lis=self.active_seed))

    def feed(self, dl_torrent, cow):
        tname = dl_torrent.name
        if int(dl_torrent.progress) is 100:  # Get the download progress in percent.
            logging.info("New completed torrent: \"{name}\" ,Judge reseed or not.".format(name=tname))
            reseed_status = False
            for pat in pattern_group:
                search = re.search(pat, tname)
                if search:
                    key_raw = re.sub(r"[_\-.]", " ", search.group("search_name"))
                    clone_dict = db.get_data_clone_id(key=key_raw)
                    for site in self.active_seed:  # Site feed
                        if cow[site.db_column] is 0:
                            tag = site.torrent_feed(torrent=dl_torrent, name_pattern=search, clone_db_dict=clone_dict)
                            db.reseed_update(did=dl_torrent.id, rid=tag, site=site.db_column)
                    reseed_status = True
                    break
            if not reseed_status:  # 不符合，更新seed_id为-1
                logging.warning("Mark Torrent \"{}\" As Un-reseed torrent,Stop watching.".format(tname))
                for tracker in self.active_tracker:
                    sql = "UPDATE seed_list SET `{}` = {:d} WHERE download_id = {:d}".format(tracker, -1, dl_torrent.id)
                    db.commit_sql(sql)
        else:
            logging.warning("Torrent:\"{name}\" is still downloading,Wait until the next round.".format(name=tname))

    def update(self):
        """Get the pre-reseed list from database."""
        result = db.get_table_seed_list_limit(tracker_list=self.active_tracker, operator="OR", condition="=0")
        for t in result:  # Traversal all un-reseed list
            try:
                dl_torrent = tc.get_torrent(t["download_id"])
            except KeyError:  # Un-exist pre-reseed torrent
                logging.error("The pre-reseed Torrent (which name: \"{0}\") isn't found in result,"
                              "It will be deleted from db in next delete-check time".format(t["title"]))
            else:
                self.feed(dl_torrent=dl_torrent, cow=t)
