# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import logging
import re
from html import unescape
from urllib.parse import unquote

from extractors.nexusphp import NexusPHP

type_dict = {
    "电影": {
        "cat": 408,
        "sec_type": {"华语": 11, "欧洲": 12, "北美": 13, "亚洲": 14, "其他": 1},
        "split": ["movie_cname", "ename0day", "movie_type", "movie_country"],
        "limit": {
            "movie_type": ["喜剧", "动作", "爱情", "文艺", "剧情", "科幻", "魔幻", "悬疑", "惊悚",
                           "恐怖", "罪案", "战争", "纪录", "动画", "音乐", "歌舞", "冒险", "历史"],
            "movie_country": ["华语", "亚洲", "欧洲", "北美", "其他"]
        }
    },
    "剧集": {
        "cat": 401,
        "sec_type": {"大陆": 15, "日韩": 16, "欧美": 17, "港台": 18, "其他": 2},
        "split": ["tv_type", "cname", "tv_ename", "tv_season", "tv_filetype"],
        "limit": {
            "tv_type": ["欧美", "大陆", "港台", "日韩", "其他"],
            "tv_filetype": ["MKV", "TS", "M2TS", "MP4", "AVI", "VOB", "RMVB", "其他"]
        }
    },
    "动漫": {
        "cat": 404,
        "sec_type": {"动画": 19, "漫画": 20, "音乐": 21, "周边": 22, "其他": 3},
        "split": ["comic_type", "subteam", "comic_cname", "comic_ename", "comic_episode",
                  "comic_quality", "comic_source", "comic_filetype", "comic_year", "comic_country"],
        "limit": {
            "comic_type": ["连载", "长篇", "TV", "剧场", "OVA", "OAD", "MAD", "漫画", "画集", "周边", "音乐", "演唱会"],
            "comic_quality": ["720p", "1080p", "480p", "576p"],
            "comic_source": ["TVRip", "BDRip", "DVDRip", "WEB", "BDMV", "DVDISO"],
            "comic_filetype": ["MP4", "MKV", "RMVB", "AVI", "WMV", "ZIP", "RAR",
                               "7Z", "MP3", "APE", "FLAC", "WAV", "TTA", "TAK"],
            "comic_country": ["日漫", "美漫", "国产", "其他"]
        }
    },
    "音乐": {
        "cat": 402,
        "sec_type": {"大陆": 23, "港台": 24, "日韩": 25, "欧美": 26, "其他": 4},
        "split": ["music_type", "artist", "album", "music_style",
                  "music_filetype", "music_quality", "music_year", "music_language"],
        "limit": {
            "music_type": ["合集", "专辑", "单曲", "MV", "演唱会", "音乐会", "戏剧"],
            "music_style": ["流行", "发烧", "古典", "民族", "摇滚", "原声(OST)", "民间", "乡村",
                            "天籁", "新世纪", "蓝调", "爵士", "金属", "电子", "贝斯", "说唱"],
            "music_filetype": ["WAV", "APE", "MP3", "AAC", "FLAC", "DTS", "OGG",
                               "MKV", "DAT", "TS", "ISO", "AVI", "其他"],
            "music_quality": ["无损", "VBR", "192Kbps", "256Kbps", "320Kbps", "1080P", "1080I", "720P", "480P"],
            "music_language": ["大陆", "港台", "日韩", "欧美", "其他"]
        }
    },
    "综艺": {
        "cat": 405,
        "sec_type": {"大陆": 27, "日韩": 28, "港台": 29, "欧美": 30, "其他": 5},
        "split": ["show_year", "show_country", "show_cname", "show_ename", "show_language", "hassub", "addition"],
        "limit": {
            "show_country": ["大陆", "港台", "欧美", "日韩", "其他"],
            "show_language": ["国语", "粤语", "英语", "日语", "韩语"],
            "hassub": ["暂无字幕", "中文字幕", "英文字幕", "中英字幕", "无需字幕"]
        }
    },
    "游戏": {
        "cat": 403,
        "sec_type": {"PC": 31, "主机": 32, "移动": 33, "掌机": 34, "视频": 35, "其他": 6},
        "split": ["platform", "ename", "gamecname", "game_type", "company", "game_language", "game_filetype"],
        "limit": {
            "platform": ["PC", "PSP", "NDS", "GBA", "NGC", "Wii", "PS", "PS2", "XBOX", "XBOX360", "周边", "视频"],
            "game_type": ["ACT", "AVG", "FPS", "FTG", "MUG", "PUZ", "TCG", "SIM", "TAB", "SPG", "RAG", "STG", "SLG",
                          "RTS", "RPG", "SRPG", "ARPG", "其他"],
            "game_language": ["英文", "日文", "官方繁体", "官方简体", "简体汉化", "繁体汉化", "其他"],
            "game_filetype": ["光盘镜像", "压缩包", "安装包", "MP4", "其他"]
        }
    },
    "软件": {
        "cat": 406,
        "sec_type": {"Windows": 36, "OSX": 37, "Linux": 38, "Android": 39, "iOS": 40, "其他": 7},
        "split": ["software_environment", "software_type", "software_cname", "software_ename",
                  "software_version", "software_language", "software_filetype"],
        "limit": {
            "software_environment": ["Windows", "Linux", "MacOSX", "iOS", "Android", "Symbian", "其他"],
            "software_type": ["操作系统", "编程开发", "行业软件", "安全软件", "媒体播放", "媒体处理", "网络应用",
                              "办公软件", "教育软件", "系统工具", "驱动", "补丁", "其他"],
            "software_language": ["英文", "官方简体", "官方繁体", "简体汉化", "繁体汉化", "多国语言"],
            "software_filetype": ["光盘镜像", "压缩包", "安装包", "其他"]
        }
    },
    "资料": {
        "cat": 407,
        "sec_type": {"公开课": 41, "出版物": 42, "学习教程": 43, "素材模板": 44, "演讲交流": 45, "生活娱乐": 46, "其他": 8},
        "split": ["document_type", "cname", "ename", "document_filetype", "version", "year"],
        "limit": {
            "document_type": ["素材模版", "精彩图集", "公开课程", "考试面试", "生活日常", "学习教程",
                              "演讲交流", "语言哲学", "期刊书籍", "经济管理", "消遣娱乐"],
            "document_filetype": ["AVI", "ASF", "WMV", "MKV", "CSF", "MPG", "MOV", "RM", "RMVB", "MP4", "FLV", "SWF",
                                  "NCE", "APE", "MP3", "FLAC", "WMA", "WAV", "PDF", "EXE", "PDG", "DJVU", "CHM", "PPT",
                                  "DOC", "RTF", "TXT", "JPG", "GIF", "BMP", "RAR", "ISO"],
        }
    },
    "体育": {
        "cat": 409,
        "sec_type": {"篮球": 47, "足球": 48, "F1": 49, "网球": 50, "其他": 9},
        "split": ["sport_type", "sport_year", "sport_cname", "sport_language", "sport_filetype", "sport_quality"],
        "limit": {
            "sport_type": ["足球", "篮球", "摔跤", "斯诺克", "羽毛球", "F1"],
            "sport_filetype": ["RMVB", "MP4", "AVI", "MKV", "RM", "WMV", "ASF", "TS"],
        }
    },
    "纪录": {
        "cat": 410,
        "sec_type": {"纪录": 10},
        "split": ["record_whetherend", "record_type", "cname", "record_ename", "record_season", "record_filetype",
                  "record_source", "record_format", "record_group", "record_area"],
        "limit": {
            "record_whetherend": ["单集", "合集", "连载"],
            "record_type": ["IMAX", "BBC", "NHK", "PBS", "Ch4", "CCTV", "BTV", "国家地理", "历史频道", "探索频道", "其他"],
            # "record_filetype": ["1080p", "1080i", "720p", "576p", "480p", "其他"],
            "record_source": ["Blu-ray", "DVD", "TV", "Web-DL"],
            # "record_format": ["MKV", "MP4", "TS", "M2TS", "VOB", "AVI"],
            # "record_group": ["MVGroup", "DON", "PublicHD", "WiKi", "CHD", "HDWinG", "CMCT", "beAst", "YYeTs",
            #                  "NGB", "道兰", "夏末秋"],
            # "record_area": ["自然", "科学", "生理", "技术", "历史", "传记", "文化", "艺术", "社会", "军事", "旅行", "生活", "真人秀"]
        }
    },
}

