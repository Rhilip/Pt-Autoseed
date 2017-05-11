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
    url_torrent_download = "https://npupt.com/download.php?id={tid}&passkey={pk}"
    url_torrent_upload = "https://npupt.com/takeupload.php"
    url_torrent_detail = "https://npupt.com/details.php?id={tid}&hit=1"
    url_torrent_file = "https://npupt.com/torrent_info.php?id={tid}"
    url_thank = "https://npupt.com/thanks.php"
    url_search = "https://npupt.com/torrents.php?search={k}&incldead=1&nodupe=1"  # TODO NPU use incldead,nodupe instead
    url_torrent_list = "https://npupt.com/torrents.php"

    db_column = "npupt.com"

    def __init__(self, setting, tr_client, db_client):
        _site_setting = setting.site_npubits
        super().__init__(setting=setting, site_setting=_site_setting, tr_client=tr_client, db_client=db_client)

    def torrent_thank(self, tid):
        requests.post(url=self.url_thank, cookies=self.cookies, data={"id": str(tid), "value": 0})  # 自动感谢

    def torrent_clone(self, tid) -> dict:
        """
        Use Internal API: https://npupt.com/transfer.php?url={url} ,Request Method:GET
        The url use base64 encryption, and will response a json dict.
        """
        transferred_url = string2base64(self.url_torrent_detail.format(tid=tid))
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

    def data_raw2tuple(self, torrent, title_search_group, raw_info):
        torrent_file_name = re.search("torrents/(.+?\.torrent)", torrent.torrentFile).group(1)
        return (  # Submit form
            ("transferred_url", ('', str(raw_info["transferred_url"]))),
            ("type", ('', str(raw_info["category"]))),
            ("source_sel", ('', str(raw_info["sub_category"]))),
            ("file", (torrent_file_name, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
            ("name", ('', string2base64(str(raw_info["name"])))),
            ("small_descr", ('', string2base64(raw_info["small_descr"]))),
            ("color", ('', 0)),  # Tell me those three key's function~
            ("font", ('', 0)),
            ("size", ('', 0)),
            ("descr", ('', string2base64(self.extend_descr(torrent=torrent, info_dict=raw_info, encode="bbcode")))),
            ("nfo", ('', '')),  # 实际上并不是这样的，但是nfo一般没有，故这么写
            ("uplver", ('', self.uplver)),
            ("transferred_torrent_file_base64", ('', '')),
            ("transferred_torrent_file_name", ('', '')),
        )
