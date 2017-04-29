# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import logging

from bs4 import BeautifulSoup
from .default import NexusPHP

type_dict = {
    "电影": {"cat": 408,
           "sec_type": {"华语": 11, "欧洲": 12, "北美": 13, "亚洲": 14, "其他": 1},
           "split": ["movie_cname", "ename0day", "movie_type", "movie_country"],
           "limit": {
               "movie_type": ["喜剧", "动作", "爱情", "文艺", "剧情", "科幻", "魔幻", "悬疑", "惊悚",
                              "恐怖", "罪案", "战争", "纪录", "动画", "音乐", "歌舞", "冒险", "历史"],
               "movie_country": ["华语", "亚洲", "欧洲", "北美", "其他"]
           }
           },
    "剧集": {"cat": 401,
           "sec_type": {"大陆": 15, "日韩": 16, "欧美": 17, "港台": 18, "其他": 2},
           "split": ["tv_type", "cname", "tv_ename", "tv_season", "tv_filetype"],
           "limit": {
               "tv_type": ["欧美", "大陆", "港台", "日韩", "其他"],
               "tv_filetype": ["MKV", "TS", "M2TS", "MP4", "AVI", "VOB", "RMVB", "其他"]
           }
           },
    "动漫": {"cat": 404,
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
    "综艺": {"cat": 405,
           "sec_type": {"大陆": 27, "日韩": 28, "港台": 29, "欧美": 30, "其他": 5},
           "split": ["show_year", "show_country", "show_cname", "show_ename", "show_language", "hassub", "addition"],
           "limit": {
               "show_country": ["大陆", "港台", "欧美", "日韩", "其他"],
               "show_language": ["国语", "粤语", "英语", "日语", "韩语"],
               "hassub": ["暂无字幕", "中文字幕", "英文字幕", "中英字幕", "无需字幕"]
           }
           },
}


def sort_title_info(raw_title, raw_type, raw_sec_type) -> dict:
    split = type_dict[raw_type]["split"]
    raw_title_group = re.findall(r"\[[^\]]*\]", raw_title)

    return_dict = {
        "type": type_dict[raw_type]["cat"],
        "sec_type": type_dict[raw_type]["sec_type"][raw_sec_type],
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
    url_torrent_download = "http://bt.byr.cn/download.php?id={tid}&passkey={pk}"
    url_torrent_upload = "http://bt.byr.cn/takeupload.php"
    url_torrent_detail = "http://bt.byr.cn/details.php?id={tid}&hit=1"
    url_thank = "http://bt.byr.cn/thanks.php"
    url_search = "http://bt.byr.cn/torrents.php?search={k}&search_mode={md}"

    reseed_column = "tracker.byr.cn"

    def __init__(self, setting):
        _site_setting = setting.site_byrbt
        super().__init__(setting=setting, site_setting=_site_setting)

    def exist_judge(self, search_title, torrent_file_name) -> int:
        """如果种子在byr存在，返回种子id，不存在返回0，已存在且种子一致返回种子号，不一致返回-1"""
        tag = self.get_last_torrent_id(search_key=search_title, search_mode=2)
        if tag is not 0:
            details_bs = BeautifulSoup(self.page_torrent_detail_text(tid=tag), "lxml")
            torrent_title_in_site = details_bs.find("a", class_="index", href=re.compile(r"^download.php")).string
            torrent_title = re.search(r"\[BYRBT\]\.(.+?)\.torrent", torrent_title_in_site).group(1)
            if torrent_file_name != torrent_title:  # Use pre-reseed torrent's name match the exist torrent's name
                tag = -1
        return tag

    def clone_from(self, search_key) -> dict:
        """
        Reconstruction from BYRBT Info Clone by Deparsoul version 20170400,thx
        This function will automatically search the clone torrent,no database need !!!
        But some may wrong,Due to inappropriate search_title
        and will return a dict include (title,small_title,imdb_url,db_url,descr,before_torrent_id) from it.
        the function (sort_title_info) will sort title to post_data due to clone_torrent's category
        """
        return_dict = {}
        tag = self.get_last_torrent_id(search_key=search_key, search_mode=0)
        if tag is not 0:
            details_bs = BeautifulSoup(self.page_torrent_detail_text(tid=tag), "lxml")
            title_search = re.search("种子详情 \"(?P<title>.*)\" - Powered", str(details_bs.title))
            if title_search:
                title = title_search.group("title")
                logging.info("Get clone torrent's info,id: {tid},title:\"{ti}\"".format(tid=tag, ti=title))
                title_dict = sort_title_info(raw_title=title, raw_type=details_bs.find("span", id="type").text.strip(),
                                             raw_sec_type=details_bs.find("span", id="sec_type").text.strip())
                return_dict.update(title_dict)
                body = details_bs.body
                imdb_url = dburl = ""
                if body.find(class_="imdbRatingPlugin"):
                    logging.debug("Found imdb link for this torrent.")
                    imdb_url = 'http://www.imdb.com/title/' + body.find(class_="imdbRatingPlugin")["data-title"]
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
                for i in descr.find_all(class_="autoseed"):  # New class
                    i.extract()
                # Old class
                if descr.find("fieldset", class_="before"):
                    descr.find("fieldset", class_="before").extract()
                if descr.find("fieldset", class_="screenshot"):
                    descr.find("fieldset", class_="screenshot").extract()
                if descr.find("fieldset", class_="mediainfo"):
                    descr.find("fieldset", class_="mediainfo").extract()
                descr_out = re.search(r"<div id=\"kdescr\">(?P<in>.+)</div>$", str(descr), re.S).group("in")
                return_dict.update({
                    "small_descr": body.find(id="subtitle").find("li").text,
                    "url": imdb_url,
                    "dburl": dburl,
                    "descr": descr_out,
                    "before_torrent_id": tag
                })
            else:
                logging.error("Error,this torrent may not exist or ConnectError")

        return return_dict

    def data_series_raw2tuple(self, torrent, torrent_info_search, torrent_raw_info_dict) -> tuple:
        torrent_file_name = re.search("torrents/(.+?\.torrent)", torrent.torrentFile).group(1)
        # 副标题 small_descr
        small_descr = "{0} {1}".format(torrent_raw_info_dict["small_descr"], torrent_info_search.group("tv_season"))
        if str(torrent_info_search.group("group")).lower() == "fleet":
            small_descr += " |fleet慎下"

        return (  # Submit form
            ("type", ('', str(torrent_raw_info_dict["type"]))),
            ("second_type", ('', str(torrent_raw_info_dict["second_type"]))),
            ("file", (torrent_file_name, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
            ("tv_type", ('', str(torrent_raw_info_dict["tv_type"]))),
            ("cname", ('', torrent_raw_info_dict["cname"])),
            ("tv_ename", ('', torrent_info_search.group("full_name"))),
            ("tv_season", ('', torrent_info_search.group("tv_season"))),
            ("tv_filetype", ('', torrent_raw_info_dict["tv_filetype"])),
            ("type", ('', str(torrent_raw_info_dict["type"]))),
            ("small_descr", ('', small_descr)),
            ("url", ('', torrent_raw_info_dict["url"])),
            ("dburl", ('', torrent_raw_info_dict["dburl"])),
            ("nfo", ('', '')),  # 实际上并不是这样的，但是nfo一般没有，故这么写
            ("descr", ('', self.extend_descr(torrent=torrent, info_dict=torrent_raw_info_dict, encode="html"))),
            ("uplver", ('', self.uplver)),
        )

    def data_anime_raw2tuple(self, torrent, torrent_info_search, torrent_raw_info_dict) -> tuple:
        torrent_file_name = re.search("torrents/(.+?\.torrent)", torrent.torrentFile).group(1)

        return (  # Submit form
            ("type", ('', str(torrent_raw_info_dict["type"]))),
            ("second_type", ('', str(torrent_raw_info_dict["second_type"]))),
            ("file", (torrent_file_name, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
            ("comic_type", ('', str(torrent_raw_info_dict["comic_type"]))),
            ("subteam", ('', torrent_raw_info_dict["subteam"])),
            ("comic_cname", ('', torrent_info_search.group("comic_cname"))),
            ("comic_ename", ('', torrent_info_search.group("comic_ename"))),
            ("comic_episode", ('', torrent_raw_info_dict["comic_episode"])),
            ("comic_quality", ('', torrent_raw_info_dict["comic_quality"])),
            ("comic_source", ('', torrent_raw_info_dict["comic_source"])),
            ("comic_filetype", ('', torrent_raw_info_dict["comic_filetype"])),
            ("comic_year", ('', torrent_raw_info_dict["comic_year"])),
            ("comic_country", ('', torrent_raw_info_dict["comic_country"])),
            ("type", ('', str(torrent_raw_info_dict["type"]))),
            ("small_descr", ('', torrent_raw_info_dict["small_descr"])),
            ("url", ('', torrent_raw_info_dict["url"])),
            ("dburl", ('', torrent_raw_info_dict["dburl"])),
            ("nfo", ('', '')),
            ("descr", ('', self.extend_descr(torrent=torrent, info_dict=torrent_raw_info_dict, encode="html"))),
            ("uplver", ('', self.uplver)),
        )

    def shunt_reseed(self, tr_client, db_client, torrent, torrent_info_search, torrent_type, flag=-1):
        search_key = pattern = table = column = ""
        if torrent_type == "series":
            search_key = torrent_info_search.group("search_name")
            pattern = torrent_info_search.group("full_name")
            table = "info_series"
            column = "tv_ename"
        elif torrent_type == "anime":
            search_name = re.sub(r"_", " ", torrent_info_search.group("search_name"))
            search_key = "{gp} {ename}".format(gp=torrent_info_search.group("group"), ename=search_name)
            pattern = "{search_key} {epo}".format(search_key=search_key, epo=torrent_info_search.group("anime_episode"))
            table = "info_anime"
            column = "comic_ename"

        search_tag = self.exist_judge(pattern, torrent_info_search.group(0))
        if search_tag == 0:  # 种子不存在，则准备发布
            torrent_raw_info_dict = {}
            if self.clone_mode == "clone":
                torrent_raw_info_dict = self.clone_from(search_key=search_key)
            if self.clone_mode == "database" or torrent_raw_info_dict == {}:
                # When clone mode return empty dict, use database.
                torrent_raw_info_dict = db_client.data_raw_info(torrent_info_search, table=table, column=column)

            if torrent_raw_info_dict:
                logging.info("Begin post The torrent {0},which name: {1}".format(torrent.id, torrent.name))
                multipart_data = ()
                if torrent_type == "series":
                    multipart_data = self.data_series_raw2tuple(torrent, torrent_info_search, torrent_raw_info_dict)
                elif torrent_type == "anime":
                    multipart_data = self.data_anime_raw2tuple(torrent, torrent_info_search, torrent_raw_info_dict)

                flag = self.torrent_upload(tr_client=tr_client, multipart_data=multipart_data)
            else:
                logging.error("Something,may wrong,Please the torrent raw dict.")
        elif search_tag == -1:  # 如果种子存在，但种子不一致
            logging.warning("Find dupe,and the exist torrent is not same as pre-reseed torrent.Stop Posting~")
        else:  # 如果种子存在（已经有人发布）  -> 辅种
            flag = self.torrent_download(tr_client=tr_client, tid=search_tag, thanks=False)
            logging.warning("Find dupe torrent,which id: {0},Automatically assist it~".format(search_tag))

        self.db_reseed_update(download_id=torrent.id, reseed_id=flag, db_client=db_client)