pat_tag_pass_by_class = re.compile("byrbt_info_clone|autoseed")


def sort_title_info(raw_title, raw_type, raw_sec_type) -> dict:
    """
    the function (sort_title_info) will sort title to post_data due to clone_torrent's category
    But some may wrong,Due to inappropriate search_title
    """
    split = type_dict[raw_type]["split"]
    raw_title_group = re.findall(r"\[[^\]]*\]", raw_title)

    return_dict = {
        "raw_type": raw_type,
        "raw_second_type": raw_sec_type,
        "type": type_dict[raw_type]["cat"],
        "second_type": type_dict[raw_type]["sec_type"][raw_sec_type],
    }

    len_split = len(type_dict[raw_type]["split"])
    if len_split != len(raw_title_group):
        logging.warning("The raw title \"{raw}\" may lack of tag (now: {no},ask: {co}),"
                        "The split may wrong.".format(raw=raw_title, no=len(raw_title_group), co=len_split))
        while len_split > len(raw_title_group):
            raw_title_group.append("")
    raw_title_group.reverse()

    for i in split:
        j = raw_title_group.pop()
        title_split = re.sub("\[(?P<in>.*)\]", "\g<in>", j)
        if i in type_dict[raw_type]["limit"]:
            if title_split not in type_dict[raw_type]["limit"][i]:
                title_split = ""  # type_dict[raw_type]["limit"][i][0]
                raw_title_group.append(j)
        return_dict.update({i: title_split})
    logging.debug("the title split success.The title dict:{dic}".format(dic=return_dict))
    return return_dict


