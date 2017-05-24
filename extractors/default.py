# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import logging
import requests
from utils.cookie import cookies_raw2jar

from bs4 import BeautifulSoup
from utils.loadsetting import tc, descr

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)


class Base(object):
    url_host = "http://www.pt_domain.com"  # No '/' at the end.
    db_column = "tracker.pt_domain.com"  # The column in table,should be as same as the first tracker's host
    encode = "bbcode"  # bbcode or html
    status = False
    cookies = None

    def model_name(self):
        return type(self).__name__

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
        try:
            self.auto_thank = site_setting["auto_thank"]
            if not site_setting["anonymous_release"]:
                self.uplver = "no"
        except KeyError:
            pass

        if self.status:
            self.login()

    # -*- Login info site,and check login's info. -*-
    def login(self):
        login_dict = self.site_setting["login"]
        try:
            account_dict = login_dict["account"]
            for pair, key in account_dict.items():
                if key in [None, ""]:
                    raise KeyError("One more account key(maybe username or password) is not filled in.")
            post_data = self.login_data(account_dict)
            r = self.post_data(url="{host}/takelogin.php".format(host=self.url_host), data=post_data)
            self.cookies = r.cookies
        except KeyError as err:
            logging.error("Account login error: \"{err}\".Use cookies install.".format(err=err.args))
            self.cookies = cookies_raw2jar(login_dict["cookies"])
        finally:
            self.session_check()

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
            outer_bs = BeautifulSoup(post.text, "lxml").find("td", id="outer")
            if outer_bs.find_all("table"):  # Remove unnecessary table info(include SMS,Report)
                for table in outer_bs.find_all("table"):
                    table.extract()
            outer_message = outer_bs.get_text().replace("\n", "")
            flag = -1
            logging.error("Upload this torrent Error,The Server echo:\"{0}\",Stop Posting".format(outer_message))
        return flag

    def torrent_thank(self, tid):
        self.post_data(url="{host}/thanks.php".format(host=self.url_host), data={"id": str(tid)})

    # -*- Get page detail.php, torrent_info.php, torrents.php -*-
    def page_torrent_detail(self, tid, bs=False):
        return self.get_page(url="{host}/details.php".format(host=self.url_host), params={"id": tid, "hit": 1}, bs=bs)

    def page_torrent_info(self, tid, bs=False):
        return self.get_page(url="{host}/torrent_info.php".format(host=self.url_host), params={"id": tid}, bs=bs)

    def page_search(self, payload: dict, bs=False):
        return self.get_page(url="{host}/torrents.php".format(host=self.url_host), params=payload, bs=bs)

    def search_first_torrent_id(self, key, tid=0) -> int:
        bs = self.page_search(payload={"search": key}, bs=True)
        first_torrent_tag = bs.find("a", href=re.compile("download.php"))
        if first_torrent_tag:  # If exist
            href = first_torrent_tag["href"]
            tid = re.search("id=(\d+)", href).group(1)  # 找出种子id
        return tid

    def extend_descr(self, torrent, info_dict) -> str:
        return descr.out(raw=info_dict["descr"], torrent=torrent, encode=self.encode, clone_id=info_dict["clone_id"])

    def exist_judge(self, search_title, torrent_file_name) -> int:
        """
        If exist in this site ,return the exist torrent's id,else return 0.
        (Warning:if the exist torrent is not same as the pre-reseed torrent ,will return -1)
        """
        tag = self.search_first_torrent_id(key=search_title)
        if tag is not 0:
            torrent_file_page = self.page_torrent_info(tid=tag, bs=True)
            torrent_file_info_table = torrent_file_page.find("div", align="center").find("table")
            torrent_title = re.search("\\[name\] \(\d+\): (?P<name>.+?) -", torrent_file_info_table.text).group("name")
            if torrent_file_name != torrent_title:  # Use pre-reseed torrent's name match the exist torrent's name
                tag = -1
        return tag

    # -*- The feeding function -*-
    def torrent_feed(self, torrent, name_pattern, clone_db_dict, flag=-1):
        logging.info("Autoseed-{mo} Get A feed torrent: {na}".format(mo=self.model_name(), na=torrent.name))
        key_raw = clone_db_dict["search_name"]
        key_with_ep = "{search_key} {epo} {gr}".format(search_key=key_raw, epo=name_pattern.group("episode"),
                                                       gr=name_pattern.group("group"))

        search_tag = self.exist_judge(key_with_ep, torrent.name)
        # TODO The repack (or v2) will not be reseeded.
        if search_tag == 0:  # Non-existent repetition torrent, prepare to reseed
            try:
                clone_id = clone_db_dict[self.db_column]
                if clone_id in [None, 0, "0"]:
                    raise KeyError("The db-record is not return the clone id.")
            except KeyError:
                logging.warning("Not Find clone id from db of this torrent,May got incorrect info when clone.")
                clone_id = self.search_first_torrent_id(key=key_raw)
            else:
                logging.debug("Get clone id({id}) from db OK,USE key: \"{key}\"".format(id=clone_id, key=key_raw))

            if clone_id not in [-1, "-1"]:  # (This search name) Set to no re-seed for this site in database.
                torrent_raw_info_dict = self.torrent_clone(clone_id)
                if torrent_raw_info_dict:
                    logging.info("Begin post The torrent {0},which name: {1}".format(torrent.id, torrent.name))
                    multipart_data = self.data_raw2tuple(torrent, name_pattern, raw_info=torrent_raw_info_dict)
                    flag = self.torrent_upload(data=multipart_data)
                else:
                    logging.error("Something may wrong,Please check torrent raw dict.Some info may help you:"
                                  "search_key: {key}, pattern: {pat}, search_tag: {tag}, "
                                  "clone_id: {cid} ".format(key=key_raw, pat=key_with_ep, tag=search_tag, cid=clone_id))
        elif search_tag == -1:  # 如果种子存在，但种子不一致
            logging.warning("Find dupe,and the exist torrent is not same as pre-reseed torrent.Stop Posting~")
        else:  # 如果种子存在（已经有人发布）  -> 辅种
            flag = self.torrent_download(tid=search_tag, thanks=False)
            logging.warning("Find dupe torrent,which id: {0},Automatically assist it~".format(search_tag))

        return flag

    # -*- At least Overridden function,Please overridden below when add a new site -*-
    def login_data(self, account_dict):  # If you want to login by account but not cookies
        raise KeyError("Unsupported method.")

    def torrent_clone(self, tid) -> dict:
        pass

    def data_raw2tuple(self, torrent, torrent_name_search, raw_info: dict):
        return ()
