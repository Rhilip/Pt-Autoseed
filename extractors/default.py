# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import re

import requests
from bs4 import BeautifulSoup

from utils.cookie import cookies_raw2jar
from utils.extend_descr import out as descr_out
from utils.loadsetting import tc

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

REQUESTS_TIMEOUT = 5


class Base(object):
    url_host = "http://www.pt_domain.com"  # No '/' at the end.
    db_column = "tracker.pt_domain.com"  # The column in table,should be as same as the first tracker's host
    encode = "bbcode"  # bbcode or html
    status = False
    cookies = None

    online_check_count = 0

    def model_name(self):
        return type(self).__name__

    def online_check(self):
        online = True
        try:
            requests.get(url=self.url_host, stream=True, timeout=REQUESTS_TIMEOUT)
        except requests.exceptions.RequestException:
            online = False
            if self.online_check_count == 0:
                logging.warning("Site: {si} is offline now.".format(si=self.url_host))
            self.online_check_count += 1
        else:
            if self.online_check_count != 0:
                logging.info("The Site: {si} is Now online,"
                             "after {count} times tries.".format(si=self.url_host, count=self.online_check_count))
            self.online_check_count = 0
        return online

    # -*- Encapsulation requests's method,with format-out as bs or json when use get -*-
    def get_page(self, url, params=None, bs=False, json=False):
        page = requests.get(url=url, params=params, cookies=self.cookies)
        return_info = page.text
        if bs:
            return_info = BeautifulSoup(return_info, "lxml")
        elif json:
            return_info = page.json()
        return return_info

    def post_data(self, url, params=None, data=None, files=None):
        return requests.post(url=url, params=params, data=data, files=files, cookies=self.cookies)


