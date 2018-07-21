# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>

import re
from html import unescape

from extractors.base.nexusphp import NexusPHP
from utils.constants import ubb_clean, episode_eng2chs, html2ubb, title_clean
from utils.load.handler import rootLogger as Logger

upload_dict = {
    "类型": {
        "key": "type",
        "values": {"Movies": 401, "Movies-3D": 402, "Concert": 419, "TV-Episode": 412, "TV-Pack": 405, "TV-Show": 413,
                   "Documentary": 410, "Animation": 411, "Sports": 415, "Music-Video": 414, "Music": 416},
    },
    "媒介": {
        "key": "medium_sel",
        "values": {"UHD Blu-ray": 12, "FHD Blu-ray": 1, "Remux": 3, "Encode": 7, "WEB-DL": 9, "HDTV": 5, "DVD": 2,
                   "CD": 8},
    },
    "编码": {
        "key": "codec_sel",
        "values": {"AVC/H.264": 12, "x264": 13, "HEVC/H.265": 14, "MPEG-2": 15, "VC-1": 16, "Xvid": 17, "Other": 18},
    },
    "音频编码": {
        "key": "audiocodec_sel",
        "values": {"Atmos": 14, "DTS X": 21, "DTS-HDMA": 1, "TrueHD": 2, "DTS": 4, "LPCM": 5, "FLAC": 13, "APE": 12,
                   "AAC": 7, "AC3": 6, "WAV": 11, "MPEG": 32},
    },
    "分辨率": {
        "key": "standard_sel",
        "values": {"SD": 4, "720p": 3, "1080i": 2, "1080p": 1, "4k": 5},
    },
    "地区": {
        "key": "processing_sel",
        "values": {"CN/中国大陆": 1, "US/EU/欧美": 2, "HK/TW/港台": 3, "JP/日": 4, "KR/韩": 5, "OT/其他": 6},
    },
    "制作组": {
        "key": "team_sel",
        "values": {"OurBits": 1, "PbK": 2, "OurPad": 3, "OurTV": 12, "iLoveTV": 42, "iLoveHD": 31, "HosT": 18,
                   "FFans": 43, "FFansWEB": 44, "DyFm": 41, "FLTTH": 46, "SBSUB": 45},
    },
}


class OurBits(NexusPHP):
    url_host = "https://ourbits.club"
    db_column = "ourbits.club"

    def torrent_clone(self, tid) -> dict:
        return_dict = {}
        details_bs = self.page_torrent_detail(tid=tid, bs=True)
        title_search = re.search("种子详情 \"(?P<title>.*)\" - Powered", str(details_bs.title))
        if title_search:
            body = details_bs.body
            return_dict["name"] = unescape(title_search.group("title")) or ""

            for pat, type_ in [("://movie.douban.com/subject", "dburl"), ("://www.imdb.com/title/tt", "url")]:
                a_another = body.find("a", href=re.compile(pat))
                return_dict[type_] = a_another.get_text() if a_another else ""

            descr_html = str(details_bs.find("div", id="kdescr"))
            return_dict["descr"] = ubb_clean(html2ubb(descr_html)) or ""

            def detail_fetch(text):
                return details_bs.find("td", text=text).next_sibling.get_text(" ", strip=True)

            return_dict["small_descr"] = detail_fetch("副标题") or ""

            info_gp = re.findall("([^：]+?[：:].+?) ", re.sub("大小.+?([TGMk]?B) ", "", detail_fetch("基本信息")))
            for info in info_gp:
                info_pat = re.search("([^：:]+?)[：: ]+(.+)", info)
                if info_pat:
                    key_human = info_pat.group(1).strip()
                    value_human = info_pat.group(2).strip()
                    try:
                        return_dict[upload_dict[key_human]["key"]] = upload_dict[key_human]["values"][value_human]
                    except (KeyError, TypeError):
                        pass
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
        regular_list = [
            ("name", raw_info["name"]),  # 标题
            ("small_descr", raw_info["small_descr"]),  # 副标题
            ("url", raw_info["url"]),  # IMDb链接
            ("dburl", raw_info["dburl"]),  # 豆瓣链接
            ("descr", raw_info["descr"]),  # 简介
            ("nfo", ""),  # 实际上并不是这样的，但是nfo一般没有，故这么写
            ("uplver", self._UPLVER),  # 匿名发布
        ]

        flexible_list = [
            (upload_dict[i]["key"], raw_info[upload_dict[i]["key"]] if upload_dict[i]["key"] in raw_info else "")
            for i in upload_dict]  # 自动生成 upload_dict 中对应表单信息

        # 部分非必填表单项未列入，如 hr, tagGF, tagDIY, tagSF, tagGY, tagZZ, tagJZ, tagBD
        return tuple(regular_list + flexible_list)
