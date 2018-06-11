# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import os
import re
import time

import requests
from bs4 import BeautifulSoup

import utils.descr as descr
from utils.constants import Video_Containers
from utils.cookie import cookies_raw2jar
from utils.load.config import setting
from utils.load.handler import rootLogger as Logger
from utils.load.submodules import tc, db
from utils.pattern import pattern_group as search_ptn

REQUESTS_TIMEOUT = 5


class Site(object):
    url_host = "http://www.pt_domain.com"  # No '/' at the end.
    db_column = "tracker.pt_domain.com"  # The column in table,should be as same as the first tracker's host
    encode = "bbcode"  # bbcode or html

    suspended = 0  # 0 -> site Online, any number bigger than 0 -> Offline

    def __init__(self, status: bool, cookies: dict or str, **kwargs):
        self.name = type(self).__name__

        # -*- Assign the based information -*-
        self.status = status
        try:
            self.cookies = cookies_raw2jar(cookies) if isinstance(cookies, str) else cookies
        except ValueError:  # Empty raw_cookies will raise ValueError (,see utils.cookie )
            Logger.critical("Empty cookies, Not allowed to active Model \"{}\"".format(self.name))
            self.status = False

        # -*- Assign Enhanced Features : Site -*-
        """
        Enhance Feature for `base` Reseeder.
        Those key-values will be set as default value unless you change it in your user-settings.
        The name of those key should be start with "_" and upper.
        
        Included:
        1. _EXTEND_DESCR_*        : default True, Enable to Enhanced the description of the reseed torrent,
                                     And its priority is higher than setting.extend_descr_raw[key]["status"].
        2. _ASSIST_ONLY           : default False, Enable to only assist the exist same torrent but not to reseed. 
        """
        self._EXTEND_DESCR_BEFORE = kwargs.setdefault("extend_descr_before", True)
        self._EXTEND_DESCR_THUMBNAILS = kwargs.setdefault("extend_descr_thumbnails", True)
        self._EXTEND_DESCR_MEDIAINFO = kwargs.setdefault("extend_descr_mediainfo", True)
        self._EXTEND_DESCR_CLONEINFO = kwargs.setdefault("extend_descr_cloneinfo", True)
        self._ASSIST_ONLY = kwargs.setdefault("assist_only", False)
        self._ASSIST_DELAY_TIME = kwargs.setdefault("assist_delay_time", 0)

        # Check Site Online Status
        if self.status:
            Logger.debug("Model \"{}\" is activation now.".format(self.name))
            self.online_check()
        else:
            Logger.info("Model \"{}\" isn't active due to your settings.".format(self.name))

    def online_check(self) -> bool:
        """
        Check function to get the site status (online or not)

        :return: bool , True if online
        """
        try:
            # requests.head() is a little Quicker than requests.get(),( Because only ask head without body)
            #                    but Slower than socket.create_connection(address[, timeout[, source_address]])
            requests.head(self.url_host, timeout=REQUESTS_TIMEOUT)
        except OSError:  # requests.exceptions.RequestException
            if self.suspended == 0:
                Logger.warning("Site: {si} is Offline now.".format(si=self.url_host))
            self.suspended += 1
        else:
            if self.suspended != 0:
                Logger.info("The Site: {si} is Online now,after {count} times tries."
                            "Will check the session soon.".format(si=self.url_host, count=self.suspended))
                self.suspended = 0  # Set self.suspended as 0 first, then session_check()
                self.session_check()
        return True if self.suspended == 0 else False

    @staticmethod
    def _post_torrent_file_tuple(torrent):
        """
        Build-in function to make part of post tuple in Requests.

        :param torrent: class transmissionrpc.Torrent
        :return: part of post tuple in Requests,like ('name.torrent', <_io.BufferedReader>, 'application/x-bittorrent')
        """
        filename = os.path.basename(torrent.torrentFile).encode("ascii", errors="ignore").decode()
        return filename, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent'

    @staticmethod
    def _get_torrent(torrent):
        """
        Build-in function to get torrent class by it's id.

        :param torrent: int or class transmissionrpc.Torrent
        :return: class transmissionrpc.Torrent
        """
        if isinstance(torrent, int):
            torrent = tc.get_torrent(torrent)
        return torrent

    def _assist_delay(self):
        if self._ASSIST_ONLY:
            Logger.info("Autoseed-{mo} only allowed to assist."
                        "it will sleep {sl} Seconds to wait the reseed site "
                        "to have this torrent".format(mo=self.name, sl=self._ASSIST_DELAY_TIME))
            time.sleep(self._ASSIST_DELAY_TIME)

    def _get_torrent_ptn(self, torrent):
        torrent = self._get_torrent(torrent)
        tname = torrent.name

        search = None
        for ptn in search_ptn:
            search = re.search(ptn, tname)
            if search:
                Logger.debug("The search group dict of Torrent: {tn} is {gr}".format(tn=tname, gr=search.groupdict()))
                break

        return search

    def get_data(self, url, params=None, bs=False, json=False, **kwargs):
        """Encapsulation requests's method - GET, with format-out as bs or json"""
        page = requests.get(url=url, params=params, cookies=self.cookies, **kwargs)
        return page.json() if json else (BeautifulSoup(page.text, "lxml") if bs else page.text)

    def post_data(self, url, params=None, **kwargs):
        """Encapsulation requests's method - POST"""
        return requests.post(url=url, params=params, cookies=self.cookies, **kwargs)

    def enhance_descr(self, torrent, descr_text, clone_id):
        video_file = None
        for test_file in [v["name"] for k, v in torrent.files().items()]:  # To get video file
            if (os.path.splitext(test_file)[1]).lower() in Video_Containers:
                if test_file.lower().find("sample") is -1:  # Pass sample video file
                    video_file = setting.trans_downloaddir + "/" + test_file
                    break

        before = descr.build_before(self.encode) if self._EXTEND_DESCR_BEFORE else ""
        shot = mediainfo = ""
        if video_file:
            shot = descr.build_shot(file=video_file, encode=self.encode) if self._EXTEND_DESCR_THUMBNAILS else ""
            mediainfo = descr.build_mediainfo(file=video_file,
                                              encode=self.encode) if self._EXTEND_DESCR_MEDIAINFO else ""
        clone_info = descr.build_clone_info(clone_id=clone_id,
                                            encode=self.encode) if self._EXTEND_DESCR_CLONEINFO else ""

        return before + descr_text + shot + mediainfo + clone_info

    # -*- The feeding function -*-
    def torrent_feed(self, torrent):
        torrent = self._get_torrent(torrent)
        reseed_tag, = db.exec(
            "SELECT `{}` FROM `seed_list` WHERE `download_id` = {}".format(self.db_column, torrent.id)
        )

        if reseed_tag in [None, 0, "0"] and reseed_tag not in [-1, "-1"]:
            # It means that the pre-reseed torrent in this site is not reseed before,
            # And this torrent not marked as an un-reseed torrent.
            self._assist_delay()
            Logger.info("Autoseed-{mo} Get A feed torrent: {na}".format(mo=self.name, na=torrent.name))

            reseed_tag = -1
            try:
                reseed_tag = self.torrent_reseed(torrent)
            except Exception as e:  # TODO 针对不同的Error情况做不同的更新（e.g. 因为网络问题则置0，其他情况置1）
                err_name = type(e).__name__
                Logger.error(
                    "Reseed not success in Site: {} for torrent: {}, "
                    "With Exception: {}, {}".format(self.name, torrent.name, err_name, e)
                )
            finally:
                db.upsert_seed_list((reseed_tag, torrent.name, self.db_column))

    # -*- At least Overridden function,Please overridden below when add a new site -*-
    def session_check(self):
        """
        Check function to get the reseeder's auth.

        Warning(s):
        1. You should write your code for session check, And self.status must be changed by check result in your code.

        """
        raise NotImplementedError

    def torrent_reseed(self, torrent):
        """
        Main reseed function of Reseeder.....

        :param torrent: class transmissionrpc.Torrent
        :return: int, the reseed flag - the reseed torrent id in transmission or -1, 0 (if not successfully reseed)
        """
        raise NotImplementedError
