# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import re

from extractors.base.nexusphp import NexusPHP
from utils.constants import ubb_clean
from utils.load.handler import rootLogger as Logger

filetype_list = ["MKV", "RMVB", "MP4", "AVI", "MPEG", "ts", "ISO", "其他文件类型"]
resolution_list = ["1080P", "720P", "480P", "其他"]
quality_list = ["DVDrip", "HDRip", "BDRip", "R5", "DVDScr", "BDMV", "BDISO", "DVDISO", "其他品质"]
country_list = ["大陆", "港台", "欧美", "日韩", "其他地区"]
subtitle_list = ["简体中文", "繁体中文", "英文字幕", "中英字幕", "中日字幕", "中韩字幕", "无需字幕", "外挂字幕", "暂无字幕", "其他字幕"]

title_split_dict = {
    "401": {  # 电影
        "order": ["release_time", "chinese_name", "english_name", "filetype"],
        "limit": {
            "filetype": filetype_list,
        }
    },
    "402": {  # 剧集
        "order": ["release_time", "chinese_name", "english_name", "jidu", "filetype", "serial"],
        "limit": {
            "filetype": filetype_list,
            "serial": ["剧场/OVA", "完结剧集", "连载剧集"]
        }
    },
    "403": {  # 综艺
        "order": ["country", "release_time", "chinese_name", "english_name", "resolution", "filetype"],
        "limit": {
            "country": country_list,
            "resolution": ["1080P", "720P", "480P", "其他"],
            "filetype": filetype_list,
        }
    },
    "405": {  # 动漫
        "order": ["month", "chinese_name", "english_name", "num", "subtitle_group",
                  "subtitle", "resolution", "quality", "filetype", "wanjieornot"],
        "limit": {
            "subtitle": ["简体GB", "繁体BIG5", "繁简外挂", "简体外挂", "繁体外挂", "无字幕", "其他"],
            "resolution": resolution_list,
            "quality": quality_list,
            "filetype": filetype_list,
            "wanjieornot": ["完结", "连载"]
        }
    },
    "414": {  # 音乐
        "order": ["chinese_name", "wusunornot", "name", "author", "codetype", "code"],
        "limit": {
            "wusunornot": ["无损"],
        }
    },
    "407": {  # 体育
        "order": ["release_time", "style", "program_name", "language", "filetype", "quality", "zhuanzai"],
        "limit": {
            "language": ["国语", "粤语", "英语", "日语", "韩语", "法语", "德语", "西班牙语", "其他语言"],
            "filetype": filetype_list
        }
    },
    "404": {  # 纪录片
        "order": ["source", "release_time", "chinese_name", "english_name", "resolution", "quality", "subtitle",
                  "filetype"],
        "limit": {
            "resolution": resolution_list,
            "quality": quality_list,
            "subtitle": subtitle_list,
            "filetype": filetype_list
        }
    },
    "406": {  # MV
        "order": ["country", "release_time", "artist", "file_name", "style", "filetype"],
        "limit": {
            "country": country_list,
            "filetype": filetype_list
        }
    },
    "408": {  # 软件
        "order": ["platform", "edition", "softwareLanguage", "software_type"],
        "limit": {
            "platform": ["Windows", "Mac", "Linux", "Mobile", "Android", "其他平台"],
            "softwareLanguage": ["简体中文", "繁体中文", "英语", "日语", "韩语", "其他语言"],
        }
    },
    "410": {  # 游戏
        "order": ["release_time", "chinese_name", "english_name", "game_type", "company", "format", "edition"],
        "limit": {}
    },
    "411": {  # 学习
        "order": ["xueke", "release_time", "school", "chinese_name", "english_name", "jishu", "subtitle", "filetype"],
        "limit": {
            "subtitle": subtitle_list,
            "filetype": filetype_list
        }
    },
    "423": {  # 原创
        "order": [],
        "limit": {}
    },
    "409": {  # 其他
        "order": [],
        "limit": {}
    }
}


class MTPT(NexusPHP):
    url_host = "https://pt.nwsuaf6.edu.cn"
    db_column = "pt.nwsuaf6.edu.cn"

    def torrent_clone(self, tid) -> dict:
        """
        Use Internal API: http://pt.nwsuaf6.edu.cn/citetorrent.php?torrent_id={tid} ,Request Method: GET
        Will response a json dict.
        """
        res_dic = {}
        try:
            res_dic = self.get_data(url=self.url_host + "/citetorrent.php", params={"torrent_id": tid}, json=True)
        except ValueError:
            Logger.error("Error,this torrent may not exist or ConnectError")
        else:
            res_dic["clone_id"] = tid
            res_dic["descr"] = ubb_clean(res_dic["descr"])
            res_dic["type"] = res_dic["category"]

            Logger.info("Get clone torrent's info,id: {tid},title:\"{ti}\"".format(tid=tid, ti=res_dic["name"]))
        return res_dic

    def date_raw_update(self, torrent_name_search, raw_info: dict) -> dict:

        raw_title = raw_info["name"]
        cat = raw_info["category"]

        split = title_split_dict[cat]["order"]
        raw_title_group = re.findall(r"\[[^\]]*\]", raw_title)
        temporarily_dict = {}

        len_split = len(title_split_dict[cat]["order"])
        # TODO if len_split == 0:
        if len_split != len(raw_title_group):
            Logger.warning("The raw title \"{raw}\" may lack of tag (now: {no},ask: {co}),"
                            "The split may wrong.".format(raw=raw_title, no=len(raw_title_group), co=len_split))
            while len_split > len(raw_title_group):
                raw_title_group.append("")
        raw_title_group.reverse()
        for i in split:
            j = raw_title_group.pop()
            title_split = re.sub("\[(?P<in>.+)\]", "\g<in>", j)
            if i in title_split_dict[cat]["limit"]:
                if title_split not in title_split_dict[cat]["limit"][i]:
                    title_split = ""  # type_dict[raw_type]["limit"][i][0]
                    raw_title_group.append(j)
            temporarily_dict.update({i: title_split})

        # Update temporarily dict
        if cat == "402":  # Series
            temporarily_dict["english_name"] = torrent_name_search.group("full_name")
            temporarily_dict["jidu"] = torrent_name_search.group("episode")
        elif cat == "405":  # Anime
            temporarily_dict["num"] = torrent_name_search.group("episode")

        # Generate new title
        new_title = ""
        for i in split:
            inner = temporarily_dict[i]
            if len(inner) is not 0:
                new_title += "[{inner}]".format(inner=inner)

        # Assign raw info
        raw_info["name"] = new_title

        return raw_info

    def data_raw2tuple(self, torrent, raw_info):
        return (  # Submit form
            ("cite_torrent", raw_info["clone_id"]),
            ("ismttv", "no"),
            ("prohibit_reshipment", 'no_restrain'),
            ("type", raw_info["category"]),
            ("source_sel", raw_info["source"]),
            ("name", raw_info["name"]),
            ("small_descr", raw_info["small_descr"]),
            ("imdburl", raw_info["url"]),
            ("dburl", raw_info["dburl"]),
            ("nfo", ""),  # 实际上并不是这样的，但是nfo一般没有，故这么写
            ("color", 0),  # Tell me those three key's function~
            ("font", 0),
            ("size", 0),
            ("descr", self.enhance_descr(torrent=torrent, info_dict=raw_info)),
            ("uplver", self._UPLVER),
        )
