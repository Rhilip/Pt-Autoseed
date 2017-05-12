import re
import logging

from utils.pattern import pattern_group

from .byrbt import Byrbt
from .npubits import NPUBits


class Autoseed(object):
    autoseed_list = []
    tracker_list = []

    def __init__(self, setting, tr_client, db_client):
        self.setting = setting
        self.tr_client = tr_client
        self.db_client = db_client

        self.load_autoseed()

    def load_autoseed(self):
        # Byrbt
        autoseed_byrbt = Byrbt(setting=self.setting, tr_client=self.tr_client, db_client=self.db_client)
        if autoseed_byrbt.status:
            self.autoseed_list.append(autoseed_byrbt)

        # NPUBits
        autoseed_npubits = NPUBits(setting=self.setting, tr_client=self.tr_client, db_client=self.db_client)
        if autoseed_byrbt.status:
            self.autoseed_list.append(autoseed_npubits)

        for site in self.autoseed_list:
            self.tracker_list.append(site.db_column)

        logging.info("The assign autoseed model:{lis}".format(lis=self.autoseed_list))

    def feed(self, dl_torrent):
        tname = dl_torrent.name
        reseed_judge = False
        if int(dl_torrent.progress) is 100:  # Get the download progress in percent.
            reseed_judge = True
            logging.info("New completed torrent: \"{name}\" ,Judge reseed or not.".format(name=tname))
        else:
            logging.warning("Torrent:\"{name}\" is still downloading,Wait until the next round.".format(name=tname))

        if reseed_judge:
            reseed_status = False
            for pat in pattern_group:
                search_group = re.search(pat, tname)
                if search_group:
                    for site in self.autoseed_list:  # Site feed
                        site.feed(torrent=dl_torrent, torrent_info_search=search_group)
                    reseed_status = True
                    break
            if not reseed_status:  # 不符合，更新seed_id为-1
                logging.warning("Mark Torrent \"{}\" As Un-reseed torrent,Stop watching.".format(tname))
                for tracker in self.tracker_list:
                    sql = "UPDATE seed_list SET `{}` = {:d} WHERE download_id = {:d}".format(tracker, -1, dl_torrent.id)
                    self.db_client.commit_sql(sql)

    def update(self):
        """Judge to reseed depend on un-reseed torrent's status,With Database update after reseed."""
        result = self.db_client.get_table_seed_list_limit(tracker_list=self.tracker_list, operator="OR", condition="=0")
        for t in result:  # Traversal all unseed_list
            try:
                self.feed(dl_torrent=self.tr_client.get_torrent(t["download_id"]))
            except KeyError:  # 种子不存在了
                logging.error("The pre-reseed Torrent (which name: \"{0}\") isn't found in result,"
                              "It will be deleted from db in next delete-check time".format(t["title"]))
