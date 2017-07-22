# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import re

from extractors.nexusphp import NexusPHP

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

TORRENT_VISIBLE = "1"  # DEBUG Features: Display In the browse page (Dead torrent will be set if not checked -> "0")


class TJUPT(NexusPHP):
    url_host = "http://pt.tju.edu.cn"
    db_column = "pttracker6.tju.edu.cn"

    def exist_torrent_title(self, tag):
        torrent_file_page = self.page_torrent_info(tid=tag, bs=True)
        if re.search("你没有该权限！", torrent_file_page.text):
            torrent_page = self.page_torrent_detail(tid=tag, bs=True)
            torrent_title = re.search("\[TJUPT\]\.(?P<name>.+?)\.torrent", torrent_page.text).group("name")
        else:  # Due to HIGH Authority (Ultimate User) asked to view this page.
            # TODO not test....
            torrent_file_info_table = torrent_file_page.find("ul", id="colapse")
            torrent_title = re.search("\\[name\] \(\d+\): (?P<name>.+?) -", torrent_file_info_table.text).group("name")
        return torrent_title

    def torrent_clone(self, tid):
        """
        Use Internal API: - http://pt.tju.edu.cn/upsimilartorrent.php?id={tid} ,Request Method: GET
                          - http://pt.tju.edu.cn/catdetail_edittorrents.php?torid={id} ,Request Method: GET
        Will response two pages about this clone torrent's information,
        And this function will sort those pages to a pre-reseed dict.
        """
        res_dic = {}

        page_clone = self.get_data(url=self.url_host + "/upsimilartorrent.php", params={"id": tid}, bs=True)

        if not re.search(r"<h2>错误！</h2>", str(page_clone)):
            logging.info("Got clone torrent's info,id: {tid}".format(tid=tid))
            res_dic.update({"clone_id": tid})

            type_select = page_clone.find("select", id="oricat")
            type_value = type_select.find("option", selected="selected")["value"]

            raw_descr = page_clone.find("textarea", id="descr").text
            raw_descr = re.sub(r"\[(?P<bbcode>code|quote).+?\[/(?P=bbcode)\]", "", raw_descr, flags=re.S)
            raw_descr = re.sub(r"\u3000", " ", raw_descr)

            url = page_clone.find("input", attrs={"name": "url"})

            res_dic.update({"type": type_value, "descr": raw_descr, "url": url["value"]})

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
        if int(raw_info["type"]) == 401:  # 电影
            pass
        elif int(raw_info["type"]) == 402:  # 剧集
            raw_info["ename"] = torrent_name_search.group("full_name")  # 英文名
            raw_info["tvseasoninfo"] = torrent_name_search.group("episode")  # 集数
        elif int(raw_info["type"]) == 403:  # 综艺
            pass
        elif int(raw_info["type"]) == 404:  # 资料
            pass
        elif int(raw_info["type"]) == 405:  # 动漫
            raw_info["animenum"] = torrent_name_search.group("episode")  # 动漫集数
        elif int(raw_info["type"]) == 407:  # 体育
            pass
        elif int(raw_info["type"]) == 408:  # 软件
            pass
        elif int(raw_info["type"]) == 409:  # 游戏
            pass
        elif int(raw_info["type"]) == 410:  # 其他
            pass
        elif int(raw_info["type"]) == 411:  # 纪录片
            pass
        elif int(raw_info["type"]) == 412:  # 移动视频
            pass

        return raw_info

    def data_raw2tuple(self, torrent, raw_info: dict):
        torrent_file_name = re.search("torrents/(.+?\.torrent)", torrent.torrentFile).group(1)
        begin_post_list = [
            ("id", ('', str(raw_info["clone_id"]))),
            ("quote", ('', str(raw_info["clone_id"]))),
            ("file", (torrent_file_name, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
            ("type", ('', str(raw_info["type"]))),
        ]

        # Make category post list
        cat_post_list = [(cat, ('', str(raw_info[cat]))) for cat in ask_dict[raw_info["type"]]]

        end_post_list = [
            ("url", ('', str(raw_info["url"]))),  # IMDb链接
            ("nfo", ('', '')),  # 实际上并不是这样的，但是nfo一般没有，故这么写
            ("color", ('', '0')),  # Tell me those three key's function~
            ("font", ('', '0')),
            ("size", ('', '0')),
            ("descr", ('', self.extend_descr(torrent=torrent, info_dict=raw_info))),  # 简介*
            ("getDescByTorrentId", ('', "")),
            ("source_sel", ('', str(raw_info["source_sel"]))),  # 质量
            ("team_sel", ('', str(raw_info["team_sel"]))),  # 内容
            ("visible", ('', TORRENT_VISIBLE)),
            ("uplver", ('', self.uplver)),
        ]

        post_list = begin_post_list + cat_post_list + end_post_list

        return tuple(post_list)
