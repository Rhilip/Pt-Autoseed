# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import re
import time

from html2bbcode.parser import HTML2BBCode

api_ptboard = "https://api.rhilip.info/tool/ptboard"

Support_Site = [
    # The tuple is like (config_dict_name in setting, Package name, Class name)
    ("site_byrbt", "extractors.byrbt", "Byrbt"),
    ("site_npubits", "extractors.npubits", "NPUBits"),
    ("site_nwsuaf6", "extractors.nwsuaf6", "MTPT"),
    ("site_tjupt", "extractors.tjupt", "TJUPT"),
    ("site_hudbt", "extractors.hudbt", "HUDBT"),
    ("site_ourbits", "extractors.ourbits", "OurBits")
]

Video_Containers = [
    # From: https://mediaarea.net/en/MediaInfo/Support/Formats
    ".mkv",  # Matroska
    ".mp4",  # Mpeg 4 container
]

REV_TAG = [
    "repack", "proper", "real",  # Series
    "v2", "rev"  # Anime
]

pat_rev_tag = re.compile("|".join(REV_TAG))


def period_f(func, sleep_time):
    while True:
        func()
        time.sleep(sleep_time)


def ubb_clean(string: str) -> str:
    string = re.sub(r"\[(?P<bbcode>code|quote).+?\[/(?P=bbcode)\]", "", string, flags=re.S)  # Remove code and quote
    string = re.sub(r"\u3000", " ", string)
    return string


def title_clean(noext: str) -> str:
    noext = re.sub("H\.264", "H_264", noext)
    noext = re.sub("([25])\.1", r"\1_1", noext)
    noext = re.sub("\.", " ", noext)
    noext = re.sub("H_264", "H.264", noext)
    noext = re.sub("([25])_1", r"\1.1", noext)
    return noext


def episode_eng2chs(ep: str) -> str:
    season_episode_info_search = re.search("(?:[Ss](?P<season>\d+))?.*?(?:[Ee][Pp]?(?P<episode>\d+))?", ep)
    season_episode_info = ""
    if season_episode_info_search.group("season"):
        season_episode_info += "第{s}季".format(s=season_episode_info_search.group("season"))
    if season_episode_info_search.group("episode"):
        season_episode_info += " 第{e}集".format(e=season_episode_info_search.group("episode"))
    return season_episode_info


def html2ubb(html: str) -> str:
    ret = str(HTML2BBCode().feed(html))
    ret = re.sub("\n\n", "\n", ret)
    return ret
