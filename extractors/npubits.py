# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import base64
import requests
import logging

from .default import NexusPHP

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)


def string2base64(raw):
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


class NPUBits(NexusPHP):
    url_host = "https://npupt.com"

    db_column = "npupt.com"

    def __init__(self, setting, tr_client, db_client):
        _site_setting = setting.site_npubits
        super().__init__(setting=setting, site_setting=_site_setting, tr_client=tr_client, db_client=db_client)

    def torrent_thank(self, tid):
        url_thank = "{host}/thanks.php".format(host=self.url_host)
        requests.post(url=url_thank, cookies=self.cookies, data={"id": str(tid), "value": 0})

    def torrent_clone(self, tid) -> dict:
        """
        Use Internal API: https://npupt.com/transfer.php?url={url} ,Request Method:GET
        The url use base64 encryption, and will response a json dict.
        """
        transferred_url = string2base64("{host}/details.php?id={tid}&hit=1".format(host=self.url_host, tid=tid))
        res = requests.get(url="https://npupt.com/transfer.php?url={url}".format(url=transferred_url),
                           cookies=self.cookies)
        res_dic = res.json()
        res_dic.update({"transferred_url": transferred_url})

        # Remove code and quote.
        raw_descr = res_dic["descr"]
        raw_descr = re.sub(r"\[code\](.+)\[/code\]", "", raw_descr, flags=re.S)
        raw_descr = re.sub(r"\[quote\](.+)\[/quote\]", "", raw_descr, flags=re.S)
        raw_descr = re.sub(r"\u3000", " ", raw_descr)
        res_dic["descr"] = raw_descr

        return res_dic

    def get_last_torrent_id(self, key, mode: int = 0, tid=0) -> int:
        url_search = "{host}/torrents.php?search={k}&incldead=1&nodupe=1".format(host=self.url_host, k=key)  # TODO NPUBits Use incldead and nodupe instead
        bs = self.get_page(url=url_search, bs=True)
        first_torrent_tag = bs.find("a", href=re.compile("torrent_download"))
        if first_torrent_tag:  # If exist
            href = first_torrent_tag["href"]
            tid = re.search("torrent_download\((\d+)", href).group(1)  # 找出种子id
        return tid

    def data_raw2tuple(self, torrent, title_search_group, raw_info):
        torrent_file_name = re.search("torrents/(.+?\.torrent)", torrent.torrentFile).group(1)
        # Assign raw info
        name = str(raw_info["name"])

        # Change some info due to the torrent's info
        if raw_info["category"] is 402:  # Series
            name = title_search_group.group("full_name")
        elif raw_info["category"] is 405:  # Anime
            name = re.sub("\.(?P<episode>\d+)\.", ".{ep}.".format(ep=title_search_group.group("episode")), name)

        post_tuple = (  # Submit form
            ("transferred_url", ('', str(raw_info["transferred_url"]))),
            ("type", ('', str(raw_info["category"]))),
            ("source_sel", ('', str(raw_info["sub_category"]))),
            ("file", (torrent_file_name, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
            ("name", ('', string2base64(name))),
            ("small_descr", ('', string2base64(raw_info["small_descr"]))),
            ("color", ('', 0)),  # Tell me those three key's function~
            ("font", ('', 0)),
            ("size", ('', 0)),
            ("descr", ('', string2base64(self.extend_descr(torrent=torrent, info_dict=raw_info)))),
            ("nfo", ('', '')),  # 实际上并不是这样的，但是nfo一般没有，故这么写
            ("uplver", ('', self.uplver)),
            ("transferred_torrent_file_base64", ('', '')),
            ("transferred_torrent_file_name", ('', '')),
        )

        return post_tuple
