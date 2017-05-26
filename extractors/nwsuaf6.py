# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import re

from .default import NexusPHP


class MTPT(NexusPHP):
    url_host = "http://pt.nwsuaf6.edu.cn"
    db_column = "pt.nwsuaf6.edu.cn"

    def __init__(self, site_setting):
        super().__init__(site_setting=site_setting)

    def torrent_clone(self, tid) -> dict:
        """
        Use Internal API: http://pt.nwsuaf6.edu.cn/citetorrent.php?torrent_id={tid} ,Request Method: GET
        Will response a json dict.
        """
        try:
            res_dic = self.get_page(url="http://pt.nwsuaf6.edu.cn/citetorrent.php", params={"torrent_id": tid},
                                    json=True)
        except ValueError:
            logging.error("Error,this torrent may not exist or ConnectError")
            res_dic = {}
        else:
            res_dic.update({"cite_torrent": tid})

            # Remove code and quote.
            raw_descr = res_dic["descr"]
            raw_descr = re.sub(r"\[code\](.+)\[/code\]", "", raw_descr, flags=re.S)
            raw_descr = re.sub(r"\[quote\](.+)\[/quote\]", "", raw_descr, flags=re.S)
            raw_descr = re.sub(r"\u3000", " ", raw_descr)
            res_dic["descr"] = raw_descr

            logging.info("Get clone torrent's info,id: {tid},title:\"{ti}\"".format(tid=tid, ti=res_dic["name"]))
        return res_dic

    def data_raw2tuple(self, torrent, title_search_group, raw_info):
        torrent_file_name = re.search("torrents/(.+?\.torrent)", torrent.torrentFile).group(1)
        # Assign raw info
        name = str(raw_info["name"])

        # Change some info due to the torrent's info
        if raw_info["category"] == "402":  # Series
            name = title_search_group.group("full_name")
        elif raw_info["category"] == "405":  # Anime
            name = re.sub("\[(?P<episode>\d+)\]", "[{ep}]".format(ep=title_search_group.group("episode")), name)

        post_tuple = (  # Submit form
            ("cite_torrent", ('', str(raw_info["transferred_url"]))),
            ("file", (torrent_file_name, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
            ("type", ('', str(raw_info["category"]))),
            ("source_sel", ('', str(raw_info["sub_category"]))),
            ("name", ('', name)),
            ("small_descr", ('', raw_info["small_descr"])),
            ("imdburl", ('', raw_info["url"])),
            ("dburl", ('', raw_info["dburl"])),
            ("nfo", ('', '')),  # 实际上并不是这样的，但是nfo一般没有，故这么写
            ("color", ('', '0')),  # Tell me those three key's function~
            ("font", ('', '0')),
            ("size", ('', '0')),
            ("descr", ('', self.extend_descr(torrent=torrent, info_dict=raw_info))),
            ("uplver", ('', self.uplver)),
        )

        return post_tuple
