# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import logging
import requests
from utils.cookie import cookies_raw2jar
from utils.extend_descr import ExtendDescr
from bs4 import BeautifulSoup

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)


class NexusPHP(object):
    url_torrent_download = "http://www.pt_domain.com/download.php?id={tid}&passkey={pk}"
    url_torrent_upload = "http://www.pt_domain.com/takeupload.php"
    url_torrent_detail = "http://www.pt_domain.com/details.php?id={tid}&hit=1"
    url_torrent_file = "https://www.pt_domain.com/torrent_info.php?id={tid}"
    url_thank = "http://www.pt_domain.com/thanks.php"
    url_search = "http://www.pt_domain.com/torrents.php?search={k}&search_mode={md}"
    url_torrent_list = "http://www.pt_domain.com/torrents.php"

    uplver = "yes"
    status = False
    auto_thank = True

    db_column = "pt_domain.com"  # The column in table

    def __init__(self, setting: set, site_setting: dict, tr_client, db_client):
        self._setting = setting
        self.cookies = cookies_raw2jar(site_setting["cookies"])
        self.passkey = site_setting["passkey"]
        try:
            self.status = site_setting["status"]
            self.auto_thank = site_setting["auto_thank"]
            if not site_setting["anonymous_release"]:
                self.uplver = "no"
        except KeyError:
            pass

        self.tc = tr_client
        self.db = db_client
        self.descr = ExtendDescr(setting=self._setting)

        if self.status:
            self.session_check()

    def model_name(self):
        return type(self).__name__

    def session_check(self):
        list_bs = self.get_page(url=self.url_torrent_list, bs=True)
        up_name_tag = list_bs.find("a", href=re.compile("userdetails.php"))
        if up_name_tag:
            logging.debug("Model \"{mo}\" is activation now.You are assign as \"{up}\" in this site."
                          "Anonymous release:{ar},auto_thank: {at}".format(mo=self.model_name(), up=up_name_tag.string,
                                                                           ar=self.uplver, at=self.auto_thank))
        else:
            self.status = False
            logging.error("You may enter a wrong cookies-pair in setting,"
                          "If you want to use \"{mo}\",please exit and Check".format(mo=self.model_name()))

    def get_page(self, url, bs=False):
        page = requests.get(url=url, cookies=self.cookies)
        return_info = page.text
        if bs:
            return_info = BeautifulSoup(return_info, "lxml")
        return return_info

    def torrent_download(self, tid, thanks=auto_thank):
        added_torrent = self.tc.add_torrent(torrent=self.url_torrent_download.format(tid=tid, pk=self.passkey))
        logging.info("Download Torrent OK,which id: {id}.".format(id=tid))
        if thanks:
            self.torrent_thank(tid)
        return added_torrent.id

    def torrent_upload(self, data: tuple):
        post = requests.post(url=self.url_torrent_upload, cookies=self.cookies, files=data)
        if post.url != self.url_torrent_upload:  # 发布成功检查
            seed_torrent_download_id = re.search("id=(\d+)", post.url).group(1)  # 获取种子编号
            flag = self.torrent_download(tid=seed_torrent_download_id)
            logging.info("Reseed post OK,The torrent's in transmission: {fl}".format(fl=flag))
        else:  # 未发布成功打log
            outer_bs = BeautifulSoup(post.text, "lxml").find("td", id="outer")
            if outer_bs.find_all("table"):  # Remove unnecessary table info(include SMS,Report)
                for table in outer_bs.find_all("table"):
                    table.extract()
            outer_message = outer_bs.get_text().replace("\n", "")
            flag = -1
            logging.error("Upload this torrent Error,The Server echo:\"{0}\",Stop Posting".format(outer_message))
        return flag

    def torrent_thank(self, tid):
        requests.post(url=self.url_thank, cookies=self.cookies, data={"id": str(tid)})  # 自动感谢

    def torrent_detail(self, tid, bs=False):
        return self.get_page(url=self.url_torrent_detail.format(tid=tid), bs=bs)

    def page_search_text(self, search_key: str, search_mode: int):
        return self.get_page(url=self.url_search.format(k=search_key, md=search_mode))

    def get_last_torrent_id(self, search_key, search_mode: int = 0, tid=0) -> int:
        bs = BeautifulSoup(self.page_search_text(search_key=search_key, search_mode=search_mode), "lxml")
        if bs.find_all("a", href=re.compile("download.php")):  # If exist
            href = bs.find_all("a", href=re.compile("download.php"))[0]["href"]
            tid = re.search("id=(\d+)", href).group(1)  # 找出种子id
        return tid

    def extend_descr(self, torrent, info_dict, encode) -> str:
        return self.descr.out(raw=info_dict["descr"], torrent=torrent, encode=encode,
                              before_torrent_id=info_dict["before_torrent_id"])

    def exist_judge(self, search_title, torrent_file_name) -> int:
        """
        
        如果种子在byr存在，返回种子id，不存在返回0，已存在且种子一致返回种子号，不一致返回-1"""
        tag = self.get_last_torrent_id(search_key=search_title)
        if tag is not 0:
            torrent_file_page = self.get_page(url=self.url_torrent_file.format(tid=tag), bs=True)
            torrent_file_info_table = torrent_file_page.find("div", align="center").find("table")
            torrent_title = re.search("\\[name\] \(\d+\): (?P<name>.+?) -", torrent_file_info_table.text).group("name")
            if torrent_file_name != torrent_title:  # Use pre-reseed torrent's name match the exist torrent's name
                tag = -1
        return tag

    def feed(self, torrent, torrent_info_search, flag=-1):
        search_key = re.sub(r"[_\-.]", " ", torrent_info_search.group("search_name"))
        pattern = "{search_key} {epo}".format(search_key=search_key, epo=torrent_info_search.group("episode"))

        search_tag = self.exist_judge(pattern, torrent_info_search.group(0))
        if search_tag == 0:  # 种子不存在，则准备发布
            clone_id = self.db.get_data_clone_id(key=search_key, site=self.db_column)
            if clone_id is None:
                logging.warning("Not Find clone id from db of this torrent,May got incorrect info when clone.")
                clone_id = self.get_last_torrent_id(search_key=search_key, search_mode=0)
            else:
                logging.debug("Get clone id({id}) from db OK,USE key: \"{key}\"".format(id=clone_id, key=search_key))

            torrent_raw_info_dict = self.torrent_clone(clone_id)
            if torrent_raw_info_dict:
                logging.info("Begin post The torrent {0},which name: {1}".format(torrent.id, torrent.name))
                multipart_data = self.data_raw2tuple(torrent, torrent_info_search, torrent_raw_info_dict)
                flag = self.torrent_upload(data=multipart_data)
            else:
                logging.error("Something may wrong,Please check torrent raw dict.Some info may help you:"
                              "search_key: {key}, pattern: {pat}, search_tag: {tag}, "
                              "clone_id: {cid} ".format(key=search_key, pat=pattern, tag=search_tag, cid=clone_id))
        elif search_tag == -1:  # 如果种子存在，但种子不一致
            logging.warning("Find dupe,and the exist torrent is not same as pre-reseed torrent.Stop Posting~")
        else:  # 如果种子存在（已经有人发布）  -> 辅种
            flag = self.torrent_download(tid=search_tag, thanks=False)
            logging.warning("Find dupe torrent,which id: {0},Automatically assist it~".format(search_tag))

        self.db.reseed_update(did=torrent.id, rid=flag, site=self.db_column)
        return flag

    def torrent_clone(self, tid) -> dict:
        """At least Overridden it please"""
        pass

    def data_raw2tuple(self, torrent, torrent_name_search, raw_info: dict):
        """At least Overridden it please"""
        return ()
