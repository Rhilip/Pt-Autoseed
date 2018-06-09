# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import re

import requests

from extractors.base.nexusphp import NexusPHP
from utils.constants import ubb_clean
from utils.load.handler import rootLogger as Logger

ask_dict = {
    "401": ["cname", "ename", "issuedate", "language", "format", "subsinfo", "district"],  # 电影
    "402": ["cname", "ename", "tvalias", "tvseasoninfo", "specificcat", "format", "subsinfo", "language"],  # 剧集
    "403": ["cname", "ename", "issuedate", "tvshowscontent", "tvshowsguest", "district", "subsinfo", "language",
            "format", "tvshowsremarks"],  # 综艺
    "404": ["cname", "ename", "issuedate", "version", "specificcat", "format"],  # 资料
    "405": ["cname", "ename", "issuedate", "animenum", "substeam", "specificcat", "format",
            "resolution", "district"],  # 动漫
    "407": ["issuedate", "cname", "ename", "language", "specificcat", "format", "resolution"],  # 体育
    "408": ["cname", "ename", "issuedate", "version", "specificcat", "format", "language"],  # 软件
    "409": ["cname", "ename", "company", "platform", "specificcat", "language", "format"],  # 游戏
    "411": ["cname", "ename", "specificcat", "format", "subsinfo", "language"],  # 纪录片
    "412": ["cname", "ename", "language", "subsinfo", "district"],  # 移动视频
    "410": ["specificcat", "cname", "format", "tvshowsremarks"],  # 其他
}


class TJUPT(NexusPHP):
    url_host = "https://tjupt.org"
    db_column = "pttracker6.tjupt.org"

    def __init__(self, status, cookies, passkey, **kwargs):
        # Site Features: Display In the browse page (Dead torrent will be set if not checked -> "0")
        self._TORRENT_VISIBLE = "1" if kwargs.setdefault("torrent_visible", True) else "0"

        super().__init__(status, cookies, passkey, **kwargs)

    def torrent_link(self, tid):
        torrent_link = self.url_host + "/download.php?id={tid}&passkey={pk}".format(tid=tid, pk=self.passkey)
        tmp_file = "/tmp/[TJUPT].{}.torrent".format(tid)
        with open(tmp_file, "wb") as torrent:
            r = requests.get(torrent_link)
            torrent.write(r.content)
        return tmp_file

    def exist_torrent_title(self, tag):
        torrent_file_page = self.page_torrent_info(tid=tag, bs=True)
        if re.search("你没有该权限！", torrent_file_page.text):
            torrent_page = self.page_torrent_detail(tid=tag, bs=True)
            torrent_title = re.search("\[TJUPT\]\.(?P<name>.+?)\.torrent", torrent_page.text).group("name")
        else:  # Due to HIGH Authority (Ultimate User) asked to view this page.
            torrent_file_info_table = torrent_file_page.find("ul", id="colapse")
            torrent_title = re.search("\\[name\] \(\d+\): (?P<name>.+?) -", torrent_file_info_table.text).group("name")
        Logger.info("The torrent name for id({id}) is \"{name}\"".format(id=tag, name=torrent_title))
        return torrent_title

    def torrent_clone(self, tid):
        """
        Use Internal API: - /upsimilartorrent.php?id={tid} ,Request Method: GET
                          - /catdetail_edittorrents.php?torid={id} ,Request Method: GET
        Will response two pages about this clone torrent's information,
        And this function will sort those pages to a pre-reseed dict.
        """
        res_dic = {}

        page_clone = self.get_data(url=self.url_host + "/upsimilartorrent.php", params={"id": tid}, bs=True)

        if not re.search(r"<h2>错误！</h2>", str(page_clone)):
            Logger.info("Got clone torrent's info,id: {tid}".format(tid=tid))

            type_select = page_clone.find("select", id="oricat")
            type_value = type_select.find("option", selected="selected")["value"]
            raw_descr = ubb_clean(page_clone.find("textarea", id="descr").text)
            url = page_clone.find("input", attrs={"name": "url"})
            res_dic.update({"clone_id": tid, "type": type_value, "descr": raw_descr, "url": url["value"]})

            for name in ["source_sel", "team_sel"]:
                tag = page_clone.find("select", attrs={"name": name})
                tag_selected = tag.find("option", selected=True)
                res_dic.update({name: tag_selected["value"]})

            # Get torrent_info page and sort this page's information into the pre-reseed dict.
            catdetail_page = self.get_data(url=self.url_host + "/catdetail_edittorrents.php", params={"torid": tid},
                                           bs=True)

            for ask_tag_name in ask_dict[type_value]:
                value = ""
                if catdetail_page.find("input", attrs={"name": ask_tag_name}):
                    tag = catdetail_page.find("input", attrs={"name": ask_tag_name})
                    value = tag["value"]
                elif catdetail_page.find("select", attrs={"name": ask_tag_name}):
                    tag = catdetail_page.find("select", attrs={"name": ask_tag_name})
                    tag_selected = tag.find("option", selected=True)
                    if tag_selected:
                        value = tag_selected["value"]
                res_dic.update({ask_tag_name: value})

        return res_dic

    def date_raw_update(self, torrent_name_search, raw_info: dict) -> dict:
        # TODO Change info due to reseed torrent's name information
        type_ = int(raw_info["type"])
        if type_ == 401:  # 电影
            pass
        elif type_ == 402:  # 剧集
            raw_info["ename"] = torrent_name_search.group("full_name")  # 英文名
            raw_info["tvseasoninfo"] = torrent_name_search.group("episode")  # 集数
            raw_info["subsinfo"] = 1  # 强制更新字幕情况为"暂无字幕"
        elif type_ == 405:  # 动漫
            raw_info["animenum"] = torrent_name_search.group("episode")  # 动漫集数

        return raw_info

    def data_raw2tuple(self, torrent, raw_info: dict):
        begin_post_list = [
            ("id", raw_info["clone_id"]),
            ("quote", raw_info["clone_id"]),
            ("type", raw_info["type"]),
        ]

        # Make category post list
        cat_post_list = [(cat, raw_info[cat]) for cat in ask_dict[raw_info["type"]]]

        end_post_list = [
            ("url", raw_info["url"]),  # IMDb链接
            ("nfo", ""),  # 实际上并不是这样的，但是nfo一般没有，故这么写
            ("color", 0),  # Tell me those three key's function~
            ("font", 0),
            ("size", 0),
            ("descr", self.enhance_descr(torrent=torrent, info_dict=raw_info)),  # 简介*
            ("getDescByTorrentId", ""),
            ("source_sel", raw_info["source_sel"]),  # 质量
            ("team_sel", raw_info["team_sel"]),  # 内容
            ("visible", self._TORRENT_VISIBLE),
            ("uplver", self._UPLVER),
        ]

        return tuple(begin_post_list + cat_post_list + end_post_list)