class NexusPHP(Base):
    auto_thank = True
    uplver = "yes"

    def __init__(self, site_setting: dict):
        self.site_setting = site_setting
        self.status = site_setting["status"]
        self.passkey = site_setting["passkey"]
        self.cookies = cookies_raw2jar(site_setting["cookies"])
        try:
            self.auto_thank = site_setting["auto_thank"]
            if not site_setting["anonymous_release"]:
                self.uplver = "no"
        except KeyError:
            pass

        if self.status and self.online_check():
            self.session_check()

    # -*- Check login's info -*-
    def session_check(self):
        page_usercp_bs = self.get_page(url="{host}/usercp.php".format(host=self.url_host), bs=True)
        info_block = page_usercp_bs.find(id="info_block")
        if info_block:
            user_tag = info_block.find("a", href=re.compile("userdetails.php"), class_=re.compile("Name"))
            up_name = user_tag.get_text()
            logging.debug("Model \"{mo}\" is activation now.You are assign as \"{up}\" in this site."
                          "Anonymous release: {ar},auto_thank: {at}".format(mo=self.model_name(), up=up_name,
                                                                            ar=self.uplver, at=self.auto_thank))
        else:
            self.status = False
            logging.error("Can not verify identity.If you want to use \"{mo}\","
                          "please exit and Check".format(mo=self.model_name()))

    # -*- Torrent's download, upload and thank -*-
    def torrent_download(self, tid, thanks=auto_thank):
        download_url = "{host}/download.php?id={tid}&passkey={pk}".format(host=self.url_host, tid=tid, pk=self.passkey)
        added_torrent = tc.add_torrent(torrent=download_url)
        # Another way is download torrent file to watch-dir(see early commits),But it will no return added_torrent.id
        logging.info("Download Torrent OK,which id: {id}.".format(id=tid))
        if thanks:  # Automatically thanks for additional Bones.
            self.torrent_thank(tid)
        return added_torrent.id

    def torrent_upload(self, data: tuple):
        upload_url = "{host}/takeupload.php".format(host=self.url_host)
        post = self.post_data(url=upload_url, files=data)
        if post.url != upload_url:  # 发布成功检查
            seed_torrent_download_id = re.search("id=(\d+)", post.url).group(1)  # 获取种子编号
            flag = self.torrent_download(tid=seed_torrent_download_id)
            logging.info("Reseed post OK,The torrent's in transmission: {fl}".format(fl=flag))
            # TODO USE new torrent's id to Update `info_list` in db
        else:  # 未发布成功打log
            flag = -1
            outer_message = self.torrent_upload_err_message(post_text=post.text)
            logging.error("Upload this torrent Error,The Server echo:\"{0}\",Stop Posting".format(outer_message))
        return flag

    @staticmethod
    def torrent_upload_err_message(post_text) -> str:
        outer_bs = BeautifulSoup(post_text, "lxml")
        outer_tag = outer_bs.find("td", id="outer")
        if outer_tag.find_all("table"):  # Remove unnecessary table info(include SMS,Report)
            for table in outer_tag.find_all("table"):
                table.extract()
        outer_message = outer_tag.get_text().replace("\n", "")
        return outer_message

    def torrent_thank(self, tid):
        self.post_data(url="{host}/thanks.php".format(host=self.url_host), data={"id": str(tid)})

    # -*- Get page detail.php, torrent_info.php, torrents.php -*-
    def page_torrent_detail(self, tid, bs=False):
        return self.get_page(url="{host}/details.php".format(host=self.url_host), params={"id": tid, "hit": 1}, bs=bs)

    def page_torrent_info(self, tid, bs=False):
        return self.get_page(url="{host}/torrent_info.php".format(host=self.url_host), params={"id": tid}, bs=bs)

    def page_search(self, payload: dict, bs=False):
        return self.get_page(url="{host}/torrents.php".format(host=self.url_host), params=payload, bs=bs)

    def search_list(self, key) -> list:
        tid_list = []
        bs = self.page_search(payload={"search": key}, bs=True)
        download_tag = bs.find_all("a", href=re.compile("download.php"))
        for tag in download_tag:
            href = tag["href"]
            tid = re.search("id=(\d+)", href).group(1)  # 找出种子id
            tid_list.append(tid)
        return tid_list

    def first_tid_in_search_list(self, key) -> int:
        tid_list = self.search_list(key=key)
        logging.debug("USE key: {key} to search,and the Return tid-list: {list}".format(key=key, list=tid_list))
        try:
            tid = tid_list[0]
        except IndexError:
            tid = 0
        return tid

    def extend_descr(self, torrent, info_dict) -> str:
        return descr_out(raw=info_dict["descr"], torrent=torrent, encode=self.encode, clone_id=info_dict["clone_id"])

    def exist_judge(self, search_title, torrent_file_name) -> int:
        """
        If exist in this site ,return the exist torrent's id,else return 0.
        (Warning:if the exist torrent is not same as the pre-reseed torrent ,will return -1)
        """
        tag = self.first_tid_in_search_list(key=search_title)
        if tag is not 0:
            torrent_file_page = self.page_torrent_info(tid=tag, bs=True)
            torrent_file_info_table = torrent_file_page.find("ul", id="colapse")
            torrent_title = re.search("\\[name\] \(\d+\): (?P<name>.+?) -", torrent_file_info_table.text).group("name")
            if torrent_file_name != torrent_title:  # Use pre-reseed torrent's name match the exist torrent's name
                tag = -1
        return tag

    # -*- The feeding function -*-
    def torrent_feed(self, torrent, name_pattern, clone_db_dict):
        logging.info("Autoseed-{mo} Get A feed torrent: {na}".format(mo=self.model_name(), na=torrent.name))
        key_raw = clone_db_dict["search_name"]  # maximum 10 keywords (NexusPHP: torrents.php,line 696),so gp ep first
        key_with_gp = "{gr} {search_key}".format(search_key=key_raw, gr=name_pattern.group("group"))
        key_with_gp_ep = "{ep} {gp_key}".format(gp_key=key_with_gp, ep=name_pattern.group("episode"))

        search_tag = self.exist_judge(key_with_gp_ep, torrent.name)
        if search_tag == -1 and re.search("REPACK|PROPER|v2", torrent.name):
            search_tag = 0  # For REPACK will let search_tag == -1 when use function exits_judge.

        flag = -1
        if search_tag == 0:  # Non-existent repetition torrent, prepare to reseed
            try:
                clone_id = clone_db_dict[self.db_column]
                if clone_id in [None, 0, "0"]:
                    raise KeyError("The db-record is not return the clone id.")
                logging.debug("Get clone id({id}) from db OK,USE key: \"{key}\"".format(id=clone_id, key=key_raw))
            except KeyError:
                logging.warning("Not Find clone id from db of this torrent,May got incorrect info when clone.")
                clone_id = self.first_tid_in_search_list(key=key_with_gp)  # USE introduction of the same group First
                if clone_id == 0:  # Generic search
                    clone_id = self.first_tid_in_search_list(key=key_raw)

            err = True
            multipart_data = None
            if int(clone_id) not in [0, -1]:  # -1 -> (This search name) Set to no re-seed for this site in database.
                logging.info("The clone id for \"{title}\" is {cid}.".format(title=torrent.name, cid=clone_id))
                torrent_raw_info_dict = self.torrent_clone(clone_id)
                if torrent_raw_info_dict:
                    logging.info("Begin post The torrent {0},which name: {1}".format(torrent.id, torrent.name))
                    multipart_data = self.data_raw2tuple(torrent, name_pattern, raw_info=torrent_raw_info_dict)
                    flag = self.torrent_upload(data=multipart_data)
                    if flag is not -1:
                        err = False
            if err:
                logging.error("The torrent reseed ERROR. With: search_key: {pat}, dupe_tag: {tag}, clone_id: {cid}, "
                              "data: {da}".format(pat=key_with_gp_ep, tag=search_tag, cid=clone_id, da=multipart_data))
        elif search_tag == -1:  # 如果种子存在，但种子不一致
            logging.warning("Find dupe,and the exist torrent is not same as pre-reseed torrent.Stop Posting~")
        else:  # 如果种子存在（已经有人发布）  -> 辅种
            flag = self.torrent_download(tid=search_tag, thanks=False)
            logging.warning("Find dupe torrent,which id: {0},Automatically assist it~".format(search_tag))

        return flag

    # -*- At least Overridden function,Please overridden below when add a new site -*-
    def torrent_clone(self, tid) -> dict:
        pass

    def data_raw2tuple(self, torrent, torrent_name_search, raw_info: dict):
        return ()
