# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import logging
import re

from bs4 import BeautifulSoup

from extractors.base import Base
from utils.cookie import cookies_raw2jar
from utils.descr import out as descr_out
from utils.load.submodules import tc

rev_tag = re.compile("repack|proper|v2|rev")


class NexusPHP(Base):
    auto_thank = True
    uplver = "yes"

    DEFAULT_TORRENT_WHEN_CLONE = None  # Enhanced Features: When not find the clone torrent, use it as default clone_id

    def __init__(self, site_setting: dict):
        self.site_setting = site_setting  # Load setting from user

        # Assign the key information
        self.status = site_setting["status"]
        self.passkey = site_setting["passkey"]
        self.cookies = cookies_raw2jar(site_setting["cookies"])
        try:
            self.auto_thank = site_setting["auto_thank"]
            if not site_setting["anonymous_release"]:
                self.uplver = "no"
        except KeyError:
            pass

        if self.online_check():
            self.session_check()

    # -*- Check login's info -*-
    def session_check(self):  # TODO Reconstruction
        page_usercp_bs = self.get_data(url=self.url_host + "/usercp.php", bs=True)
        info_block = page_usercp_bs.find(id="info_block")
        if info_block:
            user_tag = info_block.find("a", href=re.compile("userdetails.php"), class_=re.compile("Name"))
            up_name = user_tag.get_text()
            logging.debug("Model \"{mo}\" is activation now.You are assign as \"{up}\" in this site."
                          "Anonymous release: {ar},auto_thank: {at}".format(mo=self.model_name(), up=up_name,
                                                                            ar=self.uplver, at=self.auto_thank))
        else:
            self.status = False  # When can not confirm identity,Forced Turn off the status
            logging.error("Can not verify identity.If you want to use \"{mo}\","
                          "please Check your Cookies".format(mo=self.model_name()))

    # -*- Torrent's download, upload and thank -*-
    def torrent_download(self, tid, thanks=auto_thank):
        download_url = self.url_host + "/download.php?id={tid}&passkey={pk}".format(tid=tid, pk=self.passkey)
        added_torrent = tc.add_torrent(torrent=download_url)
        # Another way is download torrent file to watch-dir(see early commits),But it will no return added_torrent.id
        logging.info("Download Torrent OK,which id: {id}.".format(id=tid))
        if thanks:  # Automatically thanks for additional Bones.
            self.torrent_thank(tid)
        return added_torrent.id

    def torrent_upload(self, data: tuple):
        upload_url = self.url_host + "/takeupload.php"
        post = self.post_data(url=upload_url, files=data)
        if post.url != upload_url:  # Check reseed status
            seed_torrent_download_id = re.search("id=(\d+)", post.url).group(1)  # Read the torrent's id in reseed site
            flag = self.torrent_download(tid=seed_torrent_download_id)
            logging.info("Reseed post OK,The torrent's in transmission: {fl}".format(fl=flag))
        else:  # Log if not reseed successfully
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
        self.post_data(url=self.url_host + "/thanks.php", data={"id": str(tid)})

    # -*- Get page detail.php, torrent_info.php, torrents.php -*-
    def page_torrent_detail(self, tid, bs=False):
        return self.get_data(url=self.url_host + "/details.php", params={"id": tid, "hit": 1}, bs=bs)

    def page_torrent_info(self, tid, bs=False):
        return self.get_data(url=self.url_host + "/torrent_info.php", params={"id": tid}, bs=bs)

    def page_search(self, payload: dict, bs=False):
        return self.get_data(url=self.url_host + "/torrents.php", params=payload, bs=bs)

    def search_list(self, key) -> list:
        bs = self.page_search(payload={"search": key}, bs=True)
        download_tag = bs.find_all("a", href=re.compile("download.php"))
        tid_list = [re.search("id=(\d+)", tag["href"]).group(1) for tag in download_tag]
        logging.debug("USE key: {key} to search,and the Return tid-list: {list}".format(key=key, list=tid_list))
        return tid_list

    def first_tid_in_search_list(self, key) -> int:
        tid_list = self.search_list(key=key)
        try:
            tid = int(tid_list[0])
        except IndexError:
            tid = 0
        return tid

    def extend_descr(self, torrent, info_dict) -> str:
        return descr_out(raw=info_dict["descr"], torrent=torrent, encode=self.encode, clone_id=info_dict["clone_id"])

    def exist_torrent_title(self, tag):
        torrent_file_page = self.page_torrent_info(tid=tag, bs=True)
        torrent_file_info_table = torrent_file_page.find("ul", id="colapse")
        torrent_title = re.search("\\[name\] \(\d+\): (?P<name>.+?) -", torrent_file_info_table.text).group("name")
        return torrent_title

    def exist_judge(self, search_title, torrent_file_name) -> int:
        """
        If exist in this site ,return the exist torrent's id,else return 0.
        (Warning:if the exist torrent is not same as the pre-reseed torrent ,will return -1)
        """
        tag = self.first_tid_in_search_list(key=search_title)
        if tag is not 0:
            torrent_title = self.exist_torrent_title(tag=tag)
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
        if search_tag == -1 and re.search(rev_tag, str(torrent.name).lower()):
            search_tag = 0  # For REPACK may let search_tag == -1 when use function exits_judge.

        flag = -1
        if search_tag == 0:  # Non-existent repetition torrent, prepare to reseed
            clone_id = 0
            try:
                clone_id = clone_db_dict[self.db_column]
                if clone_id in [None, 0, "0"]:
                    raise KeyError("The db-record is not return the clone id.")
                logging.debug("Get clone id({id}) from db OK,USE key: \"{key}\"".format(id=clone_id, key=key_raw))
            except KeyError:
                logging.warning("Not Find clone id from db of this torrent,May got incorrect info when clone.")
                for key in [key_with_gp, key_raw]:  # USE introduction of the same group First and Then Generic search
                    clone_id = self.first_tid_in_search_list(key=key)
                    if clone_id != 0:
                        break
                if clone_id == 0 and self.DEFAULT_TORRENT_WHEN_CLONE:  # USE Default clone id if set.
                    clone_id = self.DEFAULT_TORRENT_WHEN_CLONE

            err = True
            multipart_data = None
            if int(clone_id) not in [0, -1]:  # -1 -> (This search name) Set to no re-seed for this site in database.
                logging.info("The clone id for \"{title}\" is {cid}.".format(title=torrent.name, cid=clone_id))
                torrent_raw_info_dict = self.torrent_clone(clone_id)
                if torrent_raw_info_dict:
                    logging.info("Begin post The torrent {0},which name: {1}".format(torrent.id, torrent.name))
                    new_dict = self.date_raw_update(torrent_name_search=name_pattern, raw_info=torrent_raw_info_dict)
                    multipart_data = self.data_raw2tuple(torrent, raw_info=new_dict)
                    flag = self.torrent_upload(data=multipart_data)
                    if flag is not -1:
                        err = False
            if err:  # May clone_id in [0,-1] or upload error
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
        """
        Get the raw information about the clone torrent's depend on given id,
        and sort it into a dict which can be converted to the post tuple.
        
        :param tid: int, The clone torrent's id in this site
        :return: dict, The information dict about this clone torrent
        """
        pass

    def date_raw_update(self, torrent_name_search, raw_info: dict) -> dict:
        """
        Update the raw dict due to the pre-reseed torrent's info (main from `torrent_name_search`)
        
        :param torrent_name_search: class '_sre.SRE_Match'
        :param raw_info: dict, The information dict about the clone torrent
        :return: dict, The information dict about the pre-reseed torrent
        """
        pass

    def data_raw2tuple(self, torrent, raw_info: dict) -> tuple:
        """
        Sort the information dict to the post tuple.
        
        :param torrent: class transmissionrpc.Torrent
        :param raw_info: dict, The information dict about the pre-reseed torrent
        :return: tuple, The prepared tuple used to upload to the site
        """
        pass
