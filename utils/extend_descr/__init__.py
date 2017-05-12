# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import logging
import base64
from .mediainfo import show_media_info


class ExtendDescr(object):
    def __init__(self, setting):
        self._setting = setting
        self.raw_dict = setting.extend_descr_raw

    def out(self, raw, torrent, before_torrent_id, encode="bbcode"):
        file = self._setting.trans_downloaddir + "/" + torrent.files()[0]["name"]
        before = self.build_before(encode)
        shot = self.build_shot(file=file, encode=encode)
        media_info = self.build_mediainfo(file=file, encode=encode)
        clone_info = self.build_clone_info(before_torrent_id=before_torrent_id, encode=encode)

        return """{before}{raw}{shot}{mediainfo}{clone_info}""" \
            .format(before=before, raw=raw, shot=shot, mediainfo=media_info, clone_info=clone_info)

    def build_before(self, encode, str_before=""):
        if self.raw_dict["before"]["status"]:
            min_time = int(self._setting.torrent_minSeedTime / 86400)
            max_time = int(self._setting.torrent_maxSeedTime / 86400)
            str_before = self.raw_dict["before"][encode].format(min_reseed_time=min_time, max_reseed_time=max_time)
        return str_before

    def build_shot(self, file, encode, str_screenshot="") -> str:
        if self.raw_dict["shot"]["status"]:
            shot_file_name = base64.b64encode(bytes(file, "utf-8"))[:32]
            screenshot_file = "screenshot/{file}.png".format(file=shot_file_name)
            file_loc = "{web_loc}/{s_file}".format(web_loc=self._setting.web_loc, s_file=screenshot_file)
            # TODO Automatically generated Screenshot time.
            ffmpeg_sh = "ffmpeg -ss 00:10:10 -y -i {file} -vframes 1 {file_loc}".format(file=file, file_loc=file_loc)
            shot = os.system(ffmpeg_sh)
            if shot == 0:
                file_url = "{web_url}/{s_f}".format(web_url=self._setting.web_url, s_f=screenshot_file)
                logging.info("The screenshot of \"{0}\" save on: \"{1}\"".format(file, file_loc))
                str_screenshot = self.raw_dict["shot"][encode].format(img_url=file_url)
            else:
                logging.warning("Can't get Screenshot for \"{0}\".".format(screenshot_file))
        return str_screenshot

    def build_clone_info(self, before_torrent_id, encode, str_clone_info="") -> str:
        if self.raw_dict["clone_info"]["status"]:
            str_clone_info = self.raw_dict["clone_info"][encode].format(torrent_id=before_torrent_id)
        return str_clone_info

    def build_mediainfo(self, file, encode, str_media_info="") -> str:
        info = show_media_info(file=file, encode=encode)
        if self.raw_dict["mediainfo"]["status"]:
            str_media_info = self.raw_dict["mediainfo"][encode].format(info=info)
        return str_media_info
