# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import logging
import re

from bs4 import BeautifulSoup

from extractors.base.site import Site
from utils.err import *
from utils.load.submodules import tc, db


class NexusPHP(Site):
    _pat_search_torrent_id = re.compile("download.php\?id=(\d+)")

    def __init__(self, status, cookies, passkey, **kwargs):
        super().__init__(status, cookies, **kwargs)

        # -*- Assign the based information -*-
        self.passkey = passkey

        # -*- Assign Enhanced Features -*-
        """
        Enhance Feature for `NexusPHP` Reseeder.
        Those key-values will be set as default value unless you change it in your user-settings.
        The name of those key should be start with "_" and upper.
        
        Included:
        1. _UPLVER                : default "no",  Enable to Release anonymously.
        2. _AUTO_THANK            : default True,  Enable to Automatically thanks for additional Bones.
        3. _DEFAULT_CLONE_TORRENT : default None,  When not find the clone torrent, use it as default clone_id
        4. _FORCE_JUDGE_DUPE_LOC  : default False, Judge torrent is dupe or not in location before post it to PT-site.
        5. _GET_CLONE_ID_FROM_DB  : default True,  Enable to get clone torrent's id from database first, then search.

        """
        self._UPLVER = "yes" if kwargs.setdefault("anonymous_release", True) else "no"
        self._AUTO_THANK = kwargs.setdefault("auto_thank", True)
        self._DEFAULT_CLONE_TORRENT = kwargs.setdefault("default_clone_torrent", None)
        self._FORCE_JUDGE_DUPE_LOC = kwargs.setdefault("force_judge_dupe_loc", False)
        self._GET_CLONE_ID_FROM_DB = kwargs.setdefault("get_clone_id_from_db", True)

    # -*- Check login's info -*-
    def session_check(self):
        page_usercp_bs = self.get_data(url=self.url_host + "/usercp.php", bs=True)
        self.status = True if page_usercp_bs.find(id="info_block") else False
        if self.status:
            logging.debug("Through authentication in Site: {}".format(self.model_name()))
        else:
            logging.error("Can not verify identity. Please Check your Cookies".format(mo=self.model_name()))
        return self.status

    # -*- Torrent's download, upload and thank -*-
    def torrent_download(self, tid, **kwargs):
        download_url = self.url_host + "/download.php?id={tid}&passkey={pk}".format(tid=tid, pk=self.passkey)
        added_torrent = tc.add_torrent(torrent=download_url)
        # Another way is download torrent file to watch-dir(see early commits),But it will no return added_torrent.id
        logging.info("Download Torrent OK,which id: {id}.".format(id=tid))
        if kwargs.setdefault("thanks", self._AUTO_THANK):
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
            outer_message = self.torrent_upload_err_message(post_text=post.text)
            raise ConnectionError("Upload this torrent Error, The Server echo:\"{0}\".".format(outer_message))
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

    def page_search(self, key: str, bs=False):
        return self.get_data(url=self.url_host + "/torrents.php", params={"search": key}, bs=bs)

    def search_list(self, key) -> list:
        bs = self.page_search(key=key, bs=True)
        download_tag = bs.find_all("a", href=self._pat_search_torrent_id)
        tid_list = [int(re.search(self._pat_search_torrent_id, tag["href"]).group(1)) for tag in download_tag]
        logging.debug("USE key: {key} to search,and the Return tid-list: {list}".format(key=key, list=tid_list))
        return tid_list

    def first_tid_in_search_list(self, key, _max=False) -> int:
        tid_list = self.search_list(key=key) + [0]
        return max(tid_list) if _max else tid_list[0]

    def exist_torrent_title(self, tag):
        torrent_file_page = self.page_torrent_info(tid=tag, bs=True)
        torrent_file_info_table = torrent_file_page.find("ul", id="colapse")
        torrent_title = re.search("\\[name\] \(\d+\): (?P<name>.+?) -", torrent_file_info_table.text).group("name")
        logging.info("The torrent name for id({id}) is \"{name}\"".format(id=tag, name=torrent_title))
        return torrent_title

    def exist_judge(self, search_title: str, torrent_file_name: str) -> int:
        """
        If exist in this site, return the exist torrent's id, else return 0.
        Warning: if the exist torrent is not same as the pre-reseed torrent, will return -1
        """
        tag = 0
        for test_id in sorted(self.search_list(key=search_title), reverse=True)[:8]:  # Travel All Search list
            test_title = self.exist_torrent_title(tag=test_id)
            if torrent_file_name == test_title:  # Try to get current dupe torrent's id
                tag = test_id
                break
            elif self._FORCE_JUDGE_DUPE_LOC:
                tag = -1

        # Some statue that should reseed when turn on FORCE_JUDGE_DUPE_LOC, Or let server to judge.
        if tag == -1:
            # TODO 对 v2|pack 等情况做适配(, 在开启本地自判断的情况下)
            pass

        return tag

    def torrent_reseed(self, torrent):
        name_pattern = self._get_torrent_ptn(torrent)
        if name_pattern:
            key_raw = re.sub(r"[_\-.']", " ", name_pattern.group("search_name"))
            key_with_gp = "{gr} {search_key}".format(search_key=key_raw, gr=name_pattern.group("group"))
            key_with_gp_ep = "{ep} {gp_key}".format(gp_key=key_with_gp, ep=name_pattern.group("episode"))
        else:
            raise NoMatchPatternError("No match pattern. Will Mark \"{}\" As Un-reseed torrent.".format(torrent.name))

        search_tag = self.exist_judge(key_with_gp_ep, torrent.name)
        if search_tag == 0 and not self._ASSIST_ONLY:
            # Non-existent repetition torrent (by local judge plugins), prepare to reseed
            torrent_raw_info_dict = None

            try:
                if self._GET_CLONE_ID_FROM_DB:
                    clone_id = db.get_data_clone_id(key=key_raw, site=self.db_column)
                    if clone_id in [None, 0]:
                        raise KeyError("The db-record is not return the correct clone id.")
                    elif clone_id is not -1:  # Set to no re-seed for this site in database.
                        torrent_raw_info_dict = self.torrent_clone(clone_id)
                        if not torrent_raw_info_dict:
                            raise ValueError("The clone torrent for tid in db-record is not exist.")
                        logging.debug("Get clone torrent info from \"DataBase\" OK, Which id: {}".format(clone_id))
                else:
                    raise KeyError("Set not get clone torrent id from \"Database.\"")
            except (KeyError, ValueError) as e:
                logging.warning("{}, Try to search the clone info from site, it may not correct".format(e.args[0]))
                clone_id = self._DEFAULT_CLONE_TORRENT if self._DEFAULT_CLONE_TORRENT else 0  # USE Default clone id
                for key in [key_with_gp, key_raw]:  # USE The same group to search firstly and Then non-group tag
                    search_id = self.first_tid_in_search_list(key=key)
                    if search_id is not 0:
                        clone_id = search_id  # The search result will cover the default setting.
                        break

                if clone_id is not 0:
                    torrent_raw_info_dict = self.torrent_clone(clone_id)
                    logging.info("Get clone torrent info from \"Reseed-Site\" OK, Which id: {cid}".format(cid=clone_id))

            if torrent_raw_info_dict:
                logging.info("Begin post The torrent {0},which name: {1}".format(torrent.id, torrent.name))
                new_dict = self.date_raw_update(torrent_name_search=name_pattern, raw_info=torrent_raw_info_dict)
                multipart_data = self.data_raw2tuple(torrent, raw_info=new_dict)
                flag = self.torrent_upload(data=multipart_data)
            else:  # TODO change Error type
                raise NoCloneTorrentError("Can't find any clone torrent to used.".format(self.model_name()))
        elif search_tag == -1:  # IF the torrents are present, but not consistent (When FORCE_JUDGE_DUPE_LOC is True)
            raise CannotAssistError("Find dupe, and the exist torrent is not same as pre-reseed torrent. Stop Posting~")
        else:  # IF the torrent is already released and can be assist
            logging.warning("Find dupe torrent,which id: {0}, Automatically assist it~".format(search_tag))
            flag = self.torrent_download(tid=search_tag, thanks=False)

        return flag

    # -*- The feeding function -*-
    def torrent_feed(self, torrent):
        torrent = self._get_torrent(torrent)
        reseed_tag, = db.exec(
            "SELECT `{}` FROM `seed_list` WHERE `download_id` = {}".format(self.db_column, torrent.id)
        )

        if reseed_tag in [None, 0, "0"] and reseed_tag not in [-1, "-1"]:
            # It means that the pre-reseed torrent in this site is not reseed before,
            # And this torrent not marked as an un-reseed torrent.
            logging.info("Autoseed-{mo} Get A feed torrent: {na}".format(mo=self.model_name(), na=torrent.name))

            reseed_tag = -1
            try:
                reseed_tag = self.torrent_reseed(torrent)
            except Exception as e:  # TODO 针对不同的Error情况做不同的更新（e.g. 因为网络问题则置0，其他情况置1）
                err_name = type(e).__name__
                logging.error(
                    "Reseed not success in Site: {}, With Exception: {}, {}".format(self.model_name(), err_name, e)
                )
            db.upsert_seed_list((reseed_tag, torrent.name, self.db_column))

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
