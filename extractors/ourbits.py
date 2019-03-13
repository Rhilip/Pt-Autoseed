# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>

import re

import requests

from extractors.base.nexusphp import NexusPHP
from utils.constants import ubb_clean, episode_eng2chs, title_clean
from utils.load.handler import rootLogger as Logger


class OurBits(NexusPHP):
    url_host = "https://ourbits.club"
    db_column = "ourbits.club"

    def exist_torrent_title(self, tag):
        torrent_page = self.page_torrent_detail(tid=tag, bs=True)
        torrent_title = re.search("\[OurBits\]\.(?P<name>.+?)\.torrent", torrent_page.text).group("name")
        Logger.info("The torrent name for id({id}) is \"{name}\"".format(id=tag, name=torrent_title))
        return torrent_title

    def torrent_clone(self, tid) -> dict:
        return_dict = {}

        api_res = self.post_data(self.url_host + "/api.php", data={"action": "getTorrentData", "torrentId": tid})
        api_json = api_res.json()

        if api_json["success"]:
            return_dict["clone_id"] = tid
            return_dict["name"] = api_json["name"]
            return_dict["small_descr"] = api_json["small_descr"]
            return_dict["url"] = ("https://www.imdb.com/title/tt" + api_json["url"]) if api_json["url"] else ""
            return_dict["dburl"] = ("https://movie.douban.com/subject/" + api_json["dburl"]) if api_json[
                "dburl"] else ""
            return_dict["descr"] = ubb_clean(api_json["descr"])
            return_dict["type"] = api_json["category"]
            for i in ["medium", "codec", "audiocodec", "standard", "processing", "team"]:
                return_dict[i + "_sel"] = api_json[i]
        else:
            Logger.error("Error,this torrent may not exist or ConnectError")
        return return_dict

    def date_raw_update(self, torrent, torrent_name_search, raw_info: dict) -> dict:
        raw_info["descr"] = self.enhance_descr(torrent, raw_info["descr"], raw_info["clone_id"])
        type_ = int(raw_info["type"])
        if type_ in [412, 405]:  # TV-Episode, TV-Pack
            torrent_raw_name = torrent_name_search.group("full_name")
            raw_info["name"] = title_clean(torrent_raw_name)
            season_episode_info = episode_eng2chs(torrent_name_search.group("episode"))
            raw_info["small_descr"] = re.sub(r"第.+([集季])", season_episode_info, raw_info["small_descr"])

        return raw_info

    def data_raw2tuple(self, raw_info: dict) -> tuple:
        upload_list = ["name", "small_descr", "url", "dburl", "type", "descr",
                       "medium_sel", "codec_sel", "audiocodec_sel", "standard_sel", "processing_sel", "team_sel"]
        regular_list = [(i, raw_info[i]) for i in upload_list]  # 自动生成 upload_dict 中对应表单信息

        other_list = [
            ("nfo", ""),  # 实际上并不是这样的，但是nfo一般没有，故这么写
            ("uplver", self._UPLVER),  # 匿名发布
        ]

        # 部分非必填表单项未列入，如 hr, tagGF, tagDIY, tagSF, tagGY, tagZZ, tagJZ, tagBD
        return tuple(regular_list + other_list)
