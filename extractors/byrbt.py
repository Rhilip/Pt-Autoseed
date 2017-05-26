# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import re

from .default import NexusPHP

type_dict = {
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
    }
}


def sort_title_info(raw_title, raw_type, raw_sec_type) -> dict:
    """
    the function (sort_title_info) will sort title to post_data due to clone_torrent's category
    But some may wrong,Due to inappropriate search_title
    """
    split = type_dict[raw_type]["split"]
    raw_title_group = re.findall(r"\[[^\]]*\]", raw_title)

    return_dict = {
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
        title_split = re.sub("\[(?P<in>.+)\]", "\g<in>", j)
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

    def __init__(self, site_setting):
        super().__init__(site_setting=site_setting)

    def torrent_clone(self, tid) -> dict:
        """
        Reconstruction from BYRBT Info Clone by Deparsoul version 20170400,thx
        This function will return a dict include (split_title,small_title,imdb_url,db_url,descr,before_torrent_id).
        """
        return_dict = {}
        details_bs = self.page_torrent_detail(tid=tid, bs=True)
        title_search = re.search("种子详情 \"(?P<title>.*)\" - Powered", str(details_bs.title))
        if title_search:
            title = title_search.group("title")
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
                img_tag["src"] = re.sub(r"images/(?:(?:\d+x)+|x)(?P<raw>.*)\.pagespeed\.ic.*",
                                        "images/\g<raw>", img_tag["src"])
            # Delete Clone Info
            if descr.find(class_="byrbt_info_clone"):
                descr.find(class_="byrbt_info_clone").extract()
            for fieldset in descr.find_all("fieldset"):
                fieldset.extract()
            descr_out = re.search(r"<div id=\"kdescr\">(?P<in>.+)</div>$", str(descr), re.S).group("in")
            return_dict.update({
                "small_descr": "",  # body.find(id="subtitle").find("li").text
                "url": imdb_url,
                "dburl": dburl,
                "descr": descr_out,
                "clone_id": tid
            })
        else:
            logging.error("Error,this torrent may not exist or ConnectError")
        return return_dict

    def data_raw2tuple(self, torrent, torrent_name_search, raw_info: dict):
        torrent_file_name = re.search("torrents/(.+?\.torrent)", torrent.torrentFile).group(1)
        post_tuple = ()
        if raw_info["type"] == 401:  # Series
            post_tuple = (  # Submit form
                ("type", ('', str(raw_info["type"]))),
                ("second_type", ('', str(raw_info["second_type"]))),
                ("file", (torrent_file_name, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
                ("tv_type", ('', str(raw_info["tv_type"]))),
                ("cname", ('', raw_info["cname"])),
                ("tv_ename", ('', torrent_name_search.group("full_name"))),
                ("tv_season", ('', torrent_name_search.group("episode"))),
                ("tv_filetype", ('', raw_info["tv_filetype"])),
                ("type", ('', str(raw_info["type"]))),
                ("small_descr", ('', raw_info["small_descr"])),
                ("url", ('', raw_info["url"])),
                ("dburl", ('', raw_info["dburl"])),
                ("nfo", ('', '')),  # 实际上并不是这样的，但是nfo一般没有，故这么写
                ("descr", ('', self.extend_descr(torrent=torrent, info_dict=raw_info))),
                ("uplver", ('', self.uplver)),
            )
        elif raw_info["type"] == 404:  # Anime
            post_tuple = (
                ("type", ('', str(raw_info["type"]))),
                ("second_type", ('', str(raw_info["second_type"]))),
                ("file", (torrent_file_name, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
                ("comic_type", ('', str(raw_info["comic_type"]))),
                ("subteam", ('', torrent_name_search.group("group"))),
                ("comic_cname", ('', raw_info["comic_cname"])),
                ("comic_ename", ('', raw_info["comic_ename"])),
                ("comic_episode", ('', torrent_name_search.group("episode"))),
                ("comic_quality", ('', raw_info["comic_quality"])),
                ("comic_source", ('', raw_info["comic_source"])),
                ("comic_filetype", ('', raw_info["comic_filetype"])),
                ("comic_year", ('', raw_info["comic_year"])),
                ("comic_country", ('', raw_info["comic_country"])),
                ("type", ('', str(raw_info["type"]))),
                ("small_descr", ('', raw_info["small_descr"])),
                ("url", ('', raw_info["url"])),
                ("dburl", ('', raw_info["dburl"])),
                ("nfo", ('', '')),
                ("descr", ('', self.extend_descr(torrent=torrent, info_dict=raw_info))),
                ("uplver", ('', self.uplver)),
            )

        return post_tuple
