import logging
import re
from utils.serverchan import ServerChan
from .byrbt import Byrbt

# Search_pattern
search_series_pattern = re.compile(
    u"(?:^[\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff:：]+[. ]?|^)"  # 移除平假名、片假名、中文
    "(?P<full_name>(?P<search_name>[\w\-. ]+?)[. ]"
    "(?P<tv_season>(?:(?:[Ss]\d+)?[Ee][Pp]?\d+(?:-[Ee]?[Pp]?\d+)?)|(?:[Ss]\d+)).+?(?:-(?P<group>.+?))?)"
    "(?:\.(?P<tv_filetype>\w+)$|$)"
)
search_anime_pattern = re.compile(
    "(?P<full_name>\[(?P<group>.+?)\]\[?(?P<search_name>.+?)\]?\[(?P<anime_episode>\d+)\].+)"
    "(?:\.(mp4|mkv))?"
)


class Autoseed(object):
    def __init__(self, setting, tr_client, db_client):
        self.setting = setting
        self.tr = tr_client
        self.db = db_client

        self.Byrbt_autoseed = Byrbt(setting=setting)

        self.server_chan = ServerChan(setting)

    def new_torrent_receive(self, dl_torrent):
        torrent_full_name = dl_torrent.name
        flag = -1
        if re.search(search_series_pattern, torrent_full_name):
            series_search_group = re.search(search_series_pattern, torrent_full_name)
            flag = self.Byrbt_autoseed.shunt_reseed(tr_client=self.tr, db_client=self.db, torrent=dl_torrent,
                                                    torrent_info_search=series_search_group, torrent_type="series")
        elif re.search(search_anime_pattern, torrent_full_name):
            anime_search_group = re.search(search_anime_pattern, torrent_full_name)
            flag = self.Byrbt_autoseed.shunt_reseed(tr_client=self.tr, db_client=self.db, torrent=dl_torrent,
                                                    torrent_info_search=anime_search_group, torrent_type="anime")
        else:  # 不符合，更新seed_id为-1
            logging.warning("Mark Torrent \"{}\" As Un-reseed torrent,Stop watching it.".format(torrent_full_name))
        return flag
