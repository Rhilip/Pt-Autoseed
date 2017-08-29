# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

from utils.descr.mediainfo import show_mediainfo
from utils.descr.thumbnails import thumbnails
from utils.load.config import setting

raw_dict = setting.extend_descr_raw


def out(raw, torrent, clone_id, encode) -> str:
    file = setting.trans_downloaddir + "/" + torrent.files()[0]["name"]

    if encode not in ["bbcode", "html"]:
        encode = "bbcode"

    before = build_before(encode)
    shot = build_shot(file=file, encode=encode)
    media_info = build_mediainfo(file=file, encode=encode)
    clone_info = build_clone_info(before_torrent_id=clone_id, encode=encode)

    return_str = before + raw + shot + media_info + clone_info
    return return_str


def build_before(encode) -> str:
    str_before = ""
    if raw_dict["before"]["status"]:
        str_before = raw_dict["before"][encode]
    return str_before


def build_shot(file, encode) -> str:
    str_screenshot = ""
    if raw_dict["shot"]["status"]:
        file_url = thumbnails(file=file)
        if file_url:
            str_screenshot = raw_dict["shot"][encode].format(img_url=file_url)
    return str_screenshot


def build_clone_info(before_torrent_id, encode) -> str:
    str_clone_info = ""
    if raw_dict["clone_info"]["status"]:
        str_clone_info = raw_dict["clone_info"][encode].format(torrent_id=before_torrent_id)
    return str_clone_info


def build_mediainfo(file, encode) -> str:
    str_media_info = ""
    if raw_dict["mediainfo"]["status"]:
        media_info = show_mediainfo(file=file, encode=encode)
        if media_info:
            str_media_info = raw_dict["mediainfo"][encode].format(info=media_info)
    return str_media_info
