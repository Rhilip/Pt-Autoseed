import logging
import re
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
    reseed_tracker_list = ["tracker.byr.cn"]

    def __init__(self, setting, tr_client, db_client):
        self.setting = setting
        self.tr = tr_client
        self.db = db_client

        self.Byrbt_autoseed = Byrbt(setting=setting, tr_client=self.tr, db_client=self.db)

    def feed_torrent(self, dl_torrent):
        torrent_full_name = dl_torrent.name
        to_type = search_group = None
        if re.search(search_series_pattern, torrent_full_name):
            to_type = "series"
            search_group = re.search(search_series_pattern, torrent_full_name)
        elif re.search(search_anime_pattern, torrent_full_name):
            to_type = "anime"
            search_group = re.search(search_anime_pattern, torrent_full_name)
        else:  # 不符合，更新seed_id为-1
            logging.warning("Mark Torrent \"{}\" As Un-reseed torrent,Stop watching it.".format(torrent_full_name))
            for tracker in self.reseed_tracker_list:
                sql = "UPDATE seed_list SET `{}` = {:d} WHERE download_id = {:d}".format(tracker, -1, dl_torrent.id)
                self.db.commit_sql(sql)

        # Site feed
        if to_type and search_group:
            self.Byrbt_autoseed.feed(torrent=dl_torrent, torrent_info_search=search_group, torrent_type=to_type)
