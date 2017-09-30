# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import logging
import os

import requests
from bs4 import BeautifulSoup

import utils.descr as descr
from utils.constants import Video_Containers
from utils.cookie import cookies_raw2jar
from utils.load.config import setting

# Disable log messages from the Requests library
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

REQUESTS_TIMEOUT = 5


class Site(object):
    url_host = "http://www.pt_domain.com"  # No '/' at the end.
    db_column = "tracker.pt_domain.com"  # The column in table,should be as same as the first tracker's host
    encode = "bbcode"  # bbcode or html

    suspended = 0  # 0 -> site Online, any number bigger than 0 -> Offline

    def __init__(self, status: bool, cookies: dict or str, **kwargs):
        # -*- Assign the based information -*-
        self.status = status
        try:
            self.cookies = cookies_raw2jar(cookies) if isinstance(cookies, str) else cookies
        except ValueError:  # Empty raw_cookies will raise ValueError (,see utils.cookie )
            logging.critical("Empty cookies, Not allowed to active Model \"{}\"".format(self.model_name()))
            self.status = False
        else:
            if self.status:
                logging.debug("Model \"{}\" is activation now.".format(self.model_name()))
            else:
                logging.info("Model \"{}\" isn't active due to your settings.".format(self.model_name()))

        # -*- Assign Enhanced Features : Site -*-
        """
        Enhance Feature for `base` Reseeder.
        Those key-values will be set as default value unless you change it in your user-settings.
        The name of those key should be start with "_" and upper.
        
        Included:
        1. _EXTEND_DESCR_* : default True, Enable to Enhanced the description of the reseed torrent, And its priority is
           higher than setting.extend_descr_raw[key]["status"].
        """
        self._EXTEND_DESCR_BEFORE = kwargs.setdefault("extend_descr_before", True)
        self._EXTEND_DESCR_THUMBNAILS = kwargs.setdefault("extend_descr_thumbnails", True)
        self._EXTEND_DESCR_MEDIAINFO = kwargs.setdefault("extend_descr_mediainfo", True)
        self._EXTEND_DESCR_CLONEINFO = kwargs.setdefault("extend_descr_cloneinfo", True)

        # Check if Site is online~
        if self.status:
            self.online_check()

    def model_name(self):
        return type(self).__name__

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
            online = False
            if self.suspended == 0:
                logging.warning("Site: {si} is Offline now.".format(si=self.url_host))
            self.suspended += 1
        else:
            online = True
            if self.suspended != 0:
                logging.info("The Site: {si} is Online now,after {count} times tries."
                             "Will check the session soon.".format(si=self.url_host, count=self.suspended))
                self.suspended = 0
                self.session_check()
        return online

    @staticmethod
    def _post_torrent_file_tuple(torrent):
        """
        Build-in function to make part of post tuple in Requests.

        :param torrent: class transmissionrpc.Torrent
        :return: part of post tuple in Requests,like ('name.torrent', <_io.BufferedReader>, 'application/x-bittorrent')
        """
        return os.path.basename(torrent.torrentFile), open(torrent.torrentFile, 'rb'), 'application/x-bittorrent'

    def get_data(self, url, params=None, bs=False, json=False, **kwargs):
        """Encapsulation requests's method - GET, with format-out as bs or json"""
        page = requests.get(url=url, params=params, cookies=self.cookies, **kwargs)
        return_info = page.text
        if bs:
            return_info = BeautifulSoup(return_info, "lxml")
        elif json:
            return_info = page.json()
        return return_info

    def post_data(self, url, params=None, **kwargs):
        """Encapsulation requests's method - POST"""
        return requests.post(url=url, params=params, cookies=self.cookies, **kwargs)

    def enhance_descr(self, torrent, info_dict):
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
        clone_info = descr.build_clone_info(clone_id=info_dict["clone_id"],
                                            encode=self.encode) if self._EXTEND_DESCR_CLONEINFO else ""

        return before + info_dict["descr"] + shot + mediainfo + clone_info

    # -*- At least Overridden function,Please overridden below when add a new site -*-
    def session_check(self) -> bool:
        """
        Check function to get the reseeder's auth.

        Warning(s):
        1. You should write your code for session check, And self.status must be changed by check result in your code.

        :return: bool, self.status
        """
        # Session check code Here.
        return self.status

    def torrent_feed(self, torrent, name_pattern, clone_db_dict):
        # TODO merge name_pattern and clone_db_dict into one dict
        """
        Main entry of Reseeder.....

        :param torrent: class transmissionrpc.Torrent
        :param name_pattern: _sre.SRE_Match
        :param clone_db_dict: dict, Information dict about clone with `search_name` and clone_id in different sites.
                May like {
                             "search_name": "<name>",
                             "<site1>": <clone_id1>,
                             "<site2>": <clone_id2>,
                             ......
                          }
        :return: int, The flag of reseed status. any number which is bigger than 0 means success.
        """
        pass
