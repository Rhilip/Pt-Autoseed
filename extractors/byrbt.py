# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import logging
import requests
from utils.cookie import cookies_raw2jar
from bs4 import BeautifulSoup

tracker_pattern = "tracker.byr.cn"

type_dict = {
    "电影": {"cat": 408,
           "sec_type": {"华语": 11, "欧洲": 12, "北美": 13, "亚洲": 14, "其他": 1},
           "split": ["movie_cname", "ename0day", "movie_type", "movie_country"]
           },
    "剧集": {"cat": 401,
           "sec_type": {"大陆": 15, "日韩": 16, "欧美": 17, "港台": 18, "其他": 2},
           "split": ["tv_type", "cname", "tv_ename", "tv_season", "tv_filetype"]
           },
    "动漫": {"cat": 404,
           "sec_type": {"动画": 19, "漫画": 20, "音乐": 21, "周边": 22, "其他": 3},
           "split": ["comic_type", "subteam", "comic_cname", "comic_ename", "comic_episode",
                     "comic_quality", "comic_source", "comic_filetype", "comic_year", "comic_country"]
           },
    "综艺": {"cat": 405,
           "sec_type": {"大陆": 27, "日韩": 28, "港台": 29, "欧美": 30, "其他": 5},
           "split": ["show_year", "show_country", "show_cname", "show_ename", "show_language", "hassub", "addition"]
           },
}


