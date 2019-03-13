# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import base64
import re

import requests

from extractors.base.nexusphp import NexusPHP
from utils.constants import ubb_clean, episode_eng2chs
from utils.load.handler import rootLogger as Logger


def string2base64(raw):
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


class NPUBits(NexusPHP):
    url_host = "https://npupt.com"
    db_column = "npupt.com"

    _pat_search_torrent_id = re.compile("torrent_download\((\d+)")

    @staticmethod
    def torrent_upload_err_message(post_text) -> str:
        """Use Internal hack for NBPub"""
        err_tag = re.search("<!-- __Error__\((?P<msg>.+)\) -->", post_text)
        err_message = err_tag.group("msg")
        return err_message

    def torrent_thank(self, tid):
        self.post_data(url=self.url_host + "/thanks.php", data={"id": str(tid), "value": 0})

    def page_search(self, key: str, bs=False):
        key = key.replace("&", " ")  # To Fix Multi Group Search Error
        return self.get_data(url=self.url_host + "/torrents.php", params={"search": key, "incldead": 1}, bs=bs)

    def torrent_clone(self, tid) -> dict:
        """
        Use Internal API: https://npupt.com/transfer.php?url={url} ,Request Method: GET
        The url use base64 encryption, and will response a json dict.
        """
        res_dic = {}
        transferred_url = string2base64("{host}/details.php?id={tid}&hit=1".format(host=self.url_host, tid=tid))
        try:
            res_dic = self.get_data(url=self.url_host + "/transfer.php", params={"url": transferred_url}, json=True)
        except ValueError:
            Logger.error("Error,this torrent may not exist or ConnectError")
        else:
            res_dic.update({"transferred_url": transferred_url, "clone_id": tid})
            res_dic["descr"] = ubb_clean(res_dic["descr"])

            Logger.info("Get clone torrent's info,id: {tid},title:\"{ti}\"".format(tid=tid, ti=res_dic["name"]))
        return res_dic

    def date_raw_update(self, torrent, torrent_name_search, raw_info: dict) -> dict:
        raw_info["descr"] = self.enhance_descr(torrent, raw_info["descr"], raw_info["clone_id"])
        if int(raw_info["category"]) == 402:  # Series
            raw_info["name"] = torrent_name_search.group("full_name")
            season_episode_info = episode_eng2chs(torrent_name_search.group("episode"))
            raw_info["small_descr"] = re.sub(r"第.+([集季])", season_episode_info, raw_info["small_descr"])
        elif int(raw_info["category"]) == 405:  # Anime
            episode = torrent_name_search.group("episode")
            group = torrent_name_search.group("group")
            # 替换集数信息
            raw_info["name"] = re.sub("^(.+?)\.\d{2,3}(?:\.5|[Vv]2)?\.(TV|BD|WEB|DVD)",
                                      "\g<1>.{ep}.\g<2>".format(ep=episode),
                                      raw_info["name"])
            # 替换制作组信息
            raw_info["name"] = re.sub("^(.+?(?:MP4|MKV|M2TS))\.(.+)$",
                                      "\g<1>.{group}".format(group=group),
                                      raw_info["name"])

        return raw_info

    def data_raw2tuple(self, raw_info):
        return (  # Submit form
            ("transferred_url", raw_info["transferred_url"]),
            ("type", raw_info["category"]),
            ("source_sel", raw_info["sub_category"]),
            ("name", string2base64(raw_info["name"])),
            ("small_descr", string2base64(raw_info["small_descr"])),
            ("descr", string2base64(raw_info["descr"])),
            ("nfo", ""),  # 实际上并不是这样的，但是nfo一般没有，故这么写
            ("uplver", self._UPLVER),
            ("transferred_torrent_file_base64", ""),
            ("transferred_torrent_file_name", ""),
        )
