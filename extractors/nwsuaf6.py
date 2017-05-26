# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import re

from .default import NexusPHP

title_split_dict = {
    "402": {  # 剧集
        "order": ["release_time", "chinese_name", "english_name", "jidu", "filetype", "serial"],
        "limit": {
            "filetype": ["MKV", "RMVB", "MP4", "AVI", "MPEG", "ts", "ISO", "其他文件类型"],
            "serial": ["剧场/OVA", "完结剧集", "连载剧集"]
        }
    },
    "405": {  # 动漫
        "order": ["month", "chinese_name", "english_name", "num", "subtitle_group",
                  "subtitle", "resolution", "quality", "filetype", "wanjieornot"],
        "limit": {
            "subtitle": ["简体GB", "繁体BIG5", "繁简外挂", "简体外挂", "繁体外挂", "无字幕", "其他"],
            "resolution": ["1080P", "720P", "480P", "其他"],
            "quality": ["DVDrip", "HDRip", "BDRip", "R5", "DVDScr", "BDMV", "BDISO", "DVDISO", "其他品质"],
            "filetype": ["MKV", "RMVB", "MP4", "AVI", "MPEG", "ts", "ISO", "其他文件类型"],
            "wanjieornot": ["完结", "连载"]
        }
    }
}


def update_title(raw_title, cat, torrent_title_search):  # -> str
    # Separate raw title
    split = title_split_dict[cat]["order"]
    raw_title_group = re.findall(r"\[[^\]]*\]", raw_title)
    temporarily_dict = {}

    len_split = len(title_split_dict[cat]["order"])
    if len_split != len(raw_title_group):
        logging.warning("The raw title \"{raw}\" may lack of tag (now: {no},ask: {co}),"
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
        temporarily_dict["english_name"] = torrent_title_search.group("full_name")
        temporarily_dict["jidu"] = torrent_title_search.group("episode")
    elif cat == "405":  # Anime
        temporarily_dict["num"] = torrent_title_search.group("episode")

    # Generate new title
    new_title = ""
    for i in split:
        new_title += "[{inner}]".format(inner=temporarily_dict[i])

    return new_title


class MTPT(NexusPHP):
    url_host = "http://pt.nwsuaf6.edu.cn"
    db_column = "pt.nwsuaf6.edu.cn"

    def __init__(self, site_setting):
        super().__init__(site_setting=site_setting)

    def torrent_clone(self, tid) -> dict:
        """
        Use Internal API: http://pt.nwsuaf6.edu.cn/citetorrent.php?torrent_id={tid} ,Request Method: GET
        Will response a json dict.
        """
        try:
            res_dic = self.get_page(url="{host}/citetorrent.php".format(host=self.url_host), params={"torrent_id": tid},
                                    json=True)
        except ValueError:
            logging.error("Error,this torrent may not exist or ConnectError")
            res_dic = {}
        else:
            res_dic.update({"clone_id": tid})

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
        name = update_title(raw_title=raw_info["name"], cat=raw_info["category"],
                            torrent_title_search=title_search_group)

        post_tuple = (  # Submit form
            ("cite_torrent", ('', str(raw_info["clone_id"]))),
            ("file", (torrent_file_name, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
            ("type", ('', str(raw_info["category"]))),
            ("source_sel", ('', str(raw_info["source"]))),
            ("name", ('', name)),
            ("small_descr", ('', raw_info["small_descr"])),
            ("imdburl", ('', raw_info["url"])),
            ("dburl", ('', raw_info["dburl"])),
            ("nfo", ('', '')),  # 实际上并不是这样的，但是nfo一般没有，故这么写
            ("color", ('', '0')),  # Tell me those three key's function~
            ("font", ('', '0')),
            ("size", ('', '0')),
            ("descr", ('', self.extend_descr(torrent=torrent, info_dict=raw_info))),
            ("uplver", ('', self.uplver)),
        )

        return post_tuple