class Byrbt(NexusPHP):
    url_host = "http://bt.byr.cn"
    db_column = "tracker.byr.cn"

    encode = "html"

    def __init__(self, status, cookies, passkey, **kwargs):
        # Site Features: POST without subtitle, change in data_raw_update()
        self._NO_SUBTITLE = kwargs.setdefault("no_subtitle", False)

        super().__init__(status, cookies, passkey, **kwargs)

    def page_torrent_detail(self, tid, bs=False):
        return self.get_data(url=self.url_host + "/details.php", params={"id": tid, "ModPagespeed": "off"}, bs=bs)

    def torrent_clone(self, tid) -> dict:
        """
        Reconstruction from BYRBT Info Clone by Deparsoul version 20170400,thx
        This function will return a dict include (split_title,small_title,imdb_url,db_url,descr,before_torrent_id).
        """
        return_dict = {}
        details_bs = self.page_torrent_detail(tid=tid, bs=True)
        title_search = re.search("种子详情 \"(?P<title>.*)\" - Powered", str(details_bs.title))
        if title_search:
            title = unescape(title_search.group("title"))
            logging.info("Get clone torrent's info,id: {tid},title:\"{ti}\"".format(tid=tid, ti=title))
            title_dict = sort_title_info(raw_title=title, raw_type=details_bs.find("span", id="type").text.strip(),
                                         raw_sec_type=details_bs.find("span", id="sec_type").text.strip())
            return_dict.update(title_dict)
            body = details_bs.body
            imdb_url = dburl = ""
            if body.find(class_="imdbRatingPlugin"):
                imdb_url = 'http://www.imdb.com/title/' + body.find(class_="imdbRatingPlugin")["data-title"]
                logging.debug("Found imdb link:{link} for this torrent.".format(link=imdb_url))
            if body.find("a", href=re.compile("://movie.douban.com/subject")):
                dburl = body.find("a", href=re.compile("://movie.douban.com/subject")).text
                logging.debug("Found douban link:{link} for this torrent.".format(link=dburl))
            # Update description
            descr = body.find(id="kdescr")

            # Restore the image link
            for img_tag in descr.find_all("img"):
                del img_tag["onload"]
                del img_tag["data-pagespeed-url-hash"]
                img_tag["src"] = unquote(re.sub(r"images/(?:(?:\d+x)+|x)(?P<raw>.*)\.pagespeed\.ic.*",
                                                "images/\g<raw>", img_tag["src"]))

            # Remove unnecessary description (class: autoseed, byrbt_info_clone_ignore, byrbt_info_clone)
            for tag in descr.find_all(class_=pat_tag_pass_by_class):
                tag.extract()

            descr_out = re.search(r"<div id=\"kdescr\">(?P<in>.+)</div>$", str(descr), re.S).group("in")
            return_dict.update({
                "small_descr": body.find(id="subtitle").find("li").text,
                "url": imdb_url,
                "dburl": dburl,
                "descr": descr_out,
                "clone_id": tid
            })
        else:
            logging.error("Error,this torrent may not exist or ConnectError")
        return return_dict

    def date_raw_update(self, torrent_name_search, raw_info: dict) -> dict:
        if raw_info["type"] == 401:  # Series
            raw_info["tv_ename"] = torrent_name_search.group("full_name")
            raw_info["tv_season"] = torrent_name_search.group("episode")
        elif raw_info["type"] == 404:  # Anime
            raw_info["comic_episode"] = torrent_name_search.group("episode")

        if self._NO_SUBTITLE:
            raw_info["small_descr"] = ""

        return raw_info

    def data_raw2tuple(self, torrent, raw_info: dict):
        begin_list = [
            ("type", ('', str(raw_info["type"]))),
            ("second_type", ('', str(raw_info["second_type"]))),
            ("file", self._post_torrent_file_tuple(torrent))
        ]

        cat_post_list = [(cat, ('', str(raw_info[cat]))) for cat in type_dict[raw_info["raw_type"]]["split"]]

        end_post_list = [
            ("type", ('', str(raw_info["type"]))),
            ("small_descr", ('', raw_info["small_descr"])),
            ("url", ('', raw_info["url"])),
            ("dburl", ('', raw_info["dburl"])),
            ("nfo", ('', '')),
            ("descr", ('', self.enhance_descr(torrent=torrent, info_dict=raw_info))),
            ("uplver", ('', self._UPLVER)),
        ]

        return tuple(begin_list + cat_post_list + end_post_list)
