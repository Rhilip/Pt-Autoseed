# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

from utils.descr.mediainfo import build_mediainfo
from utils.descr.thumbnails import build_shot
from utils.load.config import setting

dict_setting = setting.extend_descr_raw


def out(raw, torrent, clone_id, encode) -> str:
    file = setting.trans_downloaddir + "/" + torrent.files()[0]["name"]

    if encode not in ["bbcode", "html"]:
        encode = "bbcode"

    before = build_before(encode)
    shot = build_shot(file=file, encode=encode)
    media_info = build_mediainfo(file=file, encode=encode)
    clone_info = build_clone_info(before_torrent_id=clone_id, encode=encode)

    return before + raw + shot + media_info + clone_info


def build_before(encode) -> str:
    return dict_setting["before"][encode] if dict_setting["before"]["status"] else ""


def build_clone_info(before_torrent_id, encode) -> str:
    str_clone_info = ""
    if dict_setting["clone_info"]["status"]:
        str_clone_info = dict_setting["clone_info"][encode].format(torrent_id=before_torrent_id)
    return str_clone_info

