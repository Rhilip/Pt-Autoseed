# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import base64
import logging
import re

from .default import NexusPHP


def string2base64(raw):
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


class NPUBits(NexusPHP):
    url_host = "https://npupt.com"
    db_column = "npupt.com"

    def __init__(self, site_setting):
        super().__init__(site_setting=site_setting)

    @staticmethod
    def torrent_upload_err_message(post_text) -> str:
        """Use Internal hack for NBPub"""
        err_tag = re.search("<!-- __Error__\((?P<msg>.+)\) -->", post_text)
        err_message = err_tag.group("msg")
        return err_message

    def torrent_thank(self, tid):
        self.post_data(url="{host}/thanks.php".format(host=self.url_host), data={"id": str(tid), "value": 0})

    def torrent_clone(self, tid) -> dict:
        """
        Use Internal API: https://npupt.com/transfer.php?url={url} ,Request Method: GET
        The url use base64 encryption, and will response a json dict.
        """
        transferred_url = string2base64("{host}/details.php?id={tid}&hit=1".format(host=self.url_host, tid=tid))
        try:
            res_dic = self.get_page(url="https://npupt.com/transfer.php", params={"url": transferred_url}, json=True)
        except ValueError:
            logging.error("Error,this torrent may not exist or ConnectError")
            res_dic = {}
        else:
            res_dic.update({"transferred_url": transferred_url, "clone_id": tid})

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
            name = re.sub("\.(?P<episode>\d+)\.", ".{ep}.".format(ep=title_search_group.group("episode")), name)

        post_tuple = (  # Submit form
            ("transferred_url", ('', str(raw_info["transferred_url"]))),
            ("type", ('', str(raw_info["category"]))),
            ("source_sel", ('', str(raw_info["sub_category"]))),
            ("file", (torrent_file_name, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
            ("name", ('', string2base64(name))),
            ("small_descr", ('', string2base64(raw_info["small_descr"]))),
            ("color", ('', '0')),  # Tell me those three key's function~
            ("font", ('', '0')),
            ("size", ('', '0')),
            ("descr", ('', string2base64(self.extend_descr(torrent=torrent, info_dict=raw_info)))),
            ("nfo", ('', '')),  # 实际上并不是这样的，但是nfo一般没有，故这么写
            ("uplver", ('', self.uplver)),
            ("transferred_torrent_file_base64", ('', '')),
            ("transferred_torrent_file_name", ('', '')),
        )

        return post_tuple
