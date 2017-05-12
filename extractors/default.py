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
    url_host = "http://www.pt_domain.com"  # No '/' at the end.
    db_column = "tracker.pt_domain.com"  # The column in table,should be as same as the first tracker's host

    uplver = "yes"
    encode = "bbcode"  # bbcode or html
    status = False
    auto_thank = True

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
        url_usercp_page = self.get_page(url="{host}/usercp.php".format(host=self.url_host), bs=True)
        info_block = url_usercp_page.find(id="info_block")
        user_tag = info_block.find("a", href=re.compile("userdetails.php"), class_=re.compile("Name"))
        if user_tag:
            up_name = user_tag.get_text()
            logging.debug("Model \"{mo}\" is activation now.You are assign as \"{up}\" in this site."
                          "Anonymous release:{ar},auto_thank: {at}".format(mo=self.model_name(), up=up_name,
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
        download_url = "{host}/download.php?id={tid}&passkey={pk}".format(host=self.url_host, tid=tid, pk=self.passkey)
        added_torrent = self.tc.add_torrent(torrent=download_url)
        logging.info("Download Torrent OK,which id: {id}.".format(id=tid))
        if thanks:  # Automatically thanks for additional Bones.
            self.torrent_thank(tid)
        return added_torrent.id

    def torrent_upload(self, data: tuple):
        upload_url = "{host}/takeupload.php".format(host=self.url_host)
        post = requests.post(url=upload_url, cookies=self.cookies, files=data)
        if post.url != upload_url:  # 发布成功检查
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
        url_thank = "{host}/thanks.php".format(host=self.url_host)
        requests.post(url=url_thank, cookies=self.cookies, data={"id": str(tid)})

    def torrent_detail(self, tid, bs=False):
        return self.get_page(url="{host}/details.php?id={tid}&hit=1".format(host=self.url_host, tid=tid), bs=bs)

    def page_search_text(self, key: str, mode: int):
        url_search = "{host}/torrents.php?search={k}&search_mode={md}".format(host=self.url_host, k=key, md=mode)
        return self.get_page(url=url_search)

    def get_last_torrent_id(self, search_key, search_mode: int = 0, tid=0) -> int:
        bs = BeautifulSoup(self.page_search_text(key=search_key, mode=search_mode), "lxml")
        if bs.find_all("a", href=re.compile("download.php")):  # If exist
            href = bs.find_all("a", href=re.compile("download.php"))[0]["href"]
            tid = re.search("id=(\d+)", href).group(1)  # 找出种子id
        return tid

    def extend_descr(self, torrent, info_dict) -> str:
        return self.descr.out(raw=info_dict["descr"], torrent=torrent, encode=self.encode,
                              before_torrent_id=info_dict["before_torrent_id"])

    def exist_judge(self, search_title, torrent_file_name) -> int:
        """
        If exist in this site ,return the exist torrent's id,else return 0.
        (Warning:if the exist torrent is not same as the pre-reseed torrent ,will return -1)
        """
        tag = self.get_last_torrent_id(search_key=search_title)
        if tag is not 0:
            torrent_file_url = "{host}/torrent_info.php?id={tid}".format(host=self.url_host, tid=tag)
            torrent_file_page = self.get_page(url=torrent_file_url, bs=True)
            torrent_file_info_table = torrent_file_page.find("div", align="center").find("table")
            torrent_title = re.search("\\[name\] \(\d+\): (?P<name>.+?) -", torrent_file_info_table.text).group("name")
            if torrent_file_name != torrent_title:  # Use pre-reseed torrent's name match the exist torrent's name
                tag = -1
        return tag

    def feed(self, torrent, torrent_info_search, flag=-1):
        logging.info("Autoseed-{mo} Get A feed torrent: {na}".format(mo=self.model_name(), na=torrent.name))
        search_key = re.sub(r"[_\-.]", " ", torrent_info_search.group("search_name"))
        pattern = "{search_key} {epo} {gr}".format(search_key=search_key, epo=torrent_info_search.group("episode"),
                                                   gr=torrent_info_search.group("group"))

        search_tag = self.exist_judge(pattern, torrent.name)
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
        """At least Overridden it please,Below is a sample."""
        torrent_file_name = re.search("torrents/(.+?\.torrent)", torrent.torrentFile).group(1)
        post_tuple = (
            ("type", ('', str(raw_info["type"]))),
            ("second_type", ('', str(raw_info["second_type"]))),
            ("file", (torrent_file_name, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
            ("name", ('', str(raw_info["name"]))),
            ("small_descr", ('', raw_info["small_descr"])),
            ("url", ('', raw_info["url"])),
            ("dburl", ('', raw_info["dburl"])),
            ("nfo", ('', '')),  # 实际上并不是这样的，但是nfo一般没有，故这么写
            ("descr", ('', self.extend_descr(torrent=torrent, info_dict=raw_info))),
            ("uplver", ('', self.uplver)),
        )
        return post_tuple
