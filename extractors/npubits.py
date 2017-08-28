# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import base64
import logging
import re

from extractors.nexusphp import NexusPHP


def string2base64(raw):
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


class NPUBits(NexusPHP):
    url_host = "https://npupt.com"
    db_column = "npupt.com"

    @staticmethod
    def torrent_upload_err_message(post_text) -> str:
        """Use Internal hack for NBPub"""
        err_tag = re.search("<!-- __Error__\((?P<msg>.+)\) -->", post_text)
        err_message = err_tag.group("msg")
        return err_message

    def torrent_thank(self, tid):
        self.post_data(url=self.url_host + "/thanks.php", data={"id": str(tid), "value": 0})

    def search_list(self, key):
        bs = self.page_search(payload={"search": key}, bs=True)
        download_tag = bs.find_all("a", href=re.compile("torrent_download"))
        tid_list = [re.search("torrent_download\((\d+)", tag["href"]).group(1) for tag in download_tag]
        logging.debug("USE key: {key} to search,and the Return tid-list: {list}".format(key=key, list=tid_list))
        return tid_list

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
            logging.error("Error,this torrent may not exist or ConnectError")
        else:
            res_dic.update({"transferred_url": transferred_url, "clone_id": tid})

            # Remove code and quote.
            raw_descr = res_dic["descr"]
            raw_descr = re.sub(r"\[(?P<bbcode>code|quote).+?\[/(?P=bbcode)\]", "", raw_descr, flags=re.S)
            raw_descr = re.sub(r"\u3000", " ", raw_descr)
            res_dic["descr"] = raw_descr

            logging.info("Get clone torrent's info,id: {tid},title:\"{ti}\"".format(tid=tid, ti=res_dic["name"]))
        return res_dic

    def date_raw_update(self, torrent_name_search, raw_info: dict) -> dict:
        if int(raw_info["category"]) == 402:  # Series
            raw_info["name"] = torrent_name_search.group("full_name")
            season_eposide_info_search = re.search("(?:[Ss](?P<season>\d+))?.*?(?:[Ee][Pp]?(?P<eposide>\d+))?",
                                                   torrent_name_search.group("episode"))
            season_eposide_info = ""
            if season_eposide_info_search.group("season"):
                season_eposide_info += "第{s}季".format(s=season_eposide_info_search.group("season"))
            if season_eposide_info_search.group("eposide"):
                season_eposide_info += "第{e}集".format(e=season_eposide_info_search.group("eposide"))
            raw_info["small_descr"] = re.sub(r"第.+([集季])", season_eposide_info, raw_info["small_descr"])
        elif int(raw_info["category"]) == 405:  # Anime
            raw_info["name"] = re.sub("\.(?P<episode>\d+)\.", ".{ep}.".format(ep=torrent_name_search.group("episode")),
                                      raw_info["name"])

        return raw_info

    def data_raw2tuple(self, torrent, raw_info):
        return (  # Submit form
            ("transferred_url", ('', str(raw_info["transferred_url"]))),
            ("type", ('', str(raw_info["category"]))),
            ("source_sel", ('', str(raw_info["sub_category"]))),
            ("file", self._post_torrent_file_tuple(torrent)),
            ("name", ('', string2base64(raw_info["name"]))),
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
