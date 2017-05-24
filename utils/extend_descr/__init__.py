# ！/usr/bin/python3
# -*- coding: utf-8 -*-

from .mediainfo import MediaInfo
from .thumbnails import thumbnails


class ExtendDescr(object):
    def __init__(self, setting):
        self._setting = setting
        self.raw_dict = setting.extend_descr_raw

    def out(self, raw, torrent, clone_id, encode="bbcode"):
        file = self._setting.trans_downloaddir + "/" + torrent.files()[0]["name"]
        before = self.build_before(encode)
        shot = self.build_shot(file=file, encode=encode)
        media_info = self.build_mediainfo(file=file, encode=encode)
        clone_info = self.build_clone_info(before_torrent_id=clone_id, encode=encode)

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
            file_url = thumbnails(file=file)
            if file_url:
                str_screenshot = self.raw_dict["shot"][encode].format(img_url=file_url)
        return str_screenshot

    def build_clone_info(self, before_torrent_id, encode, str_clone_info="") -> str:
        if self.raw_dict["clone_info"]["status"]:
            str_clone_info = self.raw_dict["clone_info"][encode].format(torrent_id=before_torrent_id)
        return str_clone_info

    def build_mediainfo(self, file, encode, str_media_info="") -> str:
        if self.raw_dict["mediainfo"]["status"]:
            media_info = MediaInfo(file=file, encode=encode).show()
            if media_info:
                str_media_info = self.raw_dict["mediainfo"][encode].format(info=media_info)
        return str_media_info