class Byrbt:
    def __init__(self, setting):
        self.passkey = setting.byr_passkey
        self.cookies = cookies_raw2jar(setting.byr_cookies)

        self.clone_mode = setting.byr_clone_mode

        self.uplver = "no"
        if setting.byr_anonymous_release:
            self.uplver = "yes"

    def download_torrent(self, tr_client, tid, thanks=True):
        """
        直接使用transmissionrpc.Client.add_torrent方法向tr添加url直链种子
        https://pythonhosted.org/transmissionrpc/reference/transmissionrpc.html#transmissionrpc.Client.add_torrent
        """
        download_torrent_link = "http://bt.byr.cn/download.php?id={tid}&passkey={pk}".format(tid=tid, pk=self.passkey)
        added_torrent = tr_client.add_torrent(torrent=download_torrent_link)
        logging.info("Download Torrent which id = {id} OK!".format(id=tid))
        if thanks:
            requests.post(url="http://bt.byr.cn/thanks.php", cookies=self.cookies, data={"id": str(tid)})  # 自动感谢
        return added_torrent.id

    def post_torrent(self, tr_client, multipart_data: tuple):
        """使用已经构造好的表单发布种子"""
        post = requests.post(url="http://bt.byr.cn/takeupload.php", cookies=self.cookies, files=multipart_data)
        if post.url != "http://bt.byr.cn/takeupload.php":  # 发布成功检查
            seed_torrent_download_id = re.search("id=(\d+)", post.url).group(1)  # 获取种子编号
            flag = self.download_torrent(tr_client=tr_client, tid=seed_torrent_download_id)
            logging.info("Post OK,The id in Byrbt: {id},in tr: {fl}".format(id=seed_torrent_download_id, fl=flag))
        else:  # 未发布成功打log
            outer_bs = BeautifulSoup(post.text, "lxml").find("td", id="outer")
            if outer_bs.find_all("table"):  # 移除不必要的table信息
                for table in outer_bs.find_all("table"):
                    table.extract()
            outer_message = outer_bs.get_text().replace("\n", "")
            flag = -1
            logging.error("Upload this torrent Error,The Server echo:\"{0}\",Stop Posting".format(outer_message))
        return flag

    def exist_judge(self, search_title, torrent_file_name):
        """如果种子在byr存在，返回种子id，不存在返回0，已存在且种子一致返回种子号，不一致返回-1"""
        search_url = "http://bt.byr.cn/torrents.php?search={key}&search_mode=2".format(key=search_title)
        exits_judge_raw = requests.get(url=search_url, cookies=self.cookies)
        bs = BeautifulSoup(exits_judge_raw.text, "lxml")
        tag = 0
        if bs.find_all("a", href=re.compile("download.php")):  # 如果存在（还有人比Autoseed快。。。
            href = bs.find_all("a", href=re.compile("download.php"))[0]["href"]
            tag_temp = re.search("id=(\d+)", href).group(1)  # 找出种子id
            # 使用待发布种子全名匹配已有种子的名称
            details_page = requests.get("http://bt.byr.cn/details.php?id={0}&hit=1".format(tag_temp),
                                        cookies=self.cookies)
            details_bs = BeautifulSoup(details_page.text, "lxml")
            torrent_title_in_site = details_bs.find("a", class_="index", href=re.compile(r"^download.php")).string
            torrent_title = re.search(r"\[BYRBT\]\.(.+?)\.torrent", torrent_title_in_site).group(1)
            if torrent_file_name == torrent_title:  # 如果匹配，返回种子号
                tag = tag_temp
            else:  # 如果不匹配，返回-1
                tag = -1
        return tag

    @staticmethod
    def sort_title_info(raw_title, raw_type, raw_sec_type) -> dict:
        split = type_dict[raw_type]["split"]
        raw_title_group = re.findall(r"\[[^\]]*\]", raw_title)

        return_dict = {
            "type": type_dict[raw_type]["cat"],
            "sec_type": type_dict[raw_type]["sec_type"][raw_sec_type],
        }

        if len(type_dict[raw_type]["split"]) == len(raw_title_group):
            logging.debug("the title split success.")
        else:
            # TODO 被clone种子标题信息不完整（缺tag）时准确导入
            logging.warning("the title split ERROR,the origin torrent may have wrong title")

        for (i, j) in zip(split, raw_title_group):
            title_split = re.sub("\[(?P<in>.+)\]", "\g<in>", j)
            return_dict.update({i: title_split})

        return return_dict

    def clone_get(self, search_key):
        """Reconstruction from BYRBT Info Clone by Deparsoul version 20170400,thx
        This function will automatically search the clone torrent,no database need !!!
        But some may wrong,Due to inappropriate search_title
        and will return a dict include (title,small_title,imdb_url,db_url,descr,before_torrent_id) from it.
        the next function will sort title to post_data due to clone_torrent's category
        """
        search_url = "http://bt.byr.cn/torrents.php?search={key}&search_mode=2".format(key=search_key)
        search_page = requests.get(url=search_url, cookies=self.cookies)
        search_bs = BeautifulSoup(search_page.text, "lxml")

        if search_bs.find_all("a", href=re.compile("download.php")):
            href = search_bs.find_all("a", href=re.compile("download.php"))[0]["href"]
            tag_temp = re.search("id=(\d+)", href).group(1)  # 找出种子id
            details_page = requests.get(cookies=self.cookies,
                                        url="http://bt.byr.cn/details.php?id={0}&hit=1".format(tag_temp))
            details_bs = BeautifulSoup(details_page.text, "lxml")

            title_search = re.search("种子详情 \"(?P<title>.*)\" - Powered", str(details_bs.title))
            if title_search:
                return_dict = {}
                return_dict.update(self.sort_title_info(raw_title=title_search.group("title"),
                                                        raw_type=details_bs.find("span", id="type").text,
                                                        raw_sec_type=details_bs.find("span", id="sec_type").text))

                body = details_bs.body

                imdb_url = ""
                if body.find(class_="imdbRatingPlugin"):
                    imdb_url = 'http://www.imdb.com/title/' + body.find(class_="imdbRatingPlugin")["data-title"]

                dburl = ""
                dburl_search = body.find("a", href=re.compile("://movie.douban.com/subject"))
                if dburl_search:
                    dburl = dburl_search.text

                descr = body.find(id="kdescr")

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
                    "uplver": self.uplver,
                    "before_torrent_id": tag_temp
                })

                return return_dict
            else:
                logging.error("Error,this torrent may not exist or ConnectError")
                return
